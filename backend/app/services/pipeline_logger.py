"""
app/services/pipeline_logger.py — Logging dedicado al pipeline de KPIs.

Estructura de archivos generados (todos bajo LOG_DIR/pipeline/):

    pipeline.log              Histórico rolling (10 MB × 7) de todas las
                              ejecuciones — útil para `tail -f`.
    pipeline_errors.log       Solo ERROR/CRITICAL (5 MB × 7).
    runs/run_YYYYMMDD_HHMMSS_<mode>_<id>.log
                              UN archivo POR ejecución, con todos los
                              mensajes de esa corrida en orden. Ideal para
                              diagnosticar qué pasó en una ejecución
                              concreta sin perderse en el histórico.

Uso típico:

    with pipeline_run("produccion") as plog:
        plog.info("Cargando datos...")
        try:
            ...
        except Exception:
            plog.exception("Falló X")     # registra traceback automáticamente
        plog.info("Listo")
        # `plog.run_file` apunta al archivo per-run en disco.

`pipeline_run` se encarga de adjuntar/desadjuntar el handler per-run
aunque haya excepción no manejada.
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from app.config import settings

_LOGGER_NAME = "ubpd.pipeline"
_ROLLING_CONFIGURED = False  # idempotencia: configurar handlers rolling 1 sola vez

# Formato más rico (incluye nombre del módulo y nivel) para diagnóstico
_FMT = "%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"
_FORMATTER = logging.Formatter(_FMT, _DATE_FMT)


def _pipeline_log_dir() -> Path:
    base = Path(getattr(settings, "LOG_DIR", "/app/logs"))
    path = base / "pipeline"
    path.mkdir(parents=True, exist_ok=True)
    (path / "runs").mkdir(parents=True, exist_ok=True)
    return path


def _configure_rolling_handlers(logger: logging.Logger) -> None:
    """Adjunta los handlers rolling al logger una sola vez por proceso."""
    global _ROLLING_CONFIGURED
    if _ROLLING_CONFIGURED:
        return

    log_dir = _pipeline_log_dir()

    # pipeline.log — todo (INFO+)
    rolling = logging.handlers.RotatingFileHandler(
        filename=log_dir / "pipeline.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=7,
        encoding="utf-8",
    )
    rolling.setLevel(logging.INFO)
    rolling.setFormatter(_FORMATTER)
    logger.addHandler(rolling)

    # pipeline_errors.log — solo errores
    errors = logging.handlers.RotatingFileHandler(
        filename=log_dir / "pipeline_errors.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=7,
        encoding="utf-8",
    )
    errors.setLevel(logging.ERROR)
    errors.setFormatter(_FORMATTER)
    logger.addHandler(errors)

    _ROLLING_CONFIGURED = True


def get_pipeline_logger() -> logging.Logger:
    """Devuelve el logger compartido del pipeline (configura handlers una vez)."""
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    # No propagar al root para que no duplique en app.log
    logger.propagate = True  # mantiene también el flujo a app.log/console
    _configure_rolling_handlers(logger)
    return logger


@contextmanager
def pipeline_run(
    mode: str = "produccion",
    *,
    user: str | None = None,
) -> Iterator[logging.Logger]:
    """Context manager que agrega un FileHandler exclusivo para esta ejecución.

    Genera un archivo en `LOG_DIR/pipeline/runs/run_<timestamp>_<mode>_<id>.log`
    con TODOS los mensajes (INFO+) de esta corrida. Al salir del bloque, el
    handler se cierra y se desadjunta aunque haya excepciones.

    El logger devuelto expone `run_file` (Path) y `run_id` (str).
    """
    logger = get_pipeline_logger()
    log_dir = _pipeline_log_dir()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_id = uuid.uuid4().hex[:8]
    fname = f"run_{ts}_{mode}_{run_id}.log"
    run_file = log_dir / "runs" / fname

    fh = logging.FileHandler(run_file, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(_FORMATTER)
    logger.addHandler(fh)

    # Stash metadata accesible por quien tiene el logger
    setattr(logger, "run_file", run_file)
    setattr(logger, "run_id", run_id)

    logger.info(
        "═══ PIPELINE RUN start | id=%s | mode=%s | user=%s ═══",
        run_id, mode, user or "—",
    )
    try:
        yield logger
        logger.info("═══ PIPELINE RUN end ok | id=%s ═══", run_id)
    except Exception:
        logger.exception("═══ PIPELINE RUN end FAIL | id=%s ═══", run_id)
        raise
    finally:
        try:
            fh.flush()
            fh.close()
        except Exception:
            pass
        try:
            logger.removeHandler(fh)
        except Exception:
            pass


def annotate_script_error(code: str, traceback_str: str) -> str:
    """Construye un mensaje legible con el traceback + snippet del script.

    Cuando el script ejecutado falla con SyntaxError o NameError, mostrar las
    3 líneas antes y después del fallo ayuda mucho a diagnosticar.
    """
    import re

    if not code or not traceback_str:
        return traceback_str or "(sin traceback)"

    m = re.search(r'"<pipeline_script>", line (\d+)', traceback_str)
    if not m:
        return traceback_str

    lineno = int(m.group(1))
    lines = code.split("\n")
    start = max(1, lineno - 3)
    end = min(len(lines), lineno + 3)
    snippet_lines = []
    for i in range(start, end + 1):
        marker = " >> " if i == lineno else "    "
        snippet_lines.append(f"  {marker}{i:4d} | {lines[i-1]}")
    snippet = "\n".join(snippet_lines)
    return (
        f"{traceback_str}\n"
        f"--- Contexto del script (línea {lineno}) ---\n"
        f"{snippet}\n"
    )

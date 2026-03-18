"""
app/logging_config.py — Configuración centralizada de logging para UBPD.

Escribe logs en archivos rotativos fuera del contenedor (volumen ./logs/backend).
Separación por severidad:
  - app.log     → INFO y superior (todo el sistema)
  - errors.log  → ERROR y superior (solo errores)
  - access.log  → HTTP access log de Uvicorn

Para desarrollo local (sin Docker) apuntar LOG_DIR a ./logs/backend.
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path


def setup_logging(app_env: str = "production", log_dir: str = "/app/logs") -> None:
    """
    Configura el sistema de logging global.

    Args:
        app_env:  "development" activa DEBUG y logs más detallados.
        log_dir:  Directorio raíz donde se crearán los archivos de log.
                  En Docker: /app/logs (montado como ./logs/backend en el host).
                  En dev local: ./logs/backend (relativo al directorio de trabajo).
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    is_dev = app_env == "development"
    root_level = logging.DEBUG if is_dev else logging.INFO

    # ── Formato ────────────────────────────────────────────────────────────────
    fmt = "%(asctime)s | %(levelname)-8s | %(name)-35s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, date_fmt)

    # ── Root logger ────────────────────────────────────────────────────────────
    root = logging.getLogger()
    root.setLevel(root_level)
    # Limpiar handlers previos (evita duplicados en recargas)
    root.handlers.clear()

    # ── Handler: consola (stdout) ──────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(root_level)
    root.addHandler(console_handler)

    # ── Handler: app.log (INFO+, rotación 10 MB, 7 backups ≈ 70 MB máx) ───────
    app_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=7,
        encoding="utf-8",
    )
    app_handler.setFormatter(formatter)
    app_handler.setLevel(logging.INFO)
    root.addHandler(app_handler)

    # ── Handler: errors.log (ERROR+, rotación 5 MB, 7 backups) ───────────────
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / "errors.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=7,
        encoding="utf-8",
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    root.addHandler(error_handler)

    # ── Handler: access.log (accesos HTTP de Uvicorn, INFO+) ──────────────────
    access_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / "access.log",
        maxBytes=20 * 1024 * 1024,  # 20 MB — más volumen por requests
        backupCount=14,              # 14 backups (≈ 280 MB máx)
        encoding="utf-8",
    )
    access_handler.setFormatter(formatter)
    access_handler.setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").addHandler(access_handler)

    # ── Silenciar loggers muy verbosos ─────────────────────────────────────────
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if is_dev else logging.WARNING
    )
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(
        logging.DEBUG if is_dev else logging.INFO
    )

    # ── Log de inicio ──────────────────────────────────────────────────────────
    startup_logger = logging.getLogger("ubpd.logging")
    startup_logger.info(
        "Logging iniciado — env=%s | dir=%s | nivel=%s",
        app_env,
        log_path.resolve(),
        logging.getLevelName(root_level),
    )


def get_celery_log_config(log_dir: str = "/app/logs") -> dict:
    """
    Retorna la configuración de logging para Celery (formato dictConfig).
    Se pasa a celery_app.conf.update(worker_log_format=...) o se usa
    directamente en el signal after_setup_logger.
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    return {
        "worker_log_file": str(log_path / "celery_worker.log"),
        "beat_log_file": str(log_path / "celery_beat.log"),
        "worker_log_format": (
            "%(asctime)s | %(levelname)-8s | %(task_name)-40s | %(message)s"
        ),
        "worker_task_log_format": (
            "%(asctime)s | %(levelname)-8s | TASK %(task_name)s[%(task_id)s] | %(message)s"
        ),
    }

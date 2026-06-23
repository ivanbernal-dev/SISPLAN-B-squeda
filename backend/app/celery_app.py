"""
app/celery_app.py — Configuración de Celery con Valkey como broker.

Beat Schedule:
- recalcular estadísticas cada STATS_RECALC_INTERVAL_SECONDS (por defecto 10 min).
"""
from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "ubpd",
    broker=settings.VALKEY_URL,
    backend=settings.VALKEY_URL,
    include=["app.tasks.pipeline_tasks"],
)

celery_app.conf.update(
    # Serialización
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Zona horaria
    timezone="America/Bogota",
    enable_utc=True,
    # Reintentos
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Expiración de resultados: 24 horas
    result_expires=86400,
    # Beat schedule — recálculo periódico
    beat_schedule={
        "recalculate-stats-periodically": {
            "task": "app.tasks.pipeline_tasks.scheduled_recalculation",
            "schedule": settings.STATS_RECALC_INTERVAL_SECONDS,
            "options": {"expires": settings.STATS_RECALC_INTERVAL_SECONDS},
        },
    },
    # Logging — archivos dentro del volumen de logs
    worker_log_format=(
        "%(asctime)s | %(levelname)-8s | %(processName)s | %(message)s"
    ),
    worker_task_log_format=(
        "%(asctime)s | %(levelname)-8s | TASK %(task_name)s[%(task_id)s] | %(message)s"
    ),
)


# ── Configurar logging de Celery con handlers a archivo ───────────────────────
from celery.signals import after_setup_logger, after_setup_task_logger
import logging
import logging.handlers
from pathlib import Path


def _add_file_handler(logger: logging.Logger, log_file: str) -> None:
    """Añade un RotatingFileHandler al logger de Celery."""
    log_path = Path(settings.LOG_DIR)
    log_path.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    handler = logging.handlers.RotatingFileHandler(
        filename=log_path / log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=7,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)


@after_setup_logger.connect
def setup_celery_logger(logger, **kwargs):
    """Llamado tras inicializar el logger del worker."""
    _add_file_handler(logger, "celery_worker.log")


@after_setup_task_logger.connect
def setup_celery_task_logger(logger, **kwargs):
    """Llamado tras inicializar el logger de tareas."""
    _add_file_handler(logger, "celery_tasks.log")

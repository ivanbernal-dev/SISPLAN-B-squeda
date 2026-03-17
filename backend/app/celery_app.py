"""
app/celery_app.py — Configuración de Celery con Redis como broker.

Beat Schedule:
- recalcular estadísticas cada STATS_RECALC_INTERVAL_SECONDS (por defecto 10 min).
"""
from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "ubpd",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
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
)

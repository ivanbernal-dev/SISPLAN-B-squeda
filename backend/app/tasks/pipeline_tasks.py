"""
app/tasks/pipeline_tasks.py — Tareas Celery del pipeline de estadísticas.

Las tareas son síncronas (Celery no soporta async/await de forma nativa),
por lo que usan asyncio.run() para ejecutar el código async de los servicios.
"""
import asyncio
import logging
import uuid

from app.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.services.pipeline_service import (
    process_approved_form,
    recalculate_all_stats,
)

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.pipeline_tasks.process_form_approved",
    max_retries=3,
    default_retry_delay=60,
)
def process_form_approved(self, form_id: str) -> dict:
    """
    Tarea Celery disparada cuando un formulario es aprobado.
    Calcula completitud e inserta/actualiza fact_stats.
    """
    logger.info("Iniciando pipeline para formulario: %s", form_id)

    async def _run():
        async with AsyncSessionLocal() as db:
            try:
                await process_approved_form(db, uuid.UUID(form_id))
                await db.commit()
                return {"status": "success", "form_id": form_id}
            except Exception as exc:
                await db.rollback()
                raise exc

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("Error en pipeline de formulario %s: %s", form_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.pipeline_tasks.scheduled_recalculation",
)
def scheduled_recalculation() -> dict:
    """
    Tarea periódica programada por Celery Beat.
    Recalcula todos los fact_stats de formularios aprobados.
    """
    logger.info("Iniciando recálculo periódico de estadísticas.")

    async def _run():
        async with AsyncSessionLocal() as db:
            try:
                await recalculate_all_stats(db)
                await db.commit()
                return {"status": "success"}
            except Exception as exc:
                await db.rollback()
                raise exc

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("Error en recálculo periódico: %s", exc)
        raise

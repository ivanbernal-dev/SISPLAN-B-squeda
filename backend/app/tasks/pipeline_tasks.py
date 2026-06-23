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


@celery_app.task(
    name="app.tasks.pipeline_tasks.run_pipeline_on_approval",
    max_retries=2,
    default_retry_delay=30,
)
def run_pipeline_on_approval(trigger_info: str = "") -> dict:
    """
    Ejecuta el script de pipeline guardado en modo producción
    cuando se aprueba un formulario o lote. Recalcula todos los KPIs.
    """
    logger.info("Auto-ejecutando pipeline tras aprobación: %s", trigger_info)

    async def _run():
        async with AsyncSessionLocal() as db:
            try:
                from datetime import datetime, timezone
                from sqlalchemy.future import select
                from app.models.kpi import PipelineScript, KpiResultado

                # Load saved script
                res = await db.execute(
                    select(PipelineScript).order_by(PipelineScript.updated_at.desc()).limit(1)
                )
                script = res.scalar_one_or_none()
                if not script or not script.codigo:
                    logger.warning("No hay script guardado para ejecutar")
                    return {"status": "skipped", "reason": "no_script"}

                from app.routers.script_pipeline import _load_dataframes, _run_script_sync
                dfs, template_meta = await _load_dataframes(db)
                combined = {"dfs": dfs, "meta": template_meta}
                result = _run_script_sync(script.codigo, combined)

                if result["error"]:
                    logger.error("Pipeline error: %s", result["error"])
                    return {"status": "error", "error": result["error"]}

                resultado = result["resultado"]
                if not resultado or not isinstance(resultado, dict) or "nivel1" not in resultado:
                    logger.warning("Pipeline no produjo un resultado válido")
                    return {"status": "no_resultado"}

                nivel1_items = resultado.get("nivel1", [])
                nivel2_map = resultado.get("nivel2", {})

                # Upsert nivel 1
                for item in nivel1_items:
                    key = item.get("key", "")
                    existing = await db.execute(
                        select(KpiResultado).where(KpiResultado.kpi_key == key)
                    )
                    kpi = existing.scalar_one_or_none()
                    if kpi:
                        kpi.kpi_label = item.get("label", key)
                        kpi.valor = float(item.get("valor", 0.0))
                        kpi.descripcion = item.get("descripcion")
                        kpi.updated_at = datetime.now(timezone.utc)
                    else:
                        db.add(KpiResultado(
                            nivel=1, kpi_key=key,
                            kpi_label=item.get("label", key),
                            valor=float(item.get("valor", 0.0)),
                            descripcion=item.get("descripcion"),
                        ))

                # Upsert nivel 2
                for parent_key, sub_items in nivel2_map.items():
                    for item in sub_items:
                        key = item.get("key", "")
                        existing = await db.execute(
                            select(KpiResultado).where(KpiResultado.kpi_key == key)
                        )
                        kpi = existing.scalar_one_or_none()
                        tid = item.get("template_id")
                        if kpi:
                            kpi.kpi_label = item.get("label", key)
                            kpi.valor = float(item.get("valor", 0.0))
                            kpi.nivel1_key = parent_key
                            if tid:
                                kpi.template_id = str(tid)
                            kpi.updated_at = datetime.now(timezone.utc)
                        else:
                            db.add(KpiResultado(
                                nivel=2, kpi_key=key,
                                kpi_label=item.get("label", key),
                                valor=float(item.get("valor", 0.0)),
                                nivel1_key=parent_key,
                                template_id=str(tid) if tid else None,
                            ))

                await db.commit()
                logger.info(
                    "Pipeline ejecutado y KPIs actualizados: %d nivel-1, %d nivel-2",
                    len(nivel1_items),
                    sum(len(v) for v in nivel2_map.values()),
                )
                return {"status": "success"}
            except Exception as exc:
                await db.rollback()
                logger.error("Error ejecutando pipeline: %s", exc)
                raise exc

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("Error en run_pipeline_on_approval: %s", exc)
        return {"status": "error", "error": str(exc)}

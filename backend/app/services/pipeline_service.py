"""
app/services/pipeline_service.py — Lógica del pipeline de cálculo de estadísticas.

Responsabilidades:
- process_approved_form: calcula completitud y upsert en fact_stats para un formulario.
- recalculate_all_stats: recalcula todos los fact_stats de formularios aprobados.
"""
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fact_stats import FactStats
from app.models.form import Form, FormStatus
from app.models.pipeline_run import PipelineRun, PipelineStatus
from app.models.template import Template
from app.services.template_parser import calculate_completeness

logger = logging.getLogger(__name__)


async def _upsert_fact_stats(
    db: AsyncSession,
    form: Form,
    campos_llenos: int,
    campos_totales: int,
    completitud: Decimal,
) -> None:
    """
    Inserta o actualiza el registro fact_stats para el formulario dado.
    """
    result = await db.execute(
        select(FactStats).where(FactStats.formulario_id == form.id)
    )
    existing = result.scalar_one_or_none()

    fecha_aprobacion = form.fecha_validacion or datetime.now(timezone.utc)
    fecha_referencia = form.fecha_usuario or fecha_aprobacion.date()

    if existing:
        existing.campos_llenos = campos_llenos
        existing.campos_totales = campos_totales
        existing.completitud = completitud
        existing.fecha_referencia = fecha_referencia
        existing.fecha_aprobacion = fecha_aprobacion
        existing.calculado_en = datetime.now(timezone.utc)
    else:
        fs = FactStats(
            formulario_id=form.id,
            template_id=form.plantilla_id,
            indicador_id=form.plantilla.indicador_nivel1_id,
            dependency_id=form.dependency_id,
            campos_llenos=campos_llenos,
            campos_totales=campos_totales,
            completitud=completitud,
            fecha_referencia=fecha_referencia,
            fecha_aprobacion=fecha_aprobacion,
        )
        db.add(fs)


async def process_approved_form(db: AsyncSession, form_id: uuid.UUID) -> None:
    """
    Procesa un formulario aprobado:
    1. Carga el formulario y su template.
    2. Calcula completitud.
    3. Inserta/actualiza fact_stats.
    4. Registra el pipeline_run.
    """
    run = PipelineRun(
        tipo="form_approved",
        estado=PipelineStatus.running,
        formulario_id=form_id,
        detalles={},
    )
    db.add(run)
    await db.flush()

    try:
        result = await db.execute(
            select(Form).where(Form.id == form_id)
        )
        form = result.scalar_one_or_none()

        if form is None:
            raise ValueError(f"Formulario {form_id} no encontrado")
        if form.estado != FormStatus.approved:
            raise ValueError(f"El formulario {form_id} no está aprobado")
        if form.plantilla is None:
            raise ValueError(f"El formulario {form_id} no tiene plantilla")
        if form.plantilla.indicador_nivel1_id is None:
            logger.warning(
                "Template %s no tiene indicador asignado; omitiendo fact_stats.",
                form.plantilla_id,
            )
            run.estado = PipelineStatus.success
            run.terminado_en = datetime.now(timezone.utc)
            run.detalles = {"warning": "Template sin indicador_nivel1_id"}
            return

        schema = form.plantilla.configuracion_campos
        campos_llenos, campos_totales = calculate_completeness(
            form.datos_dinamicos, schema
        )

        if campos_totales > 0:
            completitud = Decimal(str(round(campos_llenos / campos_totales * 100, 2)))
        else:
            completitud = Decimal("0.00")

        await _upsert_fact_stats(db, form, campos_llenos, campos_totales, completitud)

        run.estado = PipelineStatus.success
        run.terminado_en = datetime.now(timezone.utc)
        run.detalles = {
            "campos_llenos": campos_llenos,
            "campos_totales": campos_totales,
            "completitud": float(completitud),
        }
        logger.info(
            "Pipeline procesado para formulario %s: completitud=%.2f%%",
            form_id,
            float(completitud),
        )

    except Exception as exc:
        run.estado = PipelineStatus.error
        run.terminado_en = datetime.now(timezone.utc)
        run.detalles = {"error": str(exc)}
        logger.error("Error en pipeline para formulario %s: %s", form_id, exc)
        raise


async def recalculate_all_stats(db: AsyncSession) -> None:
    """
    Recalcula fact_stats para todos los formularios aprobados.
    Usado por el job periódico de Celery.
    """
    run = PipelineRun(
        tipo="scheduled_recalc",
        estado=PipelineStatus.running,
        detalles={},
    )
    db.add(run)
    await db.flush()

    try:
        result = await db.execute(
            select(Form).where(Form.estado == FormStatus.approved)
        )
        forms = result.scalars().all()

        processed = 0
        errors = 0

        for form in forms:
            try:
                if form.plantilla is None or form.plantilla.indicador_nivel1_id is None:
                    continue
                schema = form.plantilla.configuracion_campos
                campos_llenos, campos_totales = calculate_completeness(
                    form.datos_dinamicos, schema
                )
                if campos_totales > 0:
                    completitud = Decimal(
                        str(round(campos_llenos / campos_totales * 100, 2))
                    )
                else:
                    completitud = Decimal("0.00")
                await _upsert_fact_stats(
                    db, form, campos_llenos, campos_totales, completitud
                )
                processed += 1
            except Exception as exc:
                logger.error(
                    "Error al recalcular formulario %s: %s", form.id, exc
                )
                errors += 1

        run.estado = PipelineStatus.success
        run.terminado_en = datetime.now(timezone.utc)
        run.detalles = {"processed": processed, "errors": errors}
        logger.info(
            "Recálculo periódico: %d procesados, %d errores.", processed, errors
        )

    except Exception as exc:
        run.estado = PipelineStatus.error
        run.terminado_en = datetime.now(timezone.utc)
        run.detalles = {"error": str(exc)}
        logger.error("Error en recálculo periódico: %s", exc)
        raise

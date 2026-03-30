"""
app/routers/validation.py — Endpoints de validación de formularios (validador).
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_client_ip, get_validator_user
from app.models.audit_log import AuditLog
from app.models.form import Form, FormStatus
from app.models.user import User
from app.schemas.form import FormListResponse, FormResponse, RejectRequest
from app.tasks.pipeline_tasks import process_form_approved

router = APIRouter(prefix="/validation", tags=["Validación"])


async def _log_audit(db: AsyncSession, **kwargs) -> None:
    db.add(AuditLog(**kwargs))


def _with_relations():
    return [
        selectinload(Form.archivos),
        selectinload(Form.validado_por),
        selectinload(Form.plantilla),
        selectinload(Form.dependency),
        selectinload(Form.usuario),
    ]


async def _load_form(db: AsyncSession, form_id: uuid.UUID) -> Form | None:
    result = await db.execute(
        select(Form).where(Form.id == form_id).options(*_with_relations())
    )
    return result.scalar_one_or_none()


@router.get("/pending", response_model=FormListResponse)
async def get_pending_forms(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    current_user: User = Depends(get_validator_user),
    db: AsyncSession = Depends(get_db),
) -> FormListResponse:
    """Bandeja de formularios pendientes de validación."""
    query = select(Form).where(Form.estado == FormStatus.pending)

    if start_date:
        query = query.where(Form.fecha_carga >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.where(Form.fecha_carga <= datetime.fromisoformat(end_date + "T23:59:59"))

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q) or 0

    offset = (page - 1) * size
    result = await db.execute(
        query.options(*_with_relations())
        .order_by(Form.fecha_carga.asc()).offset(offset).limit(size)
    )
    forms = result.scalars().all()
    return FormListResponse(
        total=total,
        page=page,
        size=size,
        items=[FormResponse.model_validate(f) for f in forms],
    )


@router.get("/history", response_model=FormListResponse)
async def get_validation_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_validator_user),
    db: AsyncSession = Depends(get_db),
) -> FormListResponse:
    """Historial de formularios ya procesados por este validador."""
    query = select(Form).where(
        Form.estado.in_([FormStatus.approved, FormStatus.rejected]),
        Form.validado_por_id == current_user.id,
    )

    if start_date:
        query = query.where(
            Form.fecha_validacion >= datetime.fromisoformat(start_date)
        )
    if end_date:
        query = query.where(
            Form.fecha_validacion
            <= datetime.fromisoformat(end_date + "T23:59:59")
        )

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q) or 0

    offset = (page - 1) * size
    result = await db.execute(
        query.options(*_with_relations())
        .order_by(Form.fecha_validacion.desc()).offset(offset).limit(size)
    )
    forms = result.scalars().all()
    return FormListResponse(
        total=total,
        page=page,
        size=size,
        items=[FormResponse.model_validate(f) for f in forms],
    )


@router.patch("/{form_id}/approve", response_model=FormResponse)
async def approve_form(
    request: Request,
    form_id: uuid.UUID,
    current_user: User = Depends(get_validator_user),
    db: AsyncSession = Depends(get_db),
) -> FormResponse:
    """
    Aprueba un formulario pendiente.
    Cambia el estado a 'approved' y dispara la tarea Celery de cálculo de estadísticas.
    """
    form = await _load_form(db, form_id)
    if form is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulario no encontrado")
    if form.estado != FormStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Solo se puede aprobar un formulario en estado 'pending' (actual: {form.estado.value})",
        )

    form.estado = FormStatus.approved
    form.validado_por_id = current_user.id
    form.fecha_validacion = datetime.now(timezone.utc)

    await _log_audit(
        db,
        usuario_id=current_user.id,
        accion="FORM_APPROVE",
        entidad_tipo="formulario",
        entidad_id=form.id,
        ip_address=get_client_ip(request),
    )

    form_id_str = str(form_id)
    await db.commit()
    process_form_approved.delay(form_id_str)

    form = await _load_form(db, form_id)
    return FormResponse.model_validate(form)


@router.patch("/{form_id}/reject", response_model=FormResponse)
async def reject_form(
    request: Request,
    form_id: uuid.UUID,
    body: RejectRequest,
    current_user: User = Depends(get_validator_user),
    db: AsyncSession = Depends(get_db),
) -> FormResponse:
    """
    Rechaza un formulario pendiente. Requiere comentario obligatorio.
    """
    form = await _load_form(db, form_id)
    if form is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulario no encontrado")
    if form.estado != FormStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Solo se puede rechazar un formulario en estado 'pending' (actual: {form.estado.value})",
        )

    form.estado = FormStatus.rejected
    form.comentario_rechazo = body.comentario
    form.validado_por_id = current_user.id
    form.fecha_validacion = datetime.now(timezone.utc)

    await _log_audit(
        db,
        usuario_id=current_user.id,
        accion="FORM_REJECT",
        entidad_tipo="formulario",
        entidad_id=form.id,
        detalle={"comentario": body.comentario[:200]},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    form = await _load_form(db, form_id)
    return FormResponse.model_validate(form)

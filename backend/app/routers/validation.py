"""
app/routers/validation.py — Endpoints de validación de formularios (validador).
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_client_ip, get_validator_user
from app.models.audit_log import AuditLog
from app.models.form import Form, FormStatus
from app.models.template import Template
from app.models.user import User
from app.schemas.form import FormListResponse, FormResponse, RejectRequest
from app.tasks.pipeline_tasks import process_form_approved, run_pipeline_on_approval


class ApproveRequest(BaseModel):
    """
    Body opcional para el endpoint /approve. Permite que el validador
    establezca los valores de los campos marcados como `validator_only: true`
    en la configuración del template (típicamente las observaciones OAP).
    """
    validator_fields: Optional[Dict[str, Any]] = None
    comentario: Optional[str] = None


def _validator_only_names(tpl: Template | None) -> set[str]:
    if tpl is None:
        return set()
    cfg = tpl.configuracion_campos or {}
    fields = cfg.get("fields") or cfg.get("campos") or []
    return {f.get("name") for f in fields if f.get("validator_only") and f.get("name")}

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
    """Bandeja de formularios pendientes de validación (excluye los de carga Excel)."""
    query = select(Form).where(
        Form.estado == FormStatus.pending,
        Form.lote_excel_id.is_(None),  # Los de Excel se validan por lote
    )

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
    body: ApproveRequest | None = None,
    current_user: User = Depends(get_validator_user),
    db: AsyncSession = Depends(get_db),
) -> FormResponse:
    """
    Aprueba un formulario pendiente.

    El body es opcional. Si incluye `validator_fields` con los nombres de los
    campos marcados como `validator_only` en el template, esos valores se
    almacenan en `datos_dinamicos` antes de aprobar.

    Cambia el estado a 'approved' y dispara la tarea Celery de cálculo.
    """
    form = await _load_form(db, form_id)
    if form is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulario no encontrado")
    if form.estado != FormStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Solo se puede aprobar un formulario en estado 'pending' (actual: {form.estado.value})",
        )
    # Si el formulario fue cargado por Excel, debe validarse como lote completo
    if form.lote_excel_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Este formulario fue cargado por Excel y debe validarse como lote completo. "
                   f"Usa la sección 'Carga Excel' del validador (lote: {form.lote_excel_id[:8]}...).",
        )

    # Inyectar valores de campos validator_only (si se enviaron y existen en el template)
    if body and body.validator_fields:
        allowed = _validator_only_names(form.plantilla)
        nuevos = dict(form.datos_dinamicos or {})
        for nombre, valor in body.validator_fields.items():
            if nombre in allowed:
                nuevos[nombre] = valor
        form.datos_dinamicos = nuevos
        # SQLAlchemy detecta el cambio porque reemplazamos el dict completo

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
    run_pipeline_on_approval.delay(f"form:{form_id_str}")

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
    # Si el formulario fue cargado por Excel, debe rechazarse como lote completo
    if form.lote_excel_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Este formulario fue cargado por Excel y debe rechazarse como lote completo. "
                   f"Usa la sección 'Carga Excel' del validador (lote: {form.lote_excel_id[:8]}...).",
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


# ── LOTES EXCEL ───────────────────────────────────────────────────────────────

class LoteResumen(BaseModel):
    lote_id: str
    template_nombre: str
    dependencia_nombre: str
    usuario_nombre: str
    fecha_carga: datetime
    total_registros: int


class LoteDetalle(BaseModel):
    lote_id: str
    template_nombre: str
    dependencia_nombre: str
    usuario_nombre: str
    fecha_carga: datetime
    total_registros: int
    campos: List[str]
    registros: List[Dict[str, Any]]
    plantilla_id: Optional[str] = None
    template_fields: Optional[List[Dict[str, Any]]] = None


@router.get("/lotes", response_model=List[LoteResumen])
async def list_pending_batches(
    current_user: User = Depends(get_validator_user),
    db: AsyncSession = Depends(get_db),
) -> List[LoteResumen]:
    """Lista de lotes Excel pendientes de validación (agrupados por lote_excel_id)."""
    # Obtener todos los formularios pending cargados via Excel con lote_excel_id
    result = await db.execute(
        select(Form)
        .where(
            Form.estado == FormStatus.pending,
            Form.cargado_via_excel == True,
            Form.lote_excel_id.isnot(None),
        )
        .options(*_with_relations())
        .order_by(Form.fecha_carga.asc())
    )
    forms = result.scalars().all()

    # Agrupar por lote_excel_id
    lotes: dict = {}
    for f in forms:
        lid = f.lote_excel_id
        if lid not in lotes:
            lotes[lid] = {
                "lote_id": lid,
                "template_nombre": f.plantilla.nombre if f.plantilla else "",
                "dependencia_nombre": f.dependency.nombre if f.dependency else "",
                "usuario_nombre": f.usuario.nombre_completo if f.usuario else "",
                "fecha_carga": f.fecha_carga,
                "total_registros": 0,
            }
        lotes[lid]["total_registros"] += 1

    return [LoteResumen(**v) for v in lotes.values()]


@router.get("/lotes/{lote_id}", response_model=LoteDetalle)
async def get_batch_detail(
    lote_id: str,
    current_user: User = Depends(get_validator_user),
    db: AsyncSession = Depends(get_db),
) -> LoteDetalle:
    """Detalle de un lote Excel: todos los registros con sus datos."""
    result = await db.execute(
        select(Form)
        .where(Form.lote_excel_id == lote_id)
        .options(*_with_relations())
        .order_by(Form.fecha_carga.asc())
    )
    forms = result.scalars().all()

    if not forms:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")

    first = forms[0]
    # Extraer nombres de campos del template
    campos: list[str] = []
    if first.plantilla and first.plantilla.configuracion_campos:
        cfg = first.plantilla.configuracion_campos
        fields = cfg.get("fields") or cfg.get("campos") or []
        campos = [f.get("label", f.get("name", "")) for f in fields
                  if f.get("type", "text") != "computed"]
    campos_keys = []
    if first.plantilla and first.plantilla.configuracion_campos:
        cfg = first.plantilla.configuracion_campos
        fields = cfg.get("fields") or cfg.get("campos") or []
        campos_keys = [f.get("name", "") for f in fields
                       if f.get("type", "text") != "computed"]

    registros = []
    for f in forms:
        datos = dict(f.datos_dinamicos or {})
        datos["_id"] = str(f.id)
        datos["_estado"] = f.estado.value
        datos["informe_cualitativo"] = f.informe_cualitativo or ""
        datos["fecha_referencia"] = str(f.fecha_usuario) if f.fecha_usuario else ""
        registros.append(datos)

    # Lista completa de campos del template (con validator_only) para el panel OAP
    template_fields_full: list[dict] = []
    if first.plantilla and first.plantilla.configuracion_campos:
        cfg = first.plantilla.configuracion_campos
        template_fields_full = cfg.get("fields") or cfg.get("campos") or []

    return LoteDetalle(
        lote_id=lote_id,
        template_nombre=first.plantilla.nombre if first.plantilla else "",
        dependencia_nombre=first.dependency.nombre if first.dependency else "",
        usuario_nombre=first.usuario.nombre_completo if first.usuario else "",
        fecha_carga=first.fecha_carga,
        total_registros=len(forms),
        campos=campos,
        registros=registros,
        plantilla_id=str(first.plantilla.id) if first.plantilla else None,
        template_fields=template_fields_full,
    )


@router.patch("/lotes/{lote_id}/approve")
async def approve_batch(
    request: Request,
    lote_id: str,
    body: ApproveRequest | None = None,
    current_user: User = Depends(get_validator_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Aprueba todos los formularios de un lote Excel.

    `body.validator_fields` aplica los mismos valores (campos validator_only)
    a TODOS los formularios del lote.
    """
    result = await db.execute(
        select(Form).where(
            Form.lote_excel_id == lote_id,
            Form.estado == FormStatus.pending,
        ).options(selectinload(Form.plantilla))
    )
    forms = result.scalars().all()
    if not forms:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Lote no encontrado o sin formularios pendientes")

    now = datetime.now(timezone.utc)
    approved_ids = []
    for f in forms:
        if body and body.validator_fields:
            allowed = _validator_only_names(f.plantilla)
            nuevos = dict(f.datos_dinamicos or {})
            for nombre, valor in body.validator_fields.items():
                if nombre in allowed:
                    nuevos[nombre] = valor
            f.datos_dinamicos = nuevos

        f.estado = FormStatus.approved
        f.validado_por_id = current_user.id
        f.fecha_validacion = now
        await _log_audit(
            db,
            usuario_id=current_user.id,
            accion="FORM_APPROVE",
            entidad_tipo="formulario",
            entidad_id=f.id,
            detalle={"lote_excel_id": lote_id, "bulk": True},
            ip_address=get_client_ip(request),
        )
        approved_ids.append(str(f.id))

    await db.commit()

    # Disparar tarea Celery para cada formulario aprobado
    for fid in approved_ids:
        process_form_approved.delay(fid)
    run_pipeline_on_approval.delay(f"lote:{lote_id}")

    return {
        "ok": True,
        "aprobados": len(approved_ids),
        "mensaje": f"{len(approved_ids)} registro(s) aprobados correctamente.",
    }


@router.patch("/lotes/{lote_id}/reject")
async def reject_batch(
    request: Request,
    lote_id: str,
    body: RejectRequest,
    current_user: User = Depends(get_validator_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Rechaza todos los formularios de un lote Excel con un comentario."""
    result = await db.execute(
        select(Form).where(
            Form.lote_excel_id == lote_id,
            Form.estado == FormStatus.pending,
        )
    )
    forms = result.scalars().all()
    if not forms:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Lote no encontrado o sin formularios pendientes")

    now = datetime.now(timezone.utc)
    rejected_ids = []
    for f in forms:
        f.estado = FormStatus.rejected
        f.comentario_rechazo = body.comentario
        f.validado_por_id = current_user.id
        f.fecha_validacion = now
        await _log_audit(
            db,
            usuario_id=current_user.id,
            accion="FORM_REJECT",
            entidad_tipo="formulario",
            entidad_id=f.id,
            detalle={"lote_excel_id": lote_id, "bulk": True, "comentario": body.comentario[:200]},
            ip_address=get_client_ip(request),
        )
        rejected_ids.append(str(f.id))

    await db.commit()
    return {
        "ok": True,
        "rechazados": len(rejected_ids),
        "mensaje": f"{len(rejected_ids)} registro(s) rechazados correctamente.",
    }

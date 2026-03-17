"""
app/routers/forms.py — Endpoints para gestión de formularios (usuarios de dependencia).
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_any_authenticated, get_client_ip, get_dependency_user
from app.models.audit_log import AuditLog
from app.models.form import Form, FormStatus
from app.models.template import Template
from app.models.user import User, UserRole
from app.schemas.form import FormCreate, FormListResponse, FormResponse, FormUpdate

router = APIRouter(prefix="/forms", tags=["Formularios"])


async def _log_audit(db: AsyncSession, **kwargs) -> None:
    db.add(AuditLog(**kwargs))


def _assert_editable(form: Form) -> None:
    """Verifica que el formulario esté en estado editable."""
    if form.estado not in (FormStatus.draft, FormStatus.rejected):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El formulario no puede editarse en estado '{form.estado.value}'",
        )


@router.get("", response_model=FormListResponse)
async def list_my_forms(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    estado: Optional[FormStatus] = None,
    current_user: User = Depends(get_dependency_user),
    db: AsyncSession = Depends(get_db),
) -> FormListResponse:
    """Lista todos los formularios del usuario autenticado, con filtro opcional por estado."""
    query = select(Form).where(Form.usuario_id == current_user.id)
    if estado:
        query = query.where(Form.estado == estado)

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q) or 0

    offset = (page - 1) * size
    result = await db.execute(
        query.order_by(Form.fecha_carga.desc()).offset(offset).limit(size)
    )
    forms = result.scalars().all()
    return FormListResponse(
        total=total,
        page=page,
        size=size,
        items=[FormResponse.model_validate(f) for f in forms],
    )


@router.get("/inbox", response_model=FormListResponse)
async def get_inbox(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    estado: Optional[FormStatus] = None,
    current_user: User = Depends(get_dependency_user),
    db: AsyncSession = Depends(get_db),
) -> FormListResponse:
    """Bandeja de trámites: formularios del usuario filtrados por estado."""
    return await list_my_forms(page, size, estado, current_user, db)


@router.post("", response_model=FormResponse, status_code=status.HTTP_201_CREATED)
async def create_form(
    request: Request,
    body: FormCreate,
    current_user: User = Depends(get_dependency_user),
    db: AsyncSession = Depends(get_db),
) -> FormResponse:
    """Crea un nuevo formulario en estado draft."""
    # Verificar que el template existe y está activo
    template_result = await db.execute(
        select(Template).where(Template.id == body.plantilla_id, Template.activo == True)
    )
    template = template_result.scalar_one_or_none()
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template no encontrado o inactivo",
        )

    # Autocompletar campos readonly con sus defaults
    datos = dict(body.datos_dinamicos)
    for field in template.configuracion_campos.get("fields", []):
        if field.get("readonly") and field.get("default") is not None:
            datos.setdefault(field["name"], field["default"])

    form = Form(
        plantilla_id=body.plantilla_id,
        usuario_id=current_user.id,
        dependency_id=current_user.dependency_id,
        datos_dinamicos=datos,
        informe_cualitativo=body.informe_cualitativo,
        fecha_usuario=body.fecha_usuario,
        estado=FormStatus.draft,
    )
    db.add(form)
    await db.flush()

    await _log_audit(
        db,
        usuario_id=current_user.id,
        accion="FORM_CREATE",
        entidad_tipo="formulario",
        entidad_id=form.id,
        detalle={"plantilla_id": str(body.plantilla_id)},
        ip_address=get_client_ip(request),
    )
    return FormResponse.model_validate(form)


@router.get("/{form_id}", response_model=FormResponse)
async def get_form(
    form_id: uuid.UUID,
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> FormResponse:
    """Retorna el detalle de un formulario."""
    result = await db.execute(select(Form).where(Form.id == form_id))
    form = result.scalar_one_or_none()
    if form is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulario no encontrado")

    # dependency_user solo puede ver sus propios formularios
    if (
        current_user.role == UserRole.dependency_user
        and form.usuario_id != current_user.id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso a este formulario")

    return FormResponse.model_validate(form)


@router.patch("/{form_id}", response_model=FormResponse)
async def update_form(
    request: Request,
    form_id: uuid.UUID,
    body: FormUpdate,
    current_user: User = Depends(get_dependency_user),
    db: AsyncSession = Depends(get_db),
) -> FormResponse:
    """Actualiza un formulario en estado draft o rejected."""
    result = await db.execute(select(Form).where(Form.id == form_id))
    form = result.scalar_one_or_none()
    if form is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulario no encontrado")
    if form.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso a este formulario")

    _assert_editable(form)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(form, field, value)
    form.fecha_edicion = datetime.now(timezone.utc)

    await _log_audit(
        db,
        usuario_id=current_user.id,
        accion="FORM_UPDATE",
        entidad_tipo="formulario",
        entidad_id=form.id,
        detalle=list(update_data.keys()),
        ip_address=get_client_ip(request),
    )
    return FormResponse.model_validate(form)


@router.post("/{form_id}/submit", response_model=FormResponse)
async def submit_form(
    request: Request,
    form_id: uuid.UUID,
    current_user: User = Depends(get_dependency_user),
    db: AsyncSession = Depends(get_db),
) -> FormResponse:
    """Envía un formulario a validación (draft → pending)."""
    result = await db.execute(select(Form).where(Form.id == form_id))
    form = result.scalar_one_or_none()
    if form is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulario no encontrado")
    if form.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso a este formulario")
    if form.estado not in (FormStatus.draft, FormStatus.rejected):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Solo se puede enviar un formulario en estado draft o rejected (actual: {form.estado.value})",
        )

    form.estado = FormStatus.pending
    form.comentario_rechazo = None
    form.fecha_edicion = datetime.now(timezone.utc)

    await _log_audit(
        db,
        usuario_id=current_user.id,
        accion="FORM_SUBMIT",
        entidad_tipo="formulario",
        entidad_id=form.id,
        ip_address=get_client_ip(request),
    )
    return FormResponse.model_validate(form)


@router.delete("/{form_id}", status_code=status.HTTP_200_OK)
async def delete_form(
    request: Request,
    form_id: uuid.UUID,
    current_user: User = Depends(get_dependency_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Elimina un formulario en estado draft."""
    result = await db.execute(select(Form).where(Form.id == form_id))
    form = result.scalar_one_or_none()
    if form is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulario no encontrado")
    if form.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso a este formulario")
    if form.estado != FormStatus.draft:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se pueden eliminar formularios en estado draft",
        )

    await db.delete(form)

    await _log_audit(
        db,
        usuario_id=current_user.id,
        accion="FORM_DELETE",
        entidad_tipo="formulario",
        entidad_id=form_id,
        ip_address=get_client_ip(request),
    )
    return {"detail": "Formulario eliminado exitosamente"}

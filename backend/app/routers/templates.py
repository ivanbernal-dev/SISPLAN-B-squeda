"""
app/routers/templates.py — Endpoints de gestión de templates de formularios.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_admin_or_validator, get_admin_user, get_any_authenticated, get_client_ip
from app.models.audit_log import AuditLog
from app.models.template import Template
from app.models.user import User
from app.schemas.template import (
    TemplateCreate,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
    TemplateResponse,
    TemplateSchema,
    TemplateUpdate,
)
from app.services.template_parser import (
    parse_markdown_to_schema,
    render_markdown_to_html,
    validate_schema,
)

router = APIRouter(prefix="/templates", tags=["Templates"])


async def _log_audit(db: AsyncSession, **kwargs) -> None:
    db.add(AuditLog(**kwargs))


def _get_or_parse_config(body_config, markdown: str) -> dict:
    """
    Si el body trae configuracion_campos úsala; si no, parsea el markdown.
    """
    if body_config is not None:
        return body_config.model_dump()
    return parse_markdown_to_schema(markdown)


@router.post(
    "/preview",
    response_model=TemplatePreviewResponse,
    summary="Previsualizar JSONB generado desde Markdown",
)
async def preview_template(
    body: TemplatePreviewRequest,
    current_user: User = Depends(get_admin_or_validator),
) -> TemplatePreviewResponse:
    """Parsea el Markdown y retorna el JSONB de campos sin persistir nada."""
    schema_dict = parse_markdown_to_schema(body.codigo_markdown)
    html = render_markdown_to_html(body.codigo_markdown)
    return TemplatePreviewResponse(
        configuracion_campos=TemplateSchema(**schema_dict),
        markdown_html=html,
    )


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    current_user: User = Depends(get_admin_or_validator),
    db: AsyncSession = Depends(get_db),
) -> list[TemplateResponse]:
    """Lista todos los templates activos."""
    result = await db.execute(
        select(Template).where(Template.activo == True).order_by(Template.nombre)
    )
    templates = result.scalars().all()
    return [TemplateResponse.model_validate(t) for t in templates]


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    request: Request,
    body: TemplateCreate,
    current_user: User = Depends(get_admin_or_validator),
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    """Crea un nuevo template parseando el Markdown para generar la configuración de campos."""
    config = _get_or_parse_config(body.configuracion_campos, body.codigo_markdown)

    template = Template(
        nombre=body.nombre,
        descripcion=body.descripcion,
        indicador_nivel1_id=body.indicador_nivel1_id,
        codigo_markdown=body.codigo_markdown,
        configuracion_campos=config,
        created_by_id=current_user.id,
    )
    db.add(template)
    await db.flush()

    await _log_audit(
        db,
        usuario_id=current_user.id,
        accion="TEMPLATE_CREATE",
        entidad_tipo="template",
        entidad_id=template.id,
        detalle={"nombre": template.nombre},
        ip_address=get_client_ip(request),
    )
    return TemplateResponse.model_validate(template)


@router.get("/by-dependency/{dep_id}", response_model=list[TemplateResponse])
async def list_templates_by_dependency(
    dep_id: uuid.UUID,
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> list[TemplateResponse]:
    """Retorna los templates activos disponibles (todos, sin filtro por dependencia específica)."""
    result = await db.execute(
        select(Template).where(Template.activo == True).order_by(Template.nombre)
    )
    templates = result.scalars().all()
    return [TemplateResponse.model_validate(t) for t in templates]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    """Retorna el detalle de un template."""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template no encontrado")
    return TemplateResponse.model_validate(template)


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    request: Request,
    template_id: uuid.UUID,
    body: TemplateUpdate,
    current_user: User = Depends(get_admin_or_validator),
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    """Actualiza un template. Si cambia el markdown, reparsea la configuración."""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template no encontrado")

    update_data = body.model_dump(exclude_unset=True)

    # Si cambió el markdown y no se proveyó configuracion_campos, reparsear
    if "codigo_markdown" in update_data and "configuracion_campos" not in update_data:
        update_data["configuracion_campos"] = parse_markdown_to_schema(
            update_data["codigo_markdown"]
        )

    if "configuracion_campos" in update_data and isinstance(update_data["configuracion_campos"], TemplateSchema):
        update_data["configuracion_campos"] = update_data["configuracion_campos"].model_dump()

    for field, value in update_data.items():
        setattr(template, field, value)

    template.version += 1

    await _log_audit(
        db,
        usuario_id=current_user.id,
        accion="TEMPLATE_UPDATE",
        entidad_tipo="template",
        entidad_id=template.id,
        detalle=list(update_data.keys()),
        ip_address=get_client_ip(request),
    )
    return TemplateResponse.model_validate(template)


@router.delete("/{template_id}", status_code=status.HTTP_200_OK)
async def deactivate_template(
    request: Request,
    template_id: uuid.UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Desactiva un template (soft delete)."""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template no encontrado")

    template.activo = False

    await _log_audit(
        db,
        usuario_id=current_user.id,
        accion="TEMPLATE_DEACTIVATE",
        entidad_tipo="template",
        entidad_id=template.id,
        ip_address=get_client_ip(request),
    )
    return {"detail": "Template desactivado exitosamente"}

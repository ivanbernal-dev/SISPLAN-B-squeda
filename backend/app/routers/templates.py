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


def _enrich(t: Template) -> TemplateResponse:
    """Convierte un ORM Template en TemplateResponse con campos derivados."""
    resp = TemplateResponse.model_validate(t)
    # Nombre del indicador: nivel2 tiene prioridad sobre nivel1
    if t.indicador_nivel2 is not None:
        resp.indicador_nombre = t.indicador_nivel2.nombre
    elif t.indicador is not None:
        resp.indicador_nombre = t.indicador.nombre
    return resp


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    all: bool = False,
    current_user: User = Depends(get_admin_or_validator),
    db: AsyncSession = Depends(get_db),
) -> list[TemplateResponse]:
    """Lista templates. Con ?all=true devuelve también los inactivos (solo admin)."""
    query = select(Template).order_by(Template.nombre)
    if not all:
        query = query.where(Template.activo == True)
    result = await db.execute(query)
    templates = result.scalars().all()
    return [_enrich(t) for t in templates]


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
    return [_enrich(t) for t in templates]


@router.get("/export")
async def export_templates(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Exporta todos los templates (activos e inactivos) como JSON para respaldo."""
    result = await db.execute(select(Template).order_by(Template.nombre))
    templates = result.scalars().all()
    return [
        {
            "codigo":               t.codigo,
            "nombre":               t.nombre,
            "descripcion":          t.descripcion,
            "codigo_markdown":      t.codigo_markdown,
            "configuracion_campos": t.configuracion_campos,
            "activo":               t.activo,
        }
        for t in templates
    ]


@router.post("/import")
async def import_templates(
    request: Request,
    payload: list[dict],
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Importa/restaura templates desde un JSON exportado previamente.
    - Si el código ya existe → actualiza campos y configuración.
    - Si no existe → crea uno nuevo.
    """
    created = 0
    updated = 0
    errors: list[str] = []

    for item in payload:
        codigo = item.get("codigo") or ""
        nombre = item.get("nombre") or codigo
        if not nombre:
            errors.append("Item sin nombre ni código omitido")
            continue
        try:
            if codigo:
                existing = (await db.execute(
                    select(Template).where(Template.codigo == codigo)
                )).scalar_one_or_none()
            else:
                existing = None

            if existing:
                existing.nombre               = item.get("nombre", existing.nombre)
                existing.descripcion          = item.get("descripcion", existing.descripcion)
                existing.codigo_markdown      = item.get("codigo_markdown", existing.codigo_markdown) or ""
                existing.configuracion_campos = item.get("configuracion_campos", existing.configuracion_campos) or {}
                existing.activo               = item.get("activo", existing.activo)
                existing.version              += 1
                updated += 1
            else:
                db.add(Template(
                    codigo               = codigo or None,
                    nombre               = nombre,
                    descripcion          = item.get("descripcion"),
                    codigo_markdown      = item.get("codigo_markdown") or "",
                    configuracion_campos = item.get("configuracion_campos") or {},
                    activo               = item.get("activo", True),
                    created_by_id        = current_user.id,
                ))
                created += 1
        except Exception as exc:
            errors.append(f"{codigo or nombre}: {exc}")

    await db.commit()
    return {
        "creados":    created,
        "actualizados": updated,
        "errores":    errors,
        "mensaje":    f"{created} template(s) creados, {updated} actualizado(s)." +
                      (f" {len(errors)} error(es)." if errors else ""),
    }


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
    return _enrich(template)


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


@router.get("/{template_id}/forms")
async def list_forms_by_template(
    template_id: uuid.UUID,
    page: int = 1,
    size: int = 20,
    estado: str | None = None,
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Lista los formularios de un template.
    - Admin / Validator: todos los formularios.
    - Dependency user: solo los propios.
    """
    from sqlalchemy import func
    from app.models.form import Form, FormStatus
    from app.models.user import UserRole
    from app.schemas.form import FormResponse

    from sqlalchemy.orm import selectinload

    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template no encontrado")

    query = select(Form).where(Form.plantilla_id == template_id)

    if current_user.role == UserRole.dependency_user:
        # Usuarios de dependencia solo ven sus propios formularios
        query = query.where(Form.usuario_id == current_user.id)
    else:
        # Admin / Validator: no muestran borradores (salvo filtro explícito)
        if not estado:
            query = query.where(Form.estado != FormStatus.draft)

    if estado:
        try:
            query = query.where(Form.estado == FormStatus(estado))
        except ValueError:
            pass

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q) or 0

    eager = [
        selectinload(Form.archivos),
        selectinload(Form.validado_por),
        selectinload(Form.plantilla),
        selectinload(Form.dependency),
        selectinload(Form.usuario),
    ]

    offset = (page - 1) * size
    rows = (await db.execute(
        query.options(*eager).order_by(Form.fecha_carga.desc()).offset(offset).limit(size)
    )).scalars().all()

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [FormResponse.model_validate(f) for f in rows],
    }

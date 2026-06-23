"""
app/routers/admin.py — Endpoints de administración: usuarios, dependencias, pipelines y auditoría.
"""
import logging
import secrets
import string
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

import json as _json
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_admin_user, get_client_ip
from app.models.audit_log import AuditLog
from app.models.dependency import Dependency
from app.models.form import Form, FormStatus
from app.models.pipeline_run import PipelineRun
from app.models.user import User, UserRole
from app.schemas.dependency import DependencyCreate, DependencyResponse, DependencyUpdate
from app.schemas.stats import SystemOverviewResponse
from app.schemas.user import UserCreate, UserCreateResponse, UserListResponse, UserResponse, UserUpdate
from app.services.auth_service import hash_password

router = APIRouter(prefix="/admin", tags=["Administración"])

TEMP_PASSWORD_ALPHABET = string.ascii_letters + string.digits + "@#$"


def _generate_temp_password(length: int = 12) -> str:
    return "".join(secrets.choice(TEMP_PASSWORD_ALPHABET) for _ in range(length))


async def _log_audit(
    db: AsyncSession,
    accion: str,
    usuario_id,
    entidad_tipo: str | None = None,
    entidad_id=None,
    detalle: dict | None = None,
    ip: str | None = None,
) -> None:
    log = AuditLog(
        usuario_id=usuario_id,
        accion=accion,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        detalle=detalle or {},
        ip_address=ip,
    )
    db.add(log)


# ── Usuarios ──────────────────────────────────────────────────────────────────

@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    """Lista todos los usuarios del sistema con paginación."""
    offset = (page - 1) * size
    count_result = await db.execute(select(func.count(User.id)))
    total = count_result.scalar_one()

    result = await db.execute(select(User).offset(offset).limit(size))
    users = result.scalars().all()

    return UserListResponse(
        total=total,
        page=page,
        size=size,
        items=[UserResponse.model_validate(u) for u in users],
    )


@router.post("/users", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    body: UserCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserCreateResponse:
    """Crea un nuevo usuario con contraseña temporal."""
    # Verificar username único
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El username '{body.username}' ya está en uso",
        )

    temp_password = _generate_temp_password()
    user = User(
        username=body.username,
        nombre_completo=body.nombre_completo,
        email=body.email,
        role=body.role,
        dependency_id=body.dependency_id,
        password_hash=hash_password(temp_password),
        requires_password_change=True,
    )
    db.add(user)
    await db.flush()

    await _log_audit(
        db,
        accion="USER_CREATE",
        usuario_id=current_user.id,
        entidad_tipo="usuario",
        entidad_id=user.id,
        detalle={"username": user.username, "role": user.role.value},
        ip=get_client_ip(request),
    )
    return UserCreateResponse(
        id=user.id,
        username=user.username,
        requires_password_change=True,
        temp_password=temp_password,
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Retorna el detalle de un usuario."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return UserResponse.model_validate(user)


@router.post("/users/{user_id}/reset-password", response_model=UserCreateResponse)
async def reset_user_password(
    request: Request,
    user_id: uuid.UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserCreateResponse:
    """Genera una nueva contraseña temporal para el usuario indicado."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    temp_password = _generate_temp_password()
    user.password_hash = hash_password(temp_password)
    user.requires_password_change = True
    user.updated_at = datetime.now(timezone.utc)

    await _log_audit(
        db,
        accion="USER_RESET_PASSWORD",
        usuario_id=current_user.id,
        entidad_tipo="usuario",
        entidad_id=user.id,
        ip=get_client_ip(request),
    )
    return UserCreateResponse(
        id=user.id,
        username=user.username,
        requires_password_change=True,
        temp_password=temp_password,
    )


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: uuid.UUID,
    body: UserUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Actualiza campos de un usuario."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    user.updated_at = datetime.now(timezone.utc)

    await _log_audit(
        db,
        accion="USER_UPDATE",
        usuario_id=current_user.id,
        entidad_tipo="usuario",
        entidad_id=user.id,
        detalle=update_data,
        ip=get_client_ip(request),
    )
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def deactivate_user(
    request: Request,
    user_id: uuid.UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Desactiva un usuario (soft delete)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propio usuario",
        )
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    user.activo = False
    user.updated_at = datetime.now(timezone.utc)

    await _log_audit(
        db,
        accion="USER_DEACTIVATE",
        usuario_id=current_user.id,
        entidad_tipo="usuario",
        entidad_id=user.id,
        ip=get_client_ip(request),
    )
    return {"detail": "Usuario desactivado exitosamente"}


@router.delete("/users/{user_id}/hard", status_code=status.HTTP_200_OK)
async def delete_user_hard(
    request: Request,
    user_id: uuid.UUID,
    force: bool = False,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Elimina PERMANENTEMENTE un usuario de la base de datos.

    Protecciones:
      - No puedes eliminar tu propio usuario.
      - No puedes eliminar al último administrador activo del sistema.
      - Si el usuario tiene formularios respondidos asociados:
          - Sin ?force=true → responde 409 con el conteo
          - Con ?force=true → borra formularios, archivos (MinIO) y el usuario
      - Los logs de auditoría del usuario se preservan (FK se pone en NULL).
    """
    from sqlalchemy import delete as sa_delete, func
    from app.models.form import Form
    from app.models.file import Archivo
    from app.services.minio_service import get_minio_service

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propio usuario.",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    # No permitir eliminar al último admin activo
    if user.role == UserRole.admin:
        n_admins = await db.scalar(
            select(func.count(User.id)).where(
                User.role == UserRole.admin,
                User.activo == True,
                User.id != user_id,
            )
        ) or 0
        if n_admins == 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "No puedes eliminar al último administrador activo del sistema. "
                    "Crea otro administrador antes."
                ),
            )

    # Contar formularios del usuario
    n_forms = await db.scalar(
        select(func.count(Form.id)).where(Form.usuario_id == user_id)
    ) or 0

    if n_forms > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El usuario tiene {n_forms} formulario(s) respondido(s) asociado(s). "
                f"Para eliminarlo junto con sus formularios y archivos, repite la solicitud con ?force=true."
            ),
        )

    # Si force=true, borrar los formularios y archivos MinIO
    n_archivos_borrados = 0
    if n_forms > 0 and force:
        forms_res = await db.execute(
            select(Form).where(Form.usuario_id == user_id)
        )
        forms_to_delete = list(forms_res.scalars().all())
        minio = get_minio_service()
        for f in forms_to_delete:
            for arch in (f.archivos or []):
                try:
                    minio.delete_file(arch)
                    n_archivos_borrados += 1
                except Exception as exc:
                    logger.warning("No se pudo eliminar archivo %s en MinIO: %s", arch.id, exc)
        form_ids = [f.id for f in forms_to_delete]
        if form_ids:
            await db.execute(sa_delete(Form).where(Form.id.in_(form_ids)))

    username = user.username
    user_email = user.email

    await _log_audit(
        db,
        accion="USER_DELETE_HARD",
        usuario_id=current_user.id,
        entidad_tipo="usuario",
        entidad_id=user.id,
        detalle={
            "username": username,
            "email": user_email,
            "forms_eliminados": n_forms,
            "archivos_eliminados": n_archivos_borrados,
        },
        ip=get_client_ip(request),
    )

    await db.execute(sa_delete(User).where(User.id == user_id))
    await db.commit()

    return {
        "ok": True,
        "mensaje": (
            f"Usuario '{username}' eliminado permanentemente. "
            + (f"Se borraron {n_forms} formulario(s) y {n_archivos_borrados} archivo(s) asociados." if force and n_forms > 0 else "")
        ),
        "usuario_eliminado": username,
        "forms_eliminados": n_forms if force else 0,
        "archivos_eliminados": n_archivos_borrados,
    }


# ── Dependencias ──────────────────────────────────────────────────────────────

@router.get("/dependencies", response_model=list[DependencyResponse])
async def list_dependencies(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[DependencyResponse]:
    """Lista todas las dependencias."""
    result = await db.execute(select(Dependency).order_by(Dependency.nombre))
    deps = result.scalars().all()
    return [DependencyResponse.model_validate(d) for d in deps]


@router.post("/dependencies", response_model=DependencyResponse, status_code=status.HTTP_201_CREATED)
async def create_dependency(
    request: Request,
    body: DependencyCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> DependencyResponse:
    """Crea una nueva dependencia organizativa."""
    existing = await db.execute(
        select(Dependency).where(Dependency.codigo == body.codigo)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El código '{body.codigo}' ya está en uso",
        )
    dep = Dependency(
        nombre=body.nombre,
        codigo=body.codigo,
        descripcion=body.descripcion,
    )
    db.add(dep)
    await db.flush()

    await _log_audit(
        db,
        accion="DEPENDENCY_CREATE",
        usuario_id=current_user.id,
        entidad_tipo="dependencia",
        entidad_id=dep.id,
        detalle={"codigo": dep.codigo, "nombre": dep.nombre},
        ip=get_client_ip(request),
    )
    return DependencyResponse.model_validate(dep)


@router.patch("/dependencies/{dep_id}", response_model=DependencyResponse)
async def update_dependency(
    request: Request,
    dep_id: uuid.UUID,
    body: DependencyUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> DependencyResponse:
    """Actualiza una dependencia."""
    result = await db.execute(select(Dependency).where(Dependency.id == dep_id))
    dep = result.scalar_one_or_none()
    if dep is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dependencia no encontrada")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dep, field, value)

    await _log_audit(
        db,
        accion="DEPENDENCY_UPDATE",
        usuario_id=current_user.id,
        entidad_tipo="dependencia",
        entidad_id=dep.id,
        detalle=update_data,
        ip=get_client_ip(request),
    )
    return DependencyResponse.model_validate(dep)


# ── Export / Import de dependencias en JSON ──────────────────────────────────

@router.get("/dependencies/export")
async def export_dependencies(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Exporta todas las dependencias como archivo JSON descargable."""
    result = await db.execute(select(Dependency).order_by(Dependency.nombre))
    deps = result.scalars().all()
    payload = {
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "count": len(deps),
        "dependencies": [
            {
                "codigo": d.codigo,
                "nombre": d.nombre,
                "descripcion": d.descripcion,
                "activa": d.activa,
            }
            for d in deps
        ],
    }
    body = _json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    filename = f"dependencias_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    return StreamingResponse(
        iter([body]),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/dependencies/import")
async def import_dependencies(
    request: Request,
    file: UploadFile = File(..., description="Archivo JSON con la lista de dependencias"),
    replace: bool = Query(
        False,
        description="Si es true desactiva las dependencias existentes que no estén en el archivo",
    ),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Importa dependencias desde un archivo JSON.

    Formato aceptado:
      - Lista plana: ``[{"codigo": "...", "nombre": "...", "descripcion": "...", "activa": true}, ...]``
      - O envoltorio: ``{"dependencies": [...]}`` (ej. el exportado por este endpoint)

    Las dependencias se upsertan por ``codigo``: si existe se actualiza, si no se crea.
    Si ``replace=true``, las dependencias que ya existían y NO vienen en el archivo
    se marcan como inactivas (no se borran).
    """
    raw = await file.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío",
        )
    try:
        data = _json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, _json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"JSON inválido: {exc}",
        )

    if isinstance(data, dict) and "dependencies" in data:
        items = data["dependencies"]
    elif isinstance(data, list):
        items = data
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estructura no reconocida. Se esperaba una lista o {dependencies:[...]}.",
        )

    if not isinstance(items, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'dependencies' debe ser una lista",
        )

    # Index existente por codigo
    existing_result = await db.execute(select(Dependency))
    existing = {d.codigo: d for d in existing_result.scalars().all()}

    created = 0
    updated = 0
    skipped: list[dict] = []
    seen_codigos: set[str] = set()

    for idx, raw_item in enumerate(items):
        if not isinstance(raw_item, dict):
            skipped.append({"index": idx, "reason": "no es un objeto"})
            continue
        codigo = (raw_item.get("codigo") or "").strip()
        nombre = (raw_item.get("nombre") or "").strip()
        if not codigo or not nombre:
            skipped.append({"index": idx, "reason": "faltan codigo o nombre"})
            continue

        descripcion = raw_item.get("descripcion")
        activa_raw = raw_item.get("activa", raw_item.get("is_active", True))
        activa = bool(activa_raw) if activa_raw is not None else True
        seen_codigos.add(codigo)

        dep = existing.get(codigo)
        if dep is None:
            dep = Dependency(
                codigo=codigo,
                nombre=nombre,
                descripcion=descripcion,
                activa=activa,
            )
            db.add(dep)
            created += 1
        else:
            dep.nombre = nombre
            dep.descripcion = descripcion
            dep.activa = activa
            updated += 1

    deactivated = 0
    if replace:
        for codigo, dep in existing.items():
            if codigo not in seen_codigos and dep.activa:
                dep.activa = False
                deactivated += 1

    await db.flush()
    await _log_audit(
        db,
        accion="DEPENDENCY_IMPORT",
        usuario_id=current_user.id,
        entidad_tipo="dependencia",
        entidad_id=None,
        detalle={
            "filename": file.filename,
            "creadas": created,
            "actualizadas": updated,
            "desactivadas": deactivated,
            "omitidas": len(skipped),
            "replace": replace,
        },
        ip=get_client_ip(request),
    )
    return {
        "creadas": created,
        "actualizadas": updated,
        "desactivadas": deactivated,
        "omitidas": skipped,
        "total_procesadas": created + updated,
    }


# ── Pipelines ─────────────────────────────────────────────────────────────────

@router.get("/pipelines/status")
async def get_pipeline_status(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Retorna el estado de los últimos pipelines ejecutados."""
    result = await db.execute(
        select(PipelineRun)
        .order_by(PipelineRun.iniciado_en.desc())
        .limit(limit)
    )
    runs = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "tipo": r.tipo,
            "estado": r.estado.value,
            "formulario_id": str(r.formulario_id) if r.formulario_id else None,
            "detalles": r.detalles,
            "iniciado_en": r.iniciado_en.isoformat() if r.iniciado_en else None,
            "terminado_en": r.terminado_en.isoformat() if r.terminado_en else None,
        }
        for r in runs
    ]


# ── Auditoría ─────────────────────────────────────────────────────────────────

@router.get("/audit")
async def get_audit_log(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    usuario: Optional[str] = Query(None, description="Filtrar por nombre o email de usuario"),
    accion: Optional[str] = Query(None, description="Filtrar por acción (ej: LOGIN, FORM_APPROVE)"),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Log de auditoría paginado con filtros, ordenado de más reciente a más antiguo."""
    from sqlalchemy import and_, cast, Date as SADate, or_
    from sqlalchemy.orm import selectinload

    filters = []

    # Filtro por acción (insensible a mayúsculas)
    if accion:
        filters.append(AuditLog.accion.ilike(f"%{accion}%"))

    # Filtro por fecha
    if start_date:
        try:
            filters.append(
                cast(AuditLog.created_at, SADate) >= datetime.strptime(start_date, "%Y-%m-%d").date()
            )
        except ValueError:
            pass
    if end_date:
        try:
            filters.append(
                cast(AuditLog.created_at, SADate) <= datetime.strptime(end_date, "%Y-%m-%d").date()
            )
        except ValueError:
            pass

    # Filtro por usuario (nombre o email) — requires subquery via join
    if usuario:
        filters.append(
            AuditLog.usuario_id.in_(
                select(User.id).where(
                    or_(
                        User.nombre_completo.ilike(f"%{usuario}%"),
                        User.email.ilike(f"%{usuario}%"),
                    )
                )
            )
        )

    base_query = select(AuditLog).where(and_(*filters)) if filters else select(AuditLog)

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * size
    result = await db.execute(
        base_query
        .options(selectinload(AuditLog.usuario))
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    logs = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [
            {
                "id": str(log.id),
                "fecha": log.created_at.isoformat(),
                "usuario": log.usuario.nombre_completo if log.usuario else "Sistema",
                "usuario_email": log.usuario.email if log.usuario else None,
                "accion": log.accion,
                "entidad": f"{log.entidad_tipo or ''} {str(log.entidad_id)[:8] if log.entidad_id else ''}".strip() or None,
                "entidad_tipo": log.entidad_tipo,
                "detalle": log.detalle,
                "ip": str(log.ip_address) if log.ip_address else None,
            }
            for log in logs
        ],
    }


# ── Overview del sistema ──────────────────────────────────────────────────────

@router.get("/stats/overview", response_model=SystemOverviewResponse)
async def get_system_overview(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> SystemOverviewResponse:
    """Métricas globales del sistema para el dashboard de administración."""
    from app.models.template import Template
    from app.schemas.stats import UltimoPipelineInfo

    # ── Usuarios ────────────────────────────────────────────────────────────
    total_usuarios   = await db.scalar(select(func.count(User.id))) or 0
    usuarios_activos = await db.scalar(
        select(func.count(User.id)).where(User.activo == True)
    ) or 0

    # ── Templates ───────────────────────────────────────────────────────────
    total_templates    = await db.scalar(select(func.count(Template.id))) or 0
    templates_activos  = await db.scalar(
        select(func.count(Template.id)).where(Template.activo == True)
    ) or 0

    # ── Dependencias ────────────────────────────────────────────────────────
    total_deps = await db.scalar(
        select(func.count(Dependency.id)).where(Dependency.activa == True)
    ) or 0

    # ── Formularios (por estado) ────────────────────────────────────────────
    total_forms = await db.scalar(select(func.count(Form.id))) or 0
    counts_by_estado = await db.execute(
        select(Form.estado, func.count(Form.id)).group_by(Form.estado)
    )
    forms_by_estado = {e.value if hasattr(e, "value") else str(e): n
                       for e, n in counts_by_estado.all()}

    # ── Pipelines ───────────────────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    inicio_dia = now.replace(hour=0, minute=0, second=0, microsecond=0)
    pipelines_hoy = await db.scalar(
        select(func.count(PipelineRun.id))
        .where(PipelineRun.iniciado_en >= inicio_dia)
    ) or 0

    last_run_result = await db.execute(
        select(PipelineRun).order_by(PipelineRun.iniciado_en.desc()).limit(1)
    )
    last_run = last_run_result.scalar_one_or_none()
    ultimo = None
    if last_run is not None:
        estado_val = last_run.estado.value if hasattr(last_run.estado, "value") else str(last_run.estado)
        ultimo = UltimoPipelineInfo(estado=estado_val, iniciado=last_run.iniciado_en)

    return SystemOverviewResponse(
        total_formularios=total_forms,
        formularios_draft=forms_by_estado.get("draft", 0),
        formularios_pending=forms_by_estado.get("pending", 0),
        formularios_approved=forms_by_estado.get("approved", 0),
        formularios_rejected=forms_by_estado.get("rejected", 0),
        usuarios_activos=usuarios_activos,
        total_usuarios=total_usuarios,
        templates_activos=templates_activos,
        total_templates=total_templates,
        total_dependencias=total_deps,
        pipelines_hoy=pipelines_hoy,
        ultimo_pipeline=ultimo,
    )

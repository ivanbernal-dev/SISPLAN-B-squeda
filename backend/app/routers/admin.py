"""
app/routers/admin.py — Endpoints de administración: usuarios, dependencias, pipelines y auditoría.
"""
import secrets
import string
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
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
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Log de auditoría paginado, ordenado de más reciente a más antiguo."""
    offset = (page - 1) * size
    count_result = await db.execute(select(func.count(AuditLog.id)))
    total = count_result.scalar_one()

    result = await db.execute(
        select(AuditLog)
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
                "usuario_id": str(log.usuario_id) if log.usuario_id else None,
                "accion": log.accion,
                "entidad_tipo": log.entidad_tipo,
                "entidad_id": str(log.entidad_id) if log.entidad_id else None,
                "detalle": log.detalle,
                "ip_address": str(log.ip_address) if log.ip_address else None,
                "created_at": log.created_at.isoformat(),
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
    """Métricas globales del sistema."""
    from app.models.template import Template

    total_usuarios = await db.scalar(select(func.count(User.id)).where(User.activo == True))
    total_deps = await db.scalar(select(func.count(Dependency.id)).where(Dependency.activa == True))
    total_templates = await db.scalar(select(func.count(Template.id)).where(Template.activo == True))

    async def _count_forms(estado: FormStatus) -> int:
        return await db.scalar(select(func.count(Form.id)).where(Form.estado == estado)) or 0

    last_run_result = await db.execute(
        select(PipelineRun).order_by(PipelineRun.iniciado_en.desc()).limit(1)
    )
    last_run = last_run_result.scalar_one_or_none()

    return SystemOverviewResponse(
        total_usuarios_activos=total_usuarios or 0,
        total_dependencias=total_deps or 0,
        total_templates=total_templates or 0,
        formularios_draft=await _count_forms(FormStatus.draft),
        formularios_pending=await _count_forms(FormStatus.pending),
        formularios_approved=await _count_forms(FormStatus.approved),
        formularios_rejected=await _count_forms(FormStatus.rejected),
        ultimo_pipeline=last_run.iniciado_en if last_run else None,
        estado_ultimo_pipeline=last_run.estado.value if last_run else None,
    )

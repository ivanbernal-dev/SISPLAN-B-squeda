"""
app/routers/auth.py — Endpoints de autenticación y gestión de sesión.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_any_authenticated, get_client_ip, get_current_user
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    ChangePasswordRequest,
    LoginRequest,
    TokenResponse,
    UserInfo,
    RefreshRequest,
)
from app.services.auth_service import (
    authenticate_user,
    build_token_payload,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


async def _log_audit(
    db: AsyncSession,
    accion: str,
    usuario_id=None,
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


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Autentica al usuario y retorna tokens JWT."""
    user = await authenticate_user(db, body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    # Actualizar last_login
    user.last_login = datetime.now(timezone.utc)

    payload = build_token_payload(user)
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    await _log_audit(
        db,
        accion="LOGIN",
        usuario_id=user.id,
        entidad_tipo="usuario",
        entidad_id=user.id,
        detalle={"username": user.username},
        ip=get_client_ip(request),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo(
            id=user.id,
            username=user.username,
            nombre_completo=user.nombre_completo,
            role=user.role,
            dependency_id=user.dependency_id,
            requires_password_change=user.requires_password_change,
        ),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> AccessTokenResponse:
    """Renueva el access token usando el refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token inválido o expirado",
    )
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise credentials_exception
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    from sqlalchemy import select
    from app.models.user import User as UserModel
    import uuid

    result = await db.execute(
        select(UserModel).where(
            UserModel.id == uuid.UUID(user_id), UserModel.activo == True
        )
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    new_access_token = create_access_token(build_token_payload(user))
    return AccessTokenResponse(access_token=new_access_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Registra el logout en el log de auditoría.
    El cliente debe descartar los tokens localmente.
    """
    await _log_audit(
        db,
        accion="LOGOUT",
        usuario_id=current_user.id,
        entidad_tipo="usuario",
        entidad_id=current_user.id,
        ip=get_client_ip(request),
    )
    return {"detail": "Sesión cerrada exitosamente"}


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cambia la contraseña del usuario autenticado."""
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta",
        )
    current_user.password_hash = hash_password(body.new_password)
    current_user.requires_password_change = False

    await _log_audit(
        db,
        accion="CHANGE_PASSWORD",
        usuario_id=current_user.id,
        entidad_tipo="usuario",
        entidad_id=current_user.id,
        ip=get_client_ip(request),
    )
    return {"detail": "Contraseña actualizada exitosamente"}

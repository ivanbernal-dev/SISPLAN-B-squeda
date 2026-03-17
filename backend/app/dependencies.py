"""
app/dependencies.py — Dependencias FastAPI para autenticación y autorización.
"""
import uuid
from typing import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import decode_token

# ── Bearer token extractor ────────────────────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extrae el JWT del header Authorization, lo valida y retorna el User de la BD.
    Lanza HTTP 401 si el token es inválido o el usuario no existe/está inactivo.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado o token inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        user_id_str: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if user_id_str is None or token_type != "access":
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(
        select(User).where(User.id == user_id, User.activo == True)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


# ── Role-based access control ─────────────────────────────────────────────────
def require_role(*roles: UserRole) -> Callable:
    """
    Factory que retorna una dependencia FastAPI la cual verifica
    que el usuario autenticado tenga uno de los roles indicados.
    """

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere uno de los siguientes roles: {[r.value for r in roles]}",
            )
        return current_user

    return role_checker


# ── Shortcuts de roles ────────────────────────────────────────────────────────
get_admin_user = require_role(UserRole.admin)
get_validator_user = require_role(UserRole.validator)
get_admin_or_validator = require_role(UserRole.admin, UserRole.validator)
get_dependency_user = require_role(UserRole.dependency_user)
get_any_authenticated = require_role(
    UserRole.admin, UserRole.validator, UserRole.dependency_user
)


# ── Utilidades ────────────────────────────────────────────────────────────────
def get_client_ip(request: Request) -> str | None:
    """Extrae la IP del cliente del request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None

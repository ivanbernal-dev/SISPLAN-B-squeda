"""
app/services/auth_service.py — Servicio de autenticación JWT + bcrypt.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User

# ── Contexto bcrypt ───────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password helpers ──────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Retorna el hash bcrypt de la contraseña en texto plano."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña en texto plano coincide con el hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT helpers ───────────────────────────────────────────────────────────────
def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Genera un access token JWT con expiración configurable."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(data: dict) -> str:
    """Genera un refresh token JWT con expiración de 7 días."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_token(token: str) -> dict:
    """
    Decodifica y verifica un JWT.
    Lanza JWTError si el token es inválido o expirado.
    """
    return jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )


# ── Autenticación de usuario ──────────────────────────────────────────────────
async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Optional[User]:
    """
    Busca al usuario por username y verifica la contraseña.
    Retorna el objeto User si las credenciales son válidas, None en caso contrario.
    """
    result = await db.execute(
        select(User).where(User.username == username, User.activo == True)
    )
    user = result.scalar_one_or_none()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def build_token_payload(user: User) -> dict:
    """Construye el payload JWT a partir del usuario."""
    return {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role.value,
        "dependency_id": str(user.dependency_id) if user.dependency_id else None,
    }

"""
app/schemas/user.py — Schemas Pydantic para gestión de usuarios.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    nombre_completo: str = Field(..., min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    role: UserRole
    dependency_id: Optional[uuid.UUID] = None


class UserUpdate(BaseModel):
    nombre_completo: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    dependency_id: Optional[uuid.UUID] = None
    activo: Optional[bool] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    nombre_completo: str
    email: Optional[str] = None
    role: UserRole
    dependency_id: Optional[uuid.UUID] = None
    activo: bool
    requires_password_change: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserCreateResponse(BaseModel):
    id: uuid.UUID
    username: str
    requires_password_change: bool = True
    temp_password: str


class UserListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[UserResponse]

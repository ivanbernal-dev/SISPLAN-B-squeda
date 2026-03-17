"""
app/schemas/auth.py — Schemas Pydantic para autenticación y tokens JWT.
"""
import uuid
from typing import Optional

from pydantic import BaseModel, Field

from app.models.user import UserRole


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class UserInfo(BaseModel):
    id: uuid.UUID
    username: str
    nombre_completo: str
    role: UserRole
    dependency_id: Optional[uuid.UUID] = None
    requires_password_change: bool = False

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserInfo


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    def model_post_init(self, __context) -> None:
        if self.new_password != self.confirm_password:
            raise ValueError("Las contraseñas nuevas no coinciden")

"""
app/schemas/dependency.py — Schemas Pydantic para dependencias organizativas.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DependencyCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=255)
    codigo: str = Field(..., min_length=2, max_length=50, pattern=r"^[A-Z0-9_-]+$")
    descripcion: Optional[str] = None


class DependencyUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=255)
    descripcion: Optional[str] = None
    activa: Optional[bool] = None


class DependencyResponse(BaseModel):
    id: uuid.UUID
    nombre: str
    codigo: str
    descripcion: Optional[str] = None
    activa: bool
    created_at: datetime

    model_config = {"from_attributes": True}

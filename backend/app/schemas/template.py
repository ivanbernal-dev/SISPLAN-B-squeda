"""
app/schemas/template.py — Schemas Pydantic para templates de formularios.
"""
import uuid
from datetime import datetime
from typing import Any, List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator


# ── Configuración de Campos ────────────────────────────────────────────────────
FieldType = Literal["text", "number", "date", "select", "textarea", "computed"]


class FieldConfig(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=255)
    type: FieldType = "text"
    readonly: bool = False
    default: Optional[Any] = None
    required: bool = True
    options: Optional[List[str]] = None  # Para campos select

    model_config = {"from_attributes": True}


class TemplateSchema(BaseModel):
    fields: List[FieldConfig] = []


# ── Template CRUD ──────────────────────────────────────────────────────────────
class TemplateCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=255)
    descripcion: Optional[str] = None
    indicador_nivel1_id: Optional[int] = None
    codigo_markdown: str = Field(..., min_length=1)
    configuracion_campos: Optional[TemplateSchema] = None


class TemplateUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=255)
    descripcion: Optional[str] = None
    indicador_nivel1_id: Optional[int] = None
    codigo_markdown: Optional[str] = None
    configuracion_campos: Optional[TemplateSchema] = None
    activo: Optional[bool] = None


class TemplateResponse(BaseModel):
    id: uuid.UUID
    nombre: str
    descripcion: Optional[str] = None
    codigo: Optional[str] = None
    indicador_nivel1_id: Optional[int] = None
    indicador_nivel2_id: Optional[int] = None
    codigo_markdown: str
    configuracion_campos: dict
    version: int
    activo: bool
    # Campos derivados que espera el frontend
    is_active: bool = False
    campos_count: int = 0
    indicador_nombre: Optional[str] = None
    created_by_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def _compute_derived(self) -> "TemplateResponse":
        # is_active: alias de activo
        self.is_active = self.activo
        # campos_count: contar campos en la configuracion_campos JSONB
        cfg = self.configuracion_campos or {}
        # Soporta dos estructuras: {"campos": [...]} y {"fields": [...]}
        campos = cfg.get("campos") or cfg.get("fields") or []
        self.campos_count = len(campos)
        return self


class TemplatePreviewRequest(BaseModel):
    codigo_markdown: str = Field(..., min_length=1)


class TemplatePreviewResponse(BaseModel):
    configuracion_campos: TemplateSchema
    markdown_html: str

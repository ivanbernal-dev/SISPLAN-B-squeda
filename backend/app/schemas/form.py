"""
app/schemas/form.py — Schemas Pydantic para formularios respondidos.
"""
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.form import FormStatus
from app.schemas.file import FileResponse


class FormCreate(BaseModel):
    plantilla_id: uuid.UUID
    datos_dinamicos: Dict[str, Any] = Field(default_factory=dict)
    informe_cualitativo: Optional[str] = None
    fecha_usuario: Optional[date] = None


class FormUpdate(BaseModel):
    datos_dinamicos: Optional[Dict[str, Any]] = None
    informe_cualitativo: Optional[str] = None
    fecha_usuario: Optional[date] = None


class FormSubmit(BaseModel):
    """Enviar formulario a revisión (sin cambios de datos)."""
    pass


class RejectRequest(BaseModel):
    comentario: str = Field(..., min_length=10, max_length=2000)


class FormResponse(BaseModel):
    id: uuid.UUID
    plantilla_id: uuid.UUID
    usuario_id: uuid.UUID
    dependency_id: uuid.UUID
    datos_dinamicos: Dict[str, Any]
    informe_cualitativo: Optional[str] = None
    fecha_usuario: Optional[date] = None
    fecha_carga: datetime
    fecha_edicion: datetime
    estado: FormStatus
    comentario_rechazo: Optional[str] = None
    validado_por_id: Optional[uuid.UUID] = None
    fecha_validacion: Optional[datetime] = None
    archivos: List[FileResponse] = []

    model_config = {"from_attributes": True}


class FormListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[FormResponse]

"""
app/schemas/form.py — Schemas Pydantic para formularios respondidos.
"""
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

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
    # Campos derivados de relaciones
    template_nombre: Optional[str] = None
    dependencia_nombre: Optional[str] = None
    usuario_nombre: Optional[str] = None
    validador_nombre: Optional[str] = None
    validador_correo: Optional[str] = None
    archivos: List[FileResponse] = []
    # Lista completa de campos del template (incluye validator_only) — la usa el
    # validador para renderizar el panel OAP al aprobar un formulario individual.
    template_fields: List[Dict[str, Any]] = []

    model_config = {"from_attributes": True}

    @model_validator(mode="wrap")
    @classmethod
    def _populate_relations(cls, value: Any, handler: Any) -> "FormResponse":
        instance = handler(value)
        if hasattr(value, "plantilla") and value.plantilla is not None:
            instance.template_nombre = value.plantilla.nombre
            cfg = value.plantilla.configuracion_campos or {}
            instance.template_fields = list(cfg.get("fields") or cfg.get("campos") or [])
        if hasattr(value, "dependency") and value.dependency is not None:
            instance.dependencia_nombre = value.dependency.nombre
        if hasattr(value, "usuario") and value.usuario is not None:
            instance.usuario_nombre = value.usuario.nombre_completo
        if hasattr(value, "validado_por") and value.validado_por is not None:
            instance.validador_nombre = value.validado_por.nombre_completo
            instance.validador_correo = value.validado_por.email
        return instance


class FormListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[FormResponse]

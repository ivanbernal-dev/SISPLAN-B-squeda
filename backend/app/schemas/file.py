"""
app/schemas/file.py — Schemas Pydantic para archivos adjuntos.
"""
import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, model_validator


class FileResponse(BaseModel):
    id: uuid.UUID
    formulario_id: uuid.UUID
    nombre_original: str
    nombre_minio: str
    bucket: str
    ruta_minio: str
    tipo_mime: Optional[str] = None
    tamaño_bytes: Optional[int] = None
    uploaded_at: datetime

    # Alias compatibles con el frontend (FileRecord)
    nombre: str = ""
    tamanio: int = 0
    tipo: Optional[str] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="wrap")
    @classmethod
    def _set_aliases(cls, value: Any, handler: Any) -> "FileResponse":
        instance = handler(value)
        instance.nombre = instance.nombre_original
        instance.tamanio = instance.tamaño_bytes or 0
        instance.tipo = instance.tipo_mime
        return instance


class FileUrlResponse(BaseModel):
    file_id: uuid.UUID
    nombre_original: str
    url: str
    expires_in_seconds: int

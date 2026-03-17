"""
app/schemas/file.py — Schemas Pydantic para archivos adjuntos.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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

    model_config = {"from_attributes": True}


class FileUrlResponse(BaseModel):
    file_id: uuid.UUID
    nombre_original: str
    url: str
    expires_in_seconds: int

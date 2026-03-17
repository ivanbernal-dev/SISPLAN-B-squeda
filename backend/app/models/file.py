"""
app/models/file.py — Modelo SQLAlchemy para la tabla `archivos`.
"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Archivo(Base):
    __tablename__ = "archivos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    formulario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("formularios_respondidos.id", ondelete="CASCADE"),
        nullable=False,
    )
    nombre_original: Mapped[str] = mapped_column(String(500), nullable=False)
    nombre_minio: Mapped[str] = mapped_column(String(500), nullable=False)
    bucket: Mapped[str] = mapped_column(
        String(100), nullable=False, default="ubpd-formularios"
    )
    ruta_minio: Mapped[str] = mapped_column(String(1000), nullable=False)
    tipo_mime: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tamaño_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relaciones ─────────────────────────────────────────────
    formulario: Mapped["Form"] = relationship(  # type: ignore[name-defined]
        "Form", back_populates="archivos", lazy="selectin"
    )

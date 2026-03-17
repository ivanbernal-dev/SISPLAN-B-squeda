"""
app/models/dependency.py — Modelo SQLAlchemy para la tabla `dependencias`.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Dependency(Base):
    __tablename__ = "dependencias"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relaciones ─────────────────────────────────────────────
    usuarios: Mapped[list["User"]] = relationship(  # type: ignore[name-defined]
        "User", back_populates="dependency", lazy="noload"
    )
    formularios: Mapped[list["Form"]] = relationship(  # type: ignore[name-defined]
        "Form", back_populates="dependency", lazy="noload"
    )

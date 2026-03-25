"""
app/models/template.py — Modelo SQLAlchemy para la tabla `templates`.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    codigo: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    indicador_nivel1_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("indicadores_nivel1.id", ondelete="SET NULL"),
        nullable=True,
    )
    indicador_nivel2_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("indicadores_nivel2.id", ondelete="SET NULL"),
        nullable=True,
    )
    codigo_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    configuracion_campos: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relaciones ─────────────────────────────────────────────
    indicador: Mapped["Indicator | None"] = relationship(  # type: ignore[name-defined]
        "Indicator", back_populates="templates", lazy="selectin"
    )
    indicador_nivel2: Mapped["IndicadorNivel2 | None"] = relationship(  # type: ignore[name-defined]
        "IndicadorNivel2", back_populates="templates", lazy="selectin"
    )
    created_by: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="created_templates", lazy="selectin"
    )
    formularios: Mapped[list["Form"]] = relationship(  # type: ignore[name-defined]
        "Form", back_populates="plantilla", lazy="noload"
    )
    fact_stats: Mapped[list["FactStats"]] = relationship(  # type: ignore[name-defined]
        "FactStats", back_populates="template", lazy="noload"
    )

"""
app/models/fact_stats.py — Tabla de hechos para estadísticas de completitud.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FactStats(Base):
    __tablename__ = "fact_stats"

    __table_args__ = (
        Index("idx_fact_stats_fecha", "fecha_aprobacion"),
        Index("idx_fact_stats_indicador", "indicador_id"),
        Index("idx_fact_stats_template", "template_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    formulario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("formularios_respondidos.id", ondelete="CASCADE"),
        nullable=False,
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    indicador_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("indicadores_nivel1.id", ondelete="CASCADE"),
        nullable=False,
    )
    dependency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dependencias.id", ondelete="CASCADE"),
        nullable=False,
    )
    campos_llenos: Mapped[int] = mapped_column(Integer, nullable=False)
    campos_totales: Mapped[int] = mapped_column(Integer, nullable=False)
    completitud: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    fecha_referencia: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_aprobacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    calculado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relaciones ─────────────────────────────────────────────
    formulario: Mapped["Form"] = relationship(  # type: ignore[name-defined]
        "Form", back_populates="fact_stats", lazy="selectin"
    )
    template: Mapped["Template"] = relationship(  # type: ignore[name-defined]
        "Template", back_populates="fact_stats", lazy="selectin"
    )
    indicador: Mapped["Indicator"] = relationship(  # type: ignore[name-defined]
        "Indicator", back_populates="fact_stats", lazy="selectin"
    )
    dependency: Mapped["Dependency"] = relationship(  # type: ignore[name-defined]
        "Dependency", lazy="selectin"
    )

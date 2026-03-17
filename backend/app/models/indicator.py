"""
app/models/indicator.py — Modelo SQLAlchemy para `indicadores_nivel1`.
"""
import enum
from decimal import Decimal

from sqlalchemy import Boolean, Enum, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FormulaTipo(str, enum.Enum):
    promedio_simple = "promedio_simple"
    promedio_ponderado = "promedio_ponderado"
    conteo = "conteo"
    personalizado = "personalizado"


class Indicator(Base):
    __tablename__ = "indicadores_nivel1"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    formula_tipo: Mapped[FormulaTipo] = mapped_column(
        Enum(FormulaTipo, name="formula_tipo"),
        default=FormulaTipo.promedio_simple,
        nullable=False,
    )
    peso: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("1.0"), nullable=False
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Relaciones ─────────────────────────────────────────────
    templates: Mapped[list["Template"]] = relationship(  # type: ignore[name-defined]
        "Template", back_populates="indicador", lazy="noload"
    )
    fact_stats: Mapped[list["FactStats"]] = relationship(  # type: ignore[name-defined]
        "FactStats", back_populates="indicador", lazy="noload"
    )

"""IndicadorNivel2 — Sub-indicadores del nivel 2 (agrupadores de templates)."""
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class IndicadorNivel2(Base):
    __tablename__ = "indicadores_nivel2"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    indicador_nivel1_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("indicadores_nivel1.id", ondelete="CASCADE"),
        nullable=False,
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relations
    indicador_nivel1: Mapped["Indicator"] = relationship(  # type: ignore[name-defined]
        "Indicator", back_populates="indicadores_nivel2", lazy="selectin"
    )
    templates: Mapped[list["Template"]] = relationship(  # type: ignore[name-defined]
        "Template", back_populates="indicador_nivel2", lazy="noload"
    )

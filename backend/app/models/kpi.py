"""
app/models/kpi.py — Resultados KPI del pipeline script y definición del script activo.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class KpiResultado(Base):
    """Almacena los valores KPI calculados por el script de pipeline."""

    __tablename__ = "kpi_resultados"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nivel = Column(Integer, nullable=False)          # 1 = nivel1, 2 = nivel2
    kpi_key = Column(String(120), unique=True, nullable=False)
    kpi_label = Column(String(200), nullable=False)
    valor = Column(Float, default=0.0)
    nivel1_key = Column(String(120), nullable=True)   # FK lógica al KPI padre (nivel 2)
    template_id = Column(String(36), nullable=True)   # UUID del template DB asociado
    descripcion = Column(Text, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class PipelineScript(Base):
    """Almacena el script Python activo para el pipeline de indicadores."""

    __tablename__ = "pipeline_scripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(200), default="Pipeline Principal")
    codigo = Column(Text, nullable=False, default="")
    activo = Column(Boolean, default=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

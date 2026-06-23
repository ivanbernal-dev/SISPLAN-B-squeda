"""
app/models/bi_data.py — Modelos para Dashboard BI (Metas GITT / Planes Regionales).
Datos cargados directamente desde Excel y visualizados en dashboard público.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class BiDataset(Base):
    """Metadatos del último Excel BI cargado."""

    __tablename__ = "bi_dataset"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(500), nullable=False)
    uploaded_by = Column(String(200), nullable=True)
    total_rows = Column(Integer, default=0)
    total_prb = Column(Integer, default=0)
    total_indicadores = Column(Integer, default=0)
    anio = Column(Integer, nullable=True)
    uploaded_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class BiPRB(Base):
    """Catálogo de Planes Regionales de Búsqueda."""

    __tablename__ = "bi_prb"

    cod = Column(Integer, primary_key=True)
    prb = Column(String(500), nullable=False)
    regional = Column(String(100), nullable=True, index=True)
    gitt = Column(String(100), nullable=True, index=True)


class BiEstructura(Base):
    """Estructura jerárquica de indicadores (Línea → Resultado → Indicador)."""

    __tablename__ = "bi_estructura"

    cod_indicador = Column(Integer, primary_key=True)
    codigo_indicador = Column(String(50), nullable=True)
    indicador = Column(String(500), nullable=True)
    cod_linea = Column(Integer, nullable=True, index=True)
    linea = Column(String(500), nullable=True)
    cod_resultado = Column(Integer, nullable=True, index=True)
    resultado = Column(String(500), nullable=True)


class BiHistorico(Base):
    """
    Tabla principal: avance mensual y metas por (PRB, Indicador, Año).
    Cada fila es un indicador específico dentro de un PRB dado un año.
    """

    __tablename__ = "bi_historico"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cod_prb = Column(Integer, nullable=False, index=True)
    prb = Column(String(500), nullable=True)
    cod_indicador = Column(Integer, nullable=False, index=True)
    codigo_indicador = Column(String(50), nullable=True)
    indicador = Column(Text, nullable=True)
    anio = Column(Integer, nullable=False, index=True)

    linea_base = Column(Float, default=0)
    meta = Column(Float, default=0)

    mes_1 = Column(Float, default=0)
    mes_2 = Column(Float, default=0)
    mes_3 = Column(Float, default=0)
    mes_4 = Column(Float, default=0)
    mes_5 = Column(Float, default=0)
    mes_6 = Column(Float, default=0)
    mes_7 = Column(Float, default=0)
    mes_8 = Column(Float, default=0)
    mes_9 = Column(Float, default=0)
    mes_10 = Column(Float, default=0)
    mes_11 = Column(Float, default=0)
    mes_12 = Column(Float, default=0)

    trim_i = Column(Float, default=0)
    trim_ii = Column(Float, default=0)
    trim_iii = Column(Float, default=0)
    trim_iv = Column(Float, default=0)

    avance_total = Column(Float, default=0)
    pct_avance = Column(Float, default=0)
    variacion = Column(Float, default=0)

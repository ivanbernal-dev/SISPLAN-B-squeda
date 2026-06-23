"""
app/schemas/stats.py — Schemas Pydantic para estadísticas públicas.
"""
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StatsQueryParams(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# ── Nivel 1 — Global ──────────────────────────────────────────────────────────
class GlobalStatsItem(BaseModel):
    indicador_id: int
    nombre: str
    completitud_promedio: float
    total_formularios: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class GlobalStatsResponse(BaseModel):
    items: List[GlobalStatsItem]
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# ── Nivel 2 — Por Template ────────────────────────────────────────────────────
class TemplateStatsItem(BaseModel):
    template_id: uuid.UUID
    nombre: str
    completitud: float
    total_formularios: int


class TemplateStatsResponse(BaseModel):
    indicador_id: int
    indicador_nombre: str
    items: List[TemplateStatsItem]
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# ── Nivel 3 — Detalle Formularios ─────────────────────────────────────────────
class DetailedFormItem(BaseModel):
    id: uuid.UUID
    fecha_referencia: Optional[date] = None
    fecha_carga: datetime
    dependencia: str
    usuario: str
    informe_cualitativo: Optional[str] = None
    datos_dinamicos: Dict[str, Any]
    archivos_count: int


class DetailedFormResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[DetailedFormItem]


# ── Indicadores ───────────────────────────────────────────────────────────────
class IndicatorResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    formula_tipo: str
    peso: float
    activo: bool

    model_config = {"from_attributes": True}


# ── Overview del Sistema (Admin) ──────────────────────────────────────────────
class UltimoPipelineInfo(BaseModel):
    estado:   str                 # "success" | "error" | "running"
    iniciado: datetime


class SystemOverviewResponse(BaseModel):
    # Formularios
    total_formularios:     int
    formularios_draft:     int
    formularios_pending:   int
    formularios_approved:  int
    formularios_rejected:  int
    # Usuarios
    usuarios_activos:      int
    total_usuarios:        int
    # Templates
    templates_activos:     int
    total_templates:       int
    # Dependencias (opcional, mantenido para compatibilidad)
    total_dependencias:    int = 0
    # Pipelines
    pipelines_hoy:         int = 0
    ultimo_pipeline:       Optional[UltimoPipelineInfo] = None

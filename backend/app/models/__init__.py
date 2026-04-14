"""
app/models/__init__.py — Registro de todos los modelos SQLAlchemy.
Importar este paquete asegura que todas las tablas sean conocidas por Base.metadata.
"""
from app.models.audit_log import AuditLog
from app.models.kpi import KpiResultado, PipelineScript
from app.models.dependency import Dependency
from app.models.fact_stats import FactStats
from app.models.file import Archivo
from app.models.form import Form, FormStatus
from app.models.indicator import Indicator, FormulaTipo
from app.models.indicador_nivel2 import IndicadorNivel2
from app.models.pipeline_definicion import PipelineDefinicion
from app.models.pipeline_ejecucion import PipelineEjecucion
from app.models.pipeline_run import PipelineRun, PipelineStatus
from app.models.template import Template
from app.models.user import User, UserRole

__all__ = [
    "AuditLog",
    "KpiResultado",
    "PipelineScript",
    "Dependency",
    "FactStats",
    "Archivo",
    "Form",
    "FormStatus",
    "Indicator",
    "FormulaTipo",
    "IndicadorNivel2",
    "PipelineDefinicion",
    "PipelineEjecucion",
    "PipelineRun",
    "PipelineStatus",
    "Template",
    "User",
    "UserRole",
]

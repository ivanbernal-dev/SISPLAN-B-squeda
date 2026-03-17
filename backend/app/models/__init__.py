"""
app/models/__init__.py — Registro de todos los modelos SQLAlchemy.
Importar este paquete asegura que todas las tablas sean conocidas por Base.metadata.
"""
from app.models.audit_log import AuditLog
from app.models.dependency import Dependency
from app.models.fact_stats import FactStats
from app.models.file import Archivo
from app.models.form import Form, FormStatus
from app.models.indicator import Indicator, FormulaTipo
from app.models.pipeline_run import PipelineRun, PipelineStatus
from app.models.template import Template
from app.models.user import User, UserRole

__all__ = [
    "AuditLog",
    "Dependency",
    "FactStats",
    "Archivo",
    "Form",
    "FormStatus",
    "Indicator",
    "FormulaTipo",
    "PipelineRun",
    "PipelineStatus",
    "Template",
    "User",
    "UserRole",
]

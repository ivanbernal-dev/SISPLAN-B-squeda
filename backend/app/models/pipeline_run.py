"""
app/models/pipeline_run.py — Registro de ejecuciones del pipeline de estadísticas.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PipelineStatus(str, enum.Enum):
    running = "running"
    success = "success"
    error = "error"


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tipo: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus, name="pipeline_status"),
        default=PipelineStatus.running,
        nullable=False,
    )
    formulario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("formularios_respondidos.id", ondelete="SET NULL"),
        nullable=True,
    )
    detalles: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    iniciado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    terminado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relaciones ─────────────────────────────────────────────
    formulario: Mapped["Form | None"] = relationship(  # type: ignore[name-defined]
        "Form", lazy="selectin"
    )

"""PipelineEjecucion — Log de ejecuciones del pipeline visual."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PipelineEjecucion(Base):
    __tablename__ = "pipeline_ejecuciones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pipeline_definiciones.id", ondelete="CASCADE"),
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="running"
    )  # running|success|error
    log_debug: Mapped[str | None] = mapped_column(Text, nullable=True)
    resultado: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    iniciado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    terminado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    disparado_por: Mapped[str] = mapped_column(
        String(50), nullable=False, default="manual"
    )  # manual|scheduled|form_approved

    pipeline: Mapped["PipelineDefinicion"] = relationship(  # type: ignore[name-defined]
        "PipelineDefinicion", back_populates="ejecuciones", lazy="selectin"
    )

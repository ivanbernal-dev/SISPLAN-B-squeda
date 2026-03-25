"""PipelineDefinicion — Definición visual de pipelines de procesamiento."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PipelineDefinicion(Base):
    __tablename__ = "pipeline_definiciones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Visual graph: {nodes: [...], edges: [...]}
    # Node types: data_source | processor | nivel2_output | nivel1_output
    # Node data fields: template_id, indicador_nivel2_id, indicador_nivel1_id, codigo_python, nombre, descripcion
    grafo: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=lambda: {"nodes": [], "edges": []}
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    created_by: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        "User", lazy="selectin"
    )
    ejecuciones: Mapped[list["PipelineEjecucion"]] = relationship(  # type: ignore[name-defined]
        "PipelineEjecucion",
        back_populates="pipeline",
        lazy="noload",
        cascade="all, delete-orphan",
    )

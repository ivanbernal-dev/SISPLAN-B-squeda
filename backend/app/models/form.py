"""
app/models/form.py — Modelo SQLAlchemy para `formularios_respondidos`.
"""
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FormStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Form(Base):
    __tablename__ = "formularios_respondidos"

    __table_args__ = (
        CheckConstraint(
            "estado != 'rejected' OR comentario_rechazo IS NOT NULL",
            name="chk_rechazo",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plantilla_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("templates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    dependency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dependencias.id", ondelete="RESTRICT"),
        nullable=False,
    )
    datos_dinamicos: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    informe_cualitativo: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_usuario: Mapped[date | None] = mapped_column(
        Date, server_default=func.current_date(), nullable=True
    )
    fecha_carga: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    fecha_edicion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    estado: Mapped[FormStatus] = mapped_column(
        Enum(FormStatus, name="form_status"),
        default=FormStatus.draft,
        nullable=False,
    )
    comentario_rechazo: Mapped[str | None] = mapped_column(Text, nullable=True)
    cargado_via_excel: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    fecha_validacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relaciones ─────────────────────────────────────────────
    plantilla: Mapped["Template"] = relationship(  # type: ignore[name-defined]
        "Template", back_populates="formularios", lazy="selectin"
    )
    usuario: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User",
        back_populates="forms",
        foreign_keys=[usuario_id],
        lazy="selectin",
    )
    dependency: Mapped["Dependency"] = relationship(  # type: ignore[name-defined]
        "Dependency", back_populates="formularios", lazy="selectin"
    )
    validado_por: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        "User",
        back_populates="validated_forms",
        foreign_keys=[validado_por_id],
        lazy="selectin",
    )
    archivos: Mapped[list["Archivo"]] = relationship(  # type: ignore[name-defined]
        "Archivo",
        back_populates="formulario",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    fact_stats: Mapped[list["FactStats"]] = relationship(  # type: ignore[name-defined]
        "FactStats", back_populates="formulario", lazy="noload"
    )

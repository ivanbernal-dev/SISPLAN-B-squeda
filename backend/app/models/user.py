"""
app/models/user.py — Modelo SQLAlchemy para la tabla `usuarios`.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    validator = "validator"
    dependency_user = "dependency_user"


class User(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), nullable=False
    )
    dependency_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dependencias.id", ondelete="SET NULL"),
        nullable=True,
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_password_change: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
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
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relaciones ─────────────────────────────────────────────
    dependency: Mapped["Dependency | None"] = relationship(  # type: ignore[name-defined]
        "Dependency", back_populates="usuarios", lazy="selectin"
    )
    forms: Mapped[list["Form"]] = relationship(  # type: ignore[name-defined]
        "Form",
        back_populates="usuario",
        foreign_keys="Form.usuario_id",
        lazy="noload",
    )
    validated_forms: Mapped[list["Form"]] = relationship(  # type: ignore[name-defined]
        "Form",
        back_populates="validado_por",
        foreign_keys="Form.validado_por_id",
        lazy="noload",
    )
    created_templates: Mapped[list["Template"]] = relationship(  # type: ignore[name-defined]
        "Template", back_populates="created_by", lazy="noload"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # type: ignore[name-defined]
        "AuditLog", back_populates="usuario", lazy="noload"
    )

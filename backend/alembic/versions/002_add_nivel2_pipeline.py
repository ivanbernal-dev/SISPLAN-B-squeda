"""add_nivel2_pipeline

Revision ID: 002_add_nivel2_pipeline
Revises:
Create Date: 2026-03-25

Changes:
- Creates indicadores_nivel2 table
- Adds codigo and indicador_nivel2_id FK to templates
- Adds cargado_via_excel to formularios_respondidos
- Creates pipeline_definiciones table
- Creates pipeline_ejecuciones table
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_add_nivel2_pipeline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. indicadores_nivel2 ────────────────────────────────────────────────
    op.create_table(
        "indicadores_nivel2",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("indicador_nivel1_id", sa.Integer(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(
            ["indicador_nivel1_id"],
            ["indicadores_nivel1.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── 2. templates — add codigo + indicador_nivel2_id ──────────────────────
    op.add_column(
        "templates",
        sa.Column("codigo", sa.String(length=100), nullable=True),
    )
    op.create_unique_constraint("uq_templates_codigo", "templates", ["codigo"])

    op.add_column(
        "templates",
        sa.Column("indicador_nivel2_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_templates_indicador_nivel2",
        "templates",
        "indicadores_nivel2",
        ["indicador_nivel2_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── 3. formularios_respondidos — add cargado_via_excel ───────────────────
    op.add_column(
        "formularios_respondidos",
        sa.Column(
            "cargado_via_excel",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )

    # ── 4. pipeline_definiciones ─────────────────────────────────────────────
    op.create_table(
        "pipeline_definiciones",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=uuid.uuid4,
        ),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column(
            "grafo",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default='{"nodes": [], "edges": []}',
        ),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_by_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["usuarios.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── 5. pipeline_ejecuciones ───────────────────────────────────────────────
    op.create_table(
        "pipeline_ejecuciones",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=uuid.uuid4,
        ),
        sa.Column("pipeline_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "estado",
            sa.String(length=20),
            nullable=False,
            server_default="running",
        ),
        sa.Column("log_debug", sa.Text(), nullable=True),
        sa.Column(
            "resultado",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "iniciado_en",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("terminado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "disparado_por",
            sa.String(length=50),
            nullable=False,
            server_default="manual",
        ),
        sa.ForeignKeyConstraint(
            ["pipeline_id"],
            ["pipeline_definiciones.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("pipeline_ejecuciones")
    op.drop_table("pipeline_definiciones")

    op.drop_column("formularios_respondidos", "cargado_via_excel")

    op.drop_constraint("fk_templates_indicador_nivel2", "templates", type_="foreignkey")
    op.drop_column("templates", "indicador_nivel2_id")
    op.drop_constraint("uq_templates_codigo", "templates", type_="unique")
    op.drop_column("templates", "codigo")

    op.drop_table("indicadores_nivel2")

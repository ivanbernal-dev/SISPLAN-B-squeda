"""
alembic/env.py — Entorno de migraciones async para UBPD.

Uso:
    alembic revision --autogenerate -m "descripcion"
    alembic upgrade head
    alembic downgrade -1
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── Importar config de la app ────────────────────────────────────────────────
# Asegurarse de que los modelos están registrados en Base.metadata
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import Base

# Importar todos los modelos para que Alembic los detecte
from app.models import (  # noqa: F401
    audit_log,
    dependency,
    fact_stats,
    file,
    form,
    indicator,
    indicador_nivel2,
    pipeline_definicion,
    pipeline_ejecucion,
    pipeline_run,
    template,
    user,
)

# ── Config de Alembic ─────────────────────────────────────────────────────────
config = context.config

# Inyectar DATABASE_URL desde settings (evita hardcodear en alembic.ini)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configurar logging desde alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata objetivo para autogenerate
target_metadata = Base.metadata


# ── Modo offline (sin conexión real a la BD) ──────────────────────────────────
def run_migrations_offline() -> None:
    """
    Genera SQL sin conectarse a la base de datos.
    Útil para revisar el SQL antes de aplicarlo.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ── Modo online (con conexión async) ─────────────────────────────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Ejecuta migraciones usando un engine async."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

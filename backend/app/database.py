"""
app/database.py — Configuración de la base de datos async con SQLAlchemy + asyncpg
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# ── Engine async ──────────────────────────────────────────────────────────────
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.APP_ENV == "development"),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ── Base declarativa ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Dependencia FastAPI ───────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Inyecta una sesión de base de datos en cada request y la cierra al terminar."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Inicialización de tablas ──────────────────────────────────────────────────
async def init_db() -> None:
    """Crea todas las tablas si no existen (para desarrollo / primer arranque)."""
    # Importar todos los modelos para que Base los registre
    from app.models import (  # noqa: F401
        audit_log,
        bi_data,
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

    async with engine.begin() as conn:
        # checkfirst=True evita recrear tablas existentes.
        # Los ENUM types de PostgreSQL pueden causar IntegrityError si ya existen
        # (SQLAlchemy no tiene IF NOT EXISTS para tipos). Se captura y se ignora.
        try:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        except Exception as exc:
            err = str(exc)
            if "already exists" in err or "UniqueViolation" in err:
                # Tipos enum ya presentes — la BD está inicializada, continuar
                pass
            else:
                raise

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
        dependency,
        fact_stats,
        file,
        form,
        indicator,
        pipeline_run,
        template,
        user,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

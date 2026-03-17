"""
tests/conftest.py — Fixtures compartidos para toda la suite de pruebas.

Usa SQLite en memoria con aiosqlite para pruebas unitarias e integración
sin necesidad de PostgreSQL ni otros servicios externos.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.user import User, UserRole
from app.models.dependency import Dependency
from app.models.indicator import Indicator, FormulaTipo
from app.models.template import Template
from app.models.form import Form, FormStatus
from app.models.fact_stats import FactStats
from app.services.auth_service import hash_password, create_access_token, build_token_payload
from app.config import settings

# ── SQLite en memoria para tests ──────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """Motor SQLite compartido para toda la sesión de tests."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture(scope="session")
async def create_tables(engine):
    """Crea las tablas una vez por sesión."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(engine, create_tables) -> AsyncGenerator[AsyncSession, None]:
    """Sesión de base de datos por test con rollback automático."""
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session
        await session.rollback()


# ── Fixtures de objetos de dominio ────────────────────────────────────────────

@pytest.fixture
def admin_user_data():
    return {
        "id": uuid.uuid4(),
        "username": "admin_test",
        "nombre_completo": "Administrador Test",
        "email": "admin@test.com",
        "role": UserRole.admin,
        "password_hash": hash_password("Admin123!"),
        "activo": True,
        "requires_password_change": False,
        "dependency_id": None,
    }


@pytest.fixture
def validator_user_data():
    return {
        "id": uuid.uuid4(),
        "username": "validator_test",
        "nombre_completo": "Validador Test",
        "email": "validator@test.com",
        "role": UserRole.validator,
        "password_hash": hash_password("Valid123!"),
        "activo": True,
        "requires_password_change": False,
        "dependency_id": None,
    }


@pytest.fixture
def dependency_obj():
    dep = MagicMock()
    dep.id = uuid.uuid4()
    dep.nombre = "Dependencia Test"
    dep.activo = True
    return dep


@pytest.fixture
def dependency_user_data(dependency_obj):
    return {
        "id": uuid.uuid4(),
        "username": "dep_user_test",
        "nombre_completo": "Usuario Dependencia Test",
        "email": "dep@test.com",
        "role": UserRole.dependency_user,
        "password_hash": hash_password("DepUser123!"),
        "activo": True,
        "requires_password_change": False,
        "dependency_id": dependency_obj.id,
    }


@pytest.fixture
def mock_admin_user(admin_user_data):
    user = MagicMock(spec=User)
    for k, v in admin_user_data.items():
        setattr(user, k, v)
    return user


@pytest.fixture
def mock_validator_user(validator_user_data):
    user = MagicMock(spec=User)
    for k, v in validator_user_data.items():
        setattr(user, k, v)
    return user


@pytest.fixture
def mock_dependency_user(dependency_user_data, dependency_obj):
    user = MagicMock(spec=User)
    for k, v in dependency_user_data.items():
        setattr(user, k, v)
    user.dependency = dependency_obj
    return user


@pytest.fixture
def admin_token(mock_admin_user):
    payload = build_token_payload(mock_admin_user)
    return create_access_token(payload)


@pytest.fixture
def validator_token(mock_validator_user):
    payload = build_token_payload(mock_validator_user)
    return create_access_token(payload)


@pytest.fixture
def dependency_token(mock_dependency_user):
    payload = build_token_payload(mock_dependency_user)
    return create_access_token(payload)


# ── Fixture: Indicadores de prueba ────────────────────────────────────────────

@pytest.fixture
def mock_indicator():
    ind = MagicMock(spec=Indicator)
    ind.id = 1
    ind.nombre = "Indicador Test"
    ind.formula_tipo = FormulaTipo.promedio_simple
    ind.peso = 1.0
    ind.activo = True
    return ind


@pytest.fixture
def mock_fact_stats():
    """Genera lista de FactStats mockeados con valores de completitud variables."""
    stats = []
    for completitud in [80.0, 60.0, 100.0, 40.0, 75.0]:
        fs = MagicMock()
        fs.completitud = completitud
        stats.append(fs)
    return stats


# ── FastAPI TestClient ────────────────────────────────────────────────────────

@pytest.fixture
def app_with_overrides(mock_admin_user, mock_validator_user, mock_dependency_user):
    """
    Crea la app FastAPI con overrides de dependencias para tests de integración.
    Devuelve la app y un dict con las funciones override disponibles.
    """
    from app.main import app
    from app.dependencies import get_current_user, get_admin_user, get_validator_user, get_dependency_user
    from app.database import get_db

    # Override DB
    async def override_get_db():
        yield AsyncMock()

    return app, {
        "get_db": override_get_db,
        "admin": mock_admin_user,
        "validator": mock_validator_user,
        "dep_user": mock_dependency_user,
    }

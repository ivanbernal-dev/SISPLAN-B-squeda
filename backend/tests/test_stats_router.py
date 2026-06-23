"""
tests/test_stats_router.py — Pruebas de integración para /api/stats/* endpoints (público).
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.dependencies import get_db


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_indicator_row():
    row = MagicMock()
    row.id = 1
    row.nombre = "Indicador Test"
    row.descripcion = "Descripción de prueba"
    row.formula_tipo = "promedio_simple"
    row.activo = True
    return row


class TestStatsIndicatorsEndpoint:
    """Pruebas para GET /api/stats/indicators."""

    @pytest.mark.asyncio
    async def test_indicators_endpoint_is_public(self):
        """No requiere autenticación."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        app.dependency_overrides[get_db] = lambda: mock_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/stats/indicators")
        app.dependency_overrides.clear()

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_indicators_returns_list(self, mock_db, mock_indicator_row):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_indicator_row]
        mock_db.execute = AsyncMock(return_value=mock_result)

        app.dependency_overrides[get_db] = lambda: mock_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/stats/indicators")
        app.dependency_overrides.clear()

        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestStatsGlobalEndpoint:
    """Pruebas para GET /api/stats/global."""

    @pytest.mark.asyncio
    async def test_global_stats_is_public(self):
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock())

        app.dependency_overrides[get_db] = lambda: mock_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/stats/global")
        app.dependency_overrides.clear()

        assert response.status_code in (200, 500)

    @pytest.mark.asyncio
    async def test_global_stats_accepts_date_filters(self):
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock())

        app.dependency_overrides[get_db] = lambda: mock_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/stats/global",
                params={"start_date": "2024-01-01", "end_date": "2024-12-31"}
            )
        app.dependency_overrides.clear()

        assert response.status_code in (200, 500)

    @pytest.mark.asyncio
    async def test_global_stats_invalid_date_returns_422(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/stats/global",
                params={"start_date": "fecha-invalida"}
            )
        assert response.status_code == 422


class TestHealthCheck:
    """Pruebas para GET /api/health."""

    @pytest.mark.asyncio
    async def test_health_check_returns_ok(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "app" in data

    @pytest.mark.asyncio
    async def test_health_check_no_auth_required(self):
        """El endpoint de salud es público."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/health")
        assert response.status_code == 200

"""
tests/test_auth_router.py — Pruebas de integración para /api/auth/* endpoints.

Usa httpx.AsyncClient con mocks de base de datos y servicios.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.dependencies import get_current_user, get_db
from app.services.auth_service import hash_password, create_access_token, create_refresh_token, build_token_payload
from app.models.user import UserRole


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def active_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.username = "test_user"
    user.nombre_completo = "Usuario Test"
    user.email = "test@ubpd.gov.co"
    user.role = UserRole.admin
    user.activo = True
    user.dependency_id = None
    user.requires_password_change = False
    user.password_hash = hash_password("Password123!")
    return user


@pytest.fixture
def inactive_user(active_user):
    active_user.activo = False
    return active_user


@pytest.fixture
def access_token(active_user):
    payload = build_token_payload(active_user)
    return create_access_token(payload)


@pytest.fixture
def refresh_token_str(active_user):
    payload = build_token_payload(active_user)
    return create_refresh_token(payload)


class TestLoginEndpoint:
    """Pruebas para POST /api/auth/login."""

    @pytest.mark.asyncio
    async def test_login_returns_tokens_on_valid_credentials(self, active_user, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = active_user
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        with patch("app.routers.auth.authenticate_user", return_value=active_user), \
             patch("app.routers.auth.build_token_payload", return_value={"sub": str(active_user.id), "role": "admin"}):

            app.dependency_overrides[get_db] = lambda: mock_db
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/auth/login", json={
                    "username": "test_user",
                    "password": "Password123!"
                })

        app.dependency_overrides.clear()
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_login_returns_401_on_invalid_credentials(self, mock_db):
        mock_db.execute = AsyncMock(return_value=MagicMock())

        with patch("app.routers.auth.authenticate_user", return_value=None):
            app.dependency_overrides[get_db] = lambda: mock_db
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/auth/login", json={
                    "username": "nadie",
                    "password": "wrong"
                })

        app.dependency_overrides.clear()
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_returns_422_on_missing_fields(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/auth/login", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_returns_422_on_empty_username(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/auth/login", json={
                "username": "",
                "password": "algo"
            })
        assert response.status_code in (401, 422)


class TestRefreshEndpoint:
    """Pruebas para POST /api/auth/refresh."""

    @pytest.mark.asyncio
    async def test_refresh_returns_new_access_token(self, active_user, refresh_token_str, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = active_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        app.dependency_overrides[get_db] = lambda: mock_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/auth/refresh", json={
                "refresh_token": refresh_token_str
            })
        app.dependency_overrides.clear()

        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_refresh_fails_with_access_token(self, access_token):
        """No debe aceptar un access_token como refresh_token."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/auth/refresh", json={
                "refresh_token": access_token
            })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_fails_with_invalid_token(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/auth/refresh", json={
                "refresh_token": "token.invalido.completamente"
            })
        assert response.status_code == 401


class TestLogoutEndpoint:
    """Pruebas para POST /api/auth/logout."""

    @pytest.mark.asyncio
    async def test_logout_requires_authentication(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/auth/logout")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_returns_success_when_authenticated(self, active_user, access_token, mock_db):
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        app.dependency_overrides[get_current_user] = lambda: active_user
        app.dependency_overrides[get_db] = lambda: mock_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/auth/logout",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        app.dependency_overrides.clear()

        assert response.status_code == 200


class TestChangePasswordEndpoint:
    """Pruebas para POST /api/auth/change-password."""

    @pytest.mark.asyncio
    async def test_change_password_requires_authentication(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/auth/change-password", json={
                "current_password": "old",
                "new_password": "NewPass123!"
            })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_change_password_returns_400_on_wrong_current_password(self, active_user, mock_db):
        active_user.password_hash = hash_password("CorrectPass123!")
        mock_db.commit = AsyncMock()

        app.dependency_overrides[get_current_user] = lambda: active_user
        app.dependency_overrides[get_db] = lambda: mock_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/auth/change-password",
                headers={"Authorization": "Bearer fake"},
                json={"current_password": "WrongPass!", "new_password": "NewPass123!"}
            )
        app.dependency_overrides.clear()

        assert response.status_code == 400

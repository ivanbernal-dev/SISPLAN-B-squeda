"""
tests/test_dependencies.py — Pruebas unitarias para app/dependencies.py
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.dependencies import get_current_user, require_role, get_client_ip
from app.models.user import UserRole
from app.services.auth_service import create_access_token, hash_password, build_token_payload


@pytest.fixture
def active_admin():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.username = "admin"
    user.role = UserRole.admin
    user.activo = True
    user.dependency_id = None
    return user


@pytest.fixture
def active_validator():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.username = "validator"
    user.role = UserRole.validator
    user.activo = True
    user.dependency_id = None
    return user


@pytest.fixture
def inactive_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.username = "inactive"
    user.role = UserRole.dependency_user
    user.activo = False
    user.dependency_id = uuid.uuid4()
    return user


class TestGetCurrentUser:
    """Pruebas para la dependencia get_current_user."""

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self, active_admin):
        payload = build_token_payload(active_admin)
        token = create_access_token(payload)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = active_admin
        mock_db.execute = AsyncMock(return_value=mock_result)

        user = await get_current_user(credentials=credentials, db=mock_db)
        assert user is active_admin

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token.invalido")
        mock_db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials, db=mock_db)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_inactive_user_raises_401(self, inactive_user):
        payload = build_token_payload(inactive_user)
        token = create_access_token(payload)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inactive_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials, db=mock_db)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_user_not_found_raises_401(self, active_admin):
        payload = build_token_payload(active_admin)
        token = create_access_token(payload)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials, db=mock_db)
        assert exc_info.value.status_code == 401


class TestRequireRole:
    """Pruebas para el factory require_role."""

    @pytest.mark.asyncio
    async def test_user_with_correct_role_passes(self, active_admin):
        dependency = require_role(UserRole.admin)
        user = await dependency(current_user=active_admin)
        assert user is active_admin

    @pytest.mark.asyncio
    async def test_user_with_wrong_role_raises_403(self, active_validator):
        dependency = require_role(UserRole.admin)
        with pytest.raises(HTTPException) as exc_info:
            await dependency(current_user=active_validator)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_multiple_roles_any_passes(self, active_admin):
        dependency = require_role(UserRole.admin, UserRole.validator)
        user = await dependency(current_user=active_admin)
        assert user is active_admin

    @pytest.mark.asyncio
    async def test_multiple_roles_second_role_passes(self, active_validator):
        dependency = require_role(UserRole.admin, UserRole.validator)
        user = await dependency(current_user=active_validator)
        assert user is active_validator


class TestGetClientIp:
    """Pruebas para get_client_ip."""

    def test_extracts_ip_from_forwarded_for_header(self):
        request = MagicMock()
        request.headers = {"X-Forwarded-For": "192.168.1.50, 10.0.0.1"}
        request.client.host = "127.0.0.1"
        ip = get_client_ip(request)
        assert ip == "192.168.1.50"

    def test_falls_back_to_client_host(self):
        request = MagicMock()
        request.headers = {}
        request.client.host = "192.168.1.100"
        ip = get_client_ip(request)
        assert ip == "192.168.1.100"

    def test_returns_unknown_if_no_client(self):
        request = MagicMock()
        request.headers = {}
        request.client = None
        ip = get_client_ip(request)
        assert ip is not None

"""
tests/test_auth_service.py — Pruebas unitarias para app/services/auth_service.py
"""
import pytest
import time
from unittest.mock import MagicMock, patch
from jose import jwt, JWTError

from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    build_token_payload,
    authenticate_user,
)
from app.models.user import UserRole
from app.config import settings


class TestPasswordHashing:
    """Pruebas para funciones de hash y verificación de contraseñas."""

    def test_hash_password_returns_string(self):
        hashed = hash_password("mi_contraseña_segura")
        assert isinstance(hashed, str)

    def test_hash_password_is_not_plaintext(self):
        plain = "mi_contraseña_segura"
        hashed = hash_password(plain)
        assert hashed != plain

    def test_hash_password_different_for_same_input(self):
        """bcrypt genera salt distinto cada vez."""
        h1 = hash_password("misma_contraseña")
        h2 = hash_password("misma_contraseña")
        assert h1 != h2

    def test_verify_password_correct(self):
        plain = "contraseña_correcta"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("contraseña_correcta")
        assert verify_password("contraseña_incorrecta", hashed) is False

    def test_verify_password_empty_string(self):
        hashed = hash_password("alguna_contraseña")
        assert verify_password("", hashed) is False

    def test_hash_empty_string(self):
        """Incluso una cadena vacía debe generar un hash válido."""
        hashed = hash_password("")
        assert verify_password("", hashed) is True


class TestJWTTokens:
    """Pruebas para creación y decodificación de tokens JWT."""

    def test_create_access_token_returns_string(self):
        token = create_access_token({"sub": "usuario_test", "role": "admin"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_has_correct_type(self):
        token = create_access_token({"sub": "usuario_test"})
        decoded = decode_token(token)
        assert decoded["type"] == "access"

    def test_create_refresh_token_has_correct_type(self):
        token = create_refresh_token({"sub": "usuario_test"})
        decoded = decode_token(token)
        assert decoded["type"] == "refresh"

    def test_decode_token_contains_original_data(self):
        data = {"sub": "usuario_abc", "role": "validator", "dep": "dep123"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert decoded["sub"] == "usuario_abc"
        assert decoded["role"] == "validator"
        assert decoded["dep"] == "dep123"

    def test_decode_invalid_token_raises_error(self):
        with pytest.raises(JWTError):
            decode_token("token.invalido.aqui")

    def test_decode_tampered_token_raises_error(self):
        token = create_access_token({"sub": "usuario_test"})
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            decode_token(tampered)

    def test_access_token_expires_before_refresh_token(self):
        access = create_access_token({"sub": "u"})
        refresh = create_refresh_token({"sub": "u"})
        access_decoded = decode_token(access)
        refresh_decoded = decode_token(refresh)
        assert access_decoded["exp"] < refresh_decoded["exp"]

    def test_create_access_token_custom_expiry(self):
        from datetime import timedelta
        short = create_access_token({"sub": "u"}, expires_delta=timedelta(seconds=5))
        decoded = decode_token(short)
        # expiry should be ~5 seconds from now
        margin = 10
        assert abs(decoded["exp"] - (time.time() + 5)) < margin


class TestBuildTokenPayload:
    """Pruebas para la función build_token_payload."""

    def test_payload_contains_required_fields(self, mock_admin_user):
        payload = build_token_payload(mock_admin_user)
        assert "sub" in payload
        assert "role" in payload

    def test_payload_sub_is_user_id_string(self, mock_admin_user):
        payload = build_token_payload(mock_admin_user)
        assert payload["sub"] == str(mock_admin_user.id)

    def test_payload_role_matches_user(self, mock_admin_user):
        payload = build_token_payload(mock_admin_user)
        assert payload["role"] == UserRole.admin

    def test_payload_dependency_user_includes_dep_id(self, mock_dependency_user):
        payload = build_token_payload(mock_dependency_user)
        assert "dependency_id" in payload or "dep" in payload

    def test_payload_admin_no_dependency(self, mock_admin_user):
        mock_admin_user.dependency_id = None
        payload = build_token_payload(mock_admin_user)
        dep = payload.get("dependency_id") or payload.get("dep")
        assert dep is None


class TestAuthenticateUser:
    """Pruebas para la función authenticate_user (async)."""

    @pytest.mark.asyncio
    async def test_authenticate_returns_user_on_valid_credentials(self, mock_admin_user):
        from unittest.mock import AsyncMock, patch
        db = AsyncMock()

        with patch("app.services.auth_service.verify_password", return_value=True):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_admin_user
            db.execute = AsyncMock(return_value=mock_result)

            result = await authenticate_user(db, "admin_test", "Admin123!")
            assert result is mock_admin_user

    @pytest.mark.asyncio
    async def test_authenticate_returns_none_on_wrong_password(self, mock_admin_user):
        from unittest.mock import AsyncMock, patch
        db = AsyncMock()

        with patch("app.services.auth_service.verify_password", return_value=False):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_admin_user
            db.execute = AsyncMock(return_value=mock_result)

            result = await authenticate_user(db, "admin_test", "wrong_password")
            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_returns_none_if_user_not_found(self):
        from unittest.mock import AsyncMock
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        result = await authenticate_user(db, "usuario_inexistente", "cualquier_pass")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_returns_none_if_user_inactive(self, mock_admin_user):
        from unittest.mock import AsyncMock, patch
        mock_admin_user.activo = False
        db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_admin_user
        db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.auth_service.verify_password", return_value=True):
            result = await authenticate_user(db, "admin_test", "Admin123!")
            assert result is None

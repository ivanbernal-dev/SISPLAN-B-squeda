"""
app/config.py — Configuración global mediante pydantic-settings
Lee variables de entorno desde .env o variables del sistema.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Aplicación ────────────────────────────────────────────
    APP_NAME: str = "UBPD"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "production"  # development | production

    # ── Base de Datos ──────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://ubpd_user:password@localhost:5432/ubpd_db"

    # ── JWT / Seguridad ────────────────────────────────────────
    SECRET_KEY: str = "changeme-in-production-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Redis ──────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── MinIO ──────────────────────────────────────────────────
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ROOT_USER: str = "ubpd_minio_admin"
    MINIO_ROOT_PASSWORD: str = "password"
    MINIO_BUCKET_NAME: str = "ubpd-formularios"
    MINIO_USE_SSL: bool = False
    MINIO_PRESIGNED_URL_EXPIRY: int = 3600  # segundos

    # ── Archivos ───────────────────────────────────────────────
    MAX_UPLOAD_MB: int = 50
    ALLOWED_MIME_TYPES: str = "application/pdf,image/jpeg,image/png,application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    # ── CORS ───────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── Admin inicial ──────────────────────────────────────────
    INITIAL_ADMIN_USERNAME: str = "admin"
    INITIAL_ADMIN_PASSWORD: str = "Admin@UBPD2024"
    INITIAL_ADMIN_EMAIL: str = "admin@ubpd.gov.co"
    INITIAL_ADMIN_NOMBRE: str = "Administrador UBPD"

    # ── Celery / Pipeline ──────────────────────────────────────
    STATS_RECALC_INTERVAL_SECONDS: int = 600  # 10 minutos

    # ── Propiedades derivadas ──────────────────────────────────
    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_mime_types_list(self) -> List[str]:
        return [m.strip() for m in self.ALLOWED_MIME_TYPES.split(",") if m.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024


settings = Settings()

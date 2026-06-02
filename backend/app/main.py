"""
app/main.py — Punto de entrada de la aplicación FastAPI UBPD.

Lifespan:
1. Inicializa tablas en la base de datos.
2. Crea el bucket MinIO si no existe.
3. Crea el usuario administrador inicial si no existe ningún admin.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging_config import setup_logging

# Configurar logging antes de cualquier otra cosa
setup_logging(app_env=settings.APP_ENV, log_dir=settings.LOG_DIR)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Tareas de inicio y apagado."""
    logger.info("Iniciando UBPD Backend v%s [%s]", settings.APP_VERSION, settings.APP_ENV)

    # 1. Inicializar base de datos
    from app.database import init_db
    await init_db()
    logger.info("Base de datos inicializada.")

    # 2. Inicializar MinIO
    from app.services.minio_service import init_minio
    try:
        init_minio()
        logger.info("MinIO inicializado — bucket: %s", settings.MINIO_BUCKET_NAME)
    except Exception as exc:
        logger.warning("No se pudo conectar a MinIO: %s", exc)

    # 3. Crear admin inicial si no existe
    await _create_initial_admin()

    # 4. Crear indicadores de la Línea Estratégica 1 si no existen
    await _seed_indicators()

    # 5. Sembrar script PAI 2026 como activo si pipeline_scripts está vacía
    await _seed_pai_pipeline()

    yield

    logger.info("UBPD Backend apagándose.")


async def _create_initial_admin() -> None:
    """Crea el usuario administrador inicial si no existe ningún admin activo."""
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.role == UserRole.admin, User.activo == True).limit(1)
        )
        existing_admin = result.scalar_one_or_none()
        if existing_admin:
            logger.debug("Admin ya existe: %s", existing_admin.username)
            return

        admin = User(
            username=settings.INITIAL_ADMIN_USERNAME,
            nombre_completo=settings.INITIAL_ADMIN_NOMBRE,
            email=settings.INITIAL_ADMIN_EMAIL,
            role=UserRole.admin,
            password_hash=hash_password(settings.INITIAL_ADMIN_PASSWORD),
            requires_password_change=False,
        )
        try:
            db.add(admin)
            await db.commit()
            logger.info(
                "Usuario administrador inicial creado: %s",
                settings.INITIAL_ADMIN_USERNAME,
            )
        except Exception:
            await db.rollback()
            logger.debug("Admin ya existía (creado por otro proceso al mismo tiempo).")


async def _seed_indicators() -> None:
    """Crea los indicadores de la Línea Estratégica No. 1 si no existen."""
    from sqlalchemy import select, func
    from app.database import AsyncSessionLocal
    from app.models.indicator import Indicator, FormulaTipo

    INDICADORES_L1 = [
        {"nombre": "Indicador 1 — Hallazgos e Identificaciones", "descripcion": "Mide la completitud de los registros de hallazgos e identificaciones humanitarias.", "formula_tipo": FormulaTipo.promedio_simple, "peso": 1.0},
        {"nombre": "Indicador 2 — Diligenciamiento de Procesos Extrajudiciales", "descripcion": "Mide la completitud de los procesos de búsqueda extrajudicial.", "formula_tipo": FormulaTipo.promedio_ponderado, "peso": 1.0},
        {"nombre": "Indicador 3 — Entrega Digna", "descripcion": "Mide la completitud de los registros de entrega digna a familias.", "formula_tipo": FormulaTipo.promedio_simple, "peso": 1.0},
    ]

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(func.count()).select_from(Indicator))
        count = result.scalar_one()
        if count > 0:
            logger.debug("Indicadores ya existen (%d).", count)
            return

        for data in INDICADORES_L1:
            ind = Indicator(**data)
            db.add(ind)
        await db.commit()
        logger.info("Indicadores de la Línea Estratégica 1 creados (%d).", len(INDICADORES_L1))


# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=f"{settings.APP_NAME} — Sistema de Gestión de Formularios",
    description=(
        "Backend para la Unidad de Búsqueda de Personas Dadas por Desaparecidas (UBPD). "
        "Gestiona formularios de la Línea Estratégica No. 1, validaciones y estadísticas."
    ),
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _seed_pai_pipeline() -> None:
    """Si la tabla pipeline_scripts está vacía, inserta el script PAI 2026
    (leído de app/seeds/pipeline_pai_default.py) como activo. Idempotente:
    si ya hay cualquier script en la tabla NO toca nada."""
    from pathlib import Path
    from sqlalchemy import select, func
    from app.database import AsyncSessionLocal
    from app.models.kpi import PipelineScript

    async with AsyncSessionLocal() as db:
        n = await db.scalar(select(func.count(PipelineScript.id)))
        if (n or 0) > 0:
            logger.debug("pipeline_scripts ya tiene %d fila(s); no se siembra.", n)
            return

        seed_path = Path(__file__).parent / "seeds" / "pipeline_pai_default.py"
        if not seed_path.exists():
            logger.warning(
                "No se sembró el pipeline PAI: no existe %s", seed_path,
            )
            return
        try:
            codigo = seed_path.read_text(encoding="utf-8")
            # Validación rápida: que compile como Python
            compile(codigo, str(seed_path), "exec")
        except (OSError, SyntaxError) as exc:
            logger.warning("No se sembró el pipeline PAI: %s", exc)
            return

        script = PipelineScript(
            codigo=codigo,
            nombre="Pipeline PAI 2026 (seed)",
            activo=True,
        )
        db.add(script)
        try:
            await db.commit()
            logger.info(
                "Pipeline PAI 2026 sembrado como activo (%d chars) — listo para Ejecutar.",
                len(codigo),
            )
        except Exception as exc:
            await db.rollback()
            logger.warning("Falló sembrar pipeline PAI: %s", exc)


# ── Routers ───────────────────────────────────────────────────────────────────
from app.routers import auth, admin, templates, forms, files, validation, stats
from app.routers import indicadores, pipeline_definitions, forms_excel, admin_backup
from app.routers.script_pipeline import admin_router as script_admin_router
from app.routers.script_pipeline import public_router as script_public_router
from app.routers import test_data as test_data_router
from app.routers.bi_dashboard import admin_router as bi_admin_router
from app.routers.bi_dashboard import public_router as bi_public_router

app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(templates.router, prefix="/api")
app.include_router(forms.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(validation.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(indicadores.router, prefix="/api")
app.include_router(pipeline_definitions.router, prefix="/api")
app.include_router(forms_excel.router, prefix="/api")
app.include_router(admin_backup.router, prefix="/api")
app.include_router(script_admin_router, prefix="/api")
app.include_router(script_public_router, prefix="/api")
app.include_router(test_data_router.router, prefix="/api")
app.include_router(bi_admin_router, prefix="/api")
app.include_router(bi_public_router, prefix="/api")


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Sistema"], summary="Estado del servicio")
async def health_check() -> dict:
    """Retorna el estado del servicio y la versión."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
    }


# ── Manejo global de errores ──────────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Formatea los errores de validación Pydantic de forma legible."""
    errors = []
    for error in exc.errors():
        loc = " → ".join(str(x) for x in error.get("loc", []))
        errors.append({"campo": loc, "mensaje": error.get("msg", "")})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Error de validación", "errors": errors},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Captura errores no controlados y los registra."""
    logger.error("Error no controlado en %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor"},
    )

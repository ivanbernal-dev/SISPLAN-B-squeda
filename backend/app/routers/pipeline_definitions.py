"""
app/routers/pipeline_definitions.py — Endpoints para gestión y ejecución de pipelines visuales.
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_admin_user, get_any_authenticated
from app.models.pipeline_definicion import PipelineDefinicion
from app.models.pipeline_ejecucion import PipelineEjecucion
from app.models.user import User

router = APIRouter(prefix="/pipeline-definitions", tags=["Pipelines"])
logger = logging.getLogger(__name__)


# ── Schemas ───────────────────────────────────────────────────────────────────

class PipelineCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    grafo: dict = {"nodes": [], "edges": []}
    activo: bool = True


class PipelineUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    grafo: Optional[dict] = None
    activo: Optional[bool] = None


class PipelineResponse(BaseModel):
    id: str
    nombre: str
    descripcion: Optional[str]
    grafo: dict
    activo: bool
    created_by_id: Optional[str]
    created_by_nombre: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class EjecucionResponse(BaseModel):
    id: str
    pipeline_id: str
    estado: str
    log_debug: Optional[str]
    resultado: Optional[dict]
    iniciado_en: str
    terminado_en: Optional[str]
    disparado_por: str


def _pipeline_to_response(p: PipelineDefinicion) -> PipelineResponse:
    return PipelineResponse(
        id=str(p.id),
        nombre=p.nombre,
        descripcion=p.descripcion,
        grafo=p.grafo,
        activo=p.activo,
        created_by_id=str(p.created_by_id) if p.created_by_id else None,
        created_by_nombre=p.created_by.nombre_completo if p.created_by else None,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


def _ejecucion_to_response(e: PipelineEjecucion) -> EjecucionResponse:
    return EjecucionResponse(
        id=str(e.id),
        pipeline_id=str(e.pipeline_id),
        estado=e.estado,
        log_debug=e.log_debug,
        resultado=e.resultado,
        iniciado_en=e.iniciado_en.isoformat(),
        terminado_en=e.terminado_en.isoformat() if e.terminado_en else None,
        disparado_por=e.disparado_por,
    )


# ── List & CRUD ───────────────────────────────────────────────────────────────

@router.get("", response_model=list[PipelineResponse])
async def list_pipelines(
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> list[PipelineResponse]:
    """Lista todas las definiciones de pipeline."""
    result = await db.execute(
        select(PipelineDefinicion).order_by(PipelineDefinicion.created_at.desc())
    )
    pipelines = result.scalars().all()
    return [_pipeline_to_response(p) for p in pipelines]


@router.post("", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    body: PipelineCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> PipelineResponse:
    """Crea una nueva definición de pipeline."""
    pipeline = PipelineDefinicion(
        nombre=body.nombre,
        descripcion=body.descripcion,
        grafo=body.grafo,
        activo=body.activo,
        created_by_id=current_user.id,
    )
    db.add(pipeline)
    await db.flush()
    await db.commit()
    await db.refresh(pipeline)
    return _pipeline_to_response(pipeline)


@router.get("/export-all")
async def export_all_pipelines(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Exporta todos los pipelines como JSON."""
    result = await db.execute(select(PipelineDefinicion))
    pipelines = result.scalars().all()
    data = [
        {
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "grafo": p.grafo,
            "activo": p.activo,
        }
        for p in pipelines
    ]
    return Response(
        content=json.dumps(data, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=pipelines_export.json"},
    )


@router.post("/import", response_model=list[PipelineResponse], status_code=status.HTTP_201_CREATED)
async def import_pipelines(
    body: list[PipelineCreate],
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[PipelineResponse]:
    """Importa pipelines desde JSON. Crea nuevos registros (no actualiza existentes)."""
    created = []
    for item in body:
        pipeline = PipelineDefinicion(
            nombre=item.nombre,
            descripcion=item.descripcion,
            grafo=item.grafo,
            activo=item.activo,
            created_by_id=current_user.id,
        )
        db.add(pipeline)
        await db.flush()
        created.append(pipeline)
    await db.commit()
    for p in created:
        await db.refresh(p)
    return [_pipeline_to_response(p) for p in created]


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: uuid.UUID,
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> PipelineResponse:
    """Retorna una definición de pipeline con su grafo completo."""
    result = await db.execute(
        select(PipelineDefinicion).where(PipelineDefinicion.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()
    if pipeline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline no encontrado")
    return _pipeline_to_response(pipeline)


@router.put("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: uuid.UUID,
    body: PipelineUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> PipelineResponse:
    """Actualiza una definición de pipeline."""
    result = await db.execute(
        select(PipelineDefinicion).where(PipelineDefinicion.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()
    if pipeline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline no encontrado")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(pipeline, field, value)
    pipeline.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(pipeline)
    return _pipeline_to_response(pipeline)


@router.delete("/{pipeline_id}", status_code=status.HTTP_200_OK)
async def delete_pipeline(
    pipeline_id: uuid.UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Elimina una definición de pipeline."""
    result = await db.execute(
        select(PipelineDefinicion).where(PipelineDefinicion.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()
    if pipeline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline no encontrado")

    await db.delete(pipeline)
    await db.commit()
    return {"detail": "Pipeline eliminado exitosamente"}


# ── Executions ────────────────────────────────────────────────────────────────

@router.post("/{pipeline_id}/execute", response_model=EjecucionResponse)
async def execute_pipeline_endpoint(
    pipeline_id: uuid.UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> EjecucionResponse:
    """Ejecuta un pipeline y guarda el log de ejecución."""
    result = await db.execute(
        select(PipelineDefinicion).where(PipelineDefinicion.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()
    if pipeline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline no encontrado")

    # Create execution record
    ejecucion = PipelineEjecucion(
        pipeline_id=pipeline_id,
        estado="running",
        disparado_por="manual",
    )
    db.add(ejecucion)
    await db.flush()

    from app.services.pipeline_executor import execute_pipeline
    try:
        resultado, log_str = await execute_pipeline(pipeline.grafo, db)
        ejecucion.estado = "success" if "error" not in resultado else "error"
        ejecucion.resultado = resultado
        ejecucion.log_debug = log_str
    except Exception as exc:
        logger.error("Pipeline execution failed: %s", exc, exc_info=True)
        ejecucion.estado = "error"
        ejecucion.resultado = {"error": str(exc)}
        ejecucion.log_debug = str(exc)

    ejecucion.terminado_en = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(ejecucion)
    return _ejecucion_to_response(ejecucion)


@router.get("/{pipeline_id}/executions", response_model=list[EjecucionResponse])
async def list_executions(
    pipeline_id: uuid.UUID,
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> list[EjecucionResponse]:
    """Lista el historial de ejecuciones de un pipeline."""
    result = await db.execute(
        select(PipelineEjecucion)
        .where(PipelineEjecucion.pipeline_id == pipeline_id)
        .order_by(PipelineEjecucion.iniciado_en.desc())
        .limit(50)
    )
    items = result.scalars().all()
    return [_ejecucion_to_response(e) for e in items]

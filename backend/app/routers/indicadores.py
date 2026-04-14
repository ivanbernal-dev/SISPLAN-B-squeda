"""
app/routers/indicadores.py — Gestión de indicadores KPI (conectado a kpi_resultados).
"""
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_admin_user, get_any_authenticated
from app.models.kpi import KpiResultado
from app.models.user import User

router = APIRouter(prefix="/indicadores", tags=["Indicadores"])
logger = logging.getLogger(__name__)


# ── Schemas ───────────────────────────────────────────────────────────────────

class KpiCreate(BaseModel):
    kpi_key: str
    kpi_label: str
    nivel: int                            # 1 or 2
    nivel1_key: Optional[str] = None      # Required when nivel == 2
    descripcion: Optional[str] = None
    template_id: Optional[str] = None
    activo: bool = True


class KpiUpdate(BaseModel):
    kpi_label: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None
    template_id: Optional[str] = None


class KpiResponse(BaseModel):
    id: str
    kpi_key: str
    kpi_label: str
    nivel: int
    nivel1_key: Optional[str]
    descripcion: Optional[str]
    template_id: Optional[str]
    valor: float
    activo: bool
    updated_at: Optional[str]

    model_config = {"from_attributes": True}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_response(k: KpiResultado) -> KpiResponse:
    return KpiResponse(
        id=str(k.id),
        kpi_key=k.kpi_key,
        kpi_label=k.kpi_label,
        nivel=k.nivel,
        nivel1_key=k.nivel1_key,
        descripcion=k.descripcion,
        template_id=k.template_id,
        valor=k.valor or 0.0,
        activo=k.activo if k.activo is not None else True,
        updated_at=k.updated_at.isoformat() if k.updated_at else None,
    )


async def _get_kpi(db: AsyncSession, kpi_key: str) -> KpiResultado:
    result = await db.execute(
        select(KpiResultado).where(KpiResultado.kpi_key == kpi_key)
    )
    kpi = result.scalar_one_or_none()
    if kpi is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"KPI '{kpi_key}' no encontrado")
    return kpi


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/kpis", response_model=List[KpiResponse])
async def list_kpis(
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> List[KpiResponse]:
    """Lista todos los KPI (nivel 1 y 2) con sus valores actuales."""
    result = await db.execute(
        select(KpiResultado).order_by(KpiResultado.nivel, KpiResultado.kpi_key)
    )
    return [_to_response(k) for k in result.scalars().all()]


@router.post("/kpis", response_model=KpiResponse, status_code=status.HTTP_201_CREATED)
async def create_kpi(
    body: KpiCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> KpiResponse:
    """Crea un nuevo KPI en kpi_resultados."""
    # Validate uniqueness
    existing = await db.execute(
        select(KpiResultado).where(KpiResultado.kpi_key == body.kpi_key)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Ya existe un KPI con key '{body.kpi_key}'")

    if body.nivel == 2 and not body.nivel1_key:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="nivel1_key es requerido para KPIs de nivel 2")

    kpi = KpiResultado(
        kpi_key=body.kpi_key,
        kpi_label=body.kpi_label,
        nivel=body.nivel,
        nivel1_key=body.nivel1_key,
        descripcion=body.descripcion,
        template_id=body.template_id,
        activo=body.activo,
        valor=0.0,
        updated_at=datetime.now(timezone.utc),
    )
    db.add(kpi)
    await db.commit()
    await db.refresh(kpi)
    return _to_response(kpi)


@router.patch("/kpis/{kpi_key}", response_model=KpiResponse)
async def update_kpi(
    kpi_key: str,
    body: KpiUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> KpiResponse:
    """Actualiza label, descripcion o estado activo de un KPI."""
    kpi = await _get_kpi(db, kpi_key)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(kpi, field, value)
    kpi.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(kpi)
    return _to_response(kpi)


@router.delete("/kpis/{kpi_key}", status_code=status.HTTP_200_OK)
async def delete_kpi(
    kpi_key: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Elimina permanentemente un KPI de kpi_resultados."""
    kpi = await _get_kpi(db, kpi_key)
    await db.delete(kpi)
    await db.commit()
    return {"ok": True, "detail": f"KPI '{kpi_key}' eliminado."}


# ── JSON Export / Import ──────────────────────────────────────────────────────

@router.get("/kpis/export")
async def export_kpis(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Exporta la configuración completa de KPIs como JSON."""
    result = await db.execute(
        select(KpiResultado).order_by(KpiResultado.nivel, KpiResultado.kpi_key)
    )
    kpis = result.scalars().all()
    data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "kpis": [
            {
                "kpi_key": k.kpi_key,
                "kpi_label": k.kpi_label,
                "nivel": k.nivel,
                "nivel1_key": k.nivel1_key,
                "descripcion": k.descripcion,
                "template_id": k.template_id,
                "activo": k.activo if k.activo is not None else True,
                "valor": k.valor or 0.0,
            }
            for k in kpis
        ],
    }
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f'attachment; filename="kpis_config_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}.json"'
        },
    )


@router.post("/kpis/import", status_code=status.HTTP_200_OK)
async def import_kpis(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Importa configuración de KPIs desde JSON.
    Hace upsert por kpi_key — actualiza label/descripcion/activo, no sobreescribe valor.
    """
    kpis_data = payload.get("kpis", [])
    if not isinstance(kpis_data, list):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="El JSON debe tener una clave 'kpis' con una lista.")

    created = 0
    updated = 0
    for item in kpis_data:
        key = item.get("kpi_key")
        if not key:
            continue
        existing = await db.execute(
            select(KpiResultado).where(KpiResultado.kpi_key == key)
        )
        kpi = existing.scalar_one_or_none()
        if kpi:
            # Update metadata only — preserve calculated valor
            kpi.kpi_label = item.get("kpi_label", kpi.kpi_label)
            kpi.descripcion = item.get("descripcion", kpi.descripcion)
            kpi.activo = item.get("activo", kpi.activo)
            kpi.template_id = item.get("template_id", kpi.template_id)
            kpi.updated_at = datetime.now(timezone.utc)
            updated += 1
        else:
            nivel = item.get("nivel", 1)
            new_kpi = KpiResultado(
                kpi_key=key,
                kpi_label=item.get("kpi_label", key),
                nivel=nivel,
                nivel1_key=item.get("nivel1_key"),
                descripcion=item.get("descripcion"),
                template_id=item.get("template_id"),
                activo=item.get("activo", True),
                valor=0.0,
                updated_at=datetime.now(timezone.utc),
            )
            db.add(new_kpi)
            created += 1

    await db.commit()
    return {
        "ok": True,
        "creados": created,
        "actualizados": updated,
        "mensaje": f"{created} creados, {updated} actualizados.",
    }


# ── Legacy level1/level2 endpoints (kept for backward compat) ────────────────

@router.get("/nivel1")
async def list_nivel1_legacy(
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
):
    """Legacy: redirige a kpi_resultados nivel 1."""
    result = await db.execute(
        select(KpiResultado).where(KpiResultado.nivel == 1).order_by(KpiResultado.kpi_key)
    )
    kpis = result.scalars().all()
    return [
        {
            "id": str(k.id), "nombre": k.kpi_label, "descripcion": k.descripcion,
            "formula_tipo": "pipeline", "peso": 1.0,
            "activo": k.activo if k.activo is not None else True,
            "total_nivel2": 0, "total_templates": 0,
        }
        for k in kpis
    ]


@router.get("/nivel2")
async def list_nivel2_legacy(
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
):
    """Legacy: redirige a kpi_resultados nivel 2."""
    result = await db.execute(
        select(KpiResultado).where(KpiResultado.nivel == 2).order_by(KpiResultado.kpi_key)
    )
    kpis = result.scalars().all()
    return [
        {
            "id": str(k.id), "nombre": k.kpi_label, "descripcion": k.descripcion,
            "indicador_nivel1_id": k.nivel1_key,
            "indicador_nivel1_nombre": k.nivel1_key,
            "activo": k.activo if k.activo is not None else True,
            "total_templates": 0,
        }
        for k in kpis
    ]

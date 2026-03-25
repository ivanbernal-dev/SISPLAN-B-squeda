"""
app/routers/indicadores.py — Endpoints para gestión de indicadores Nivel 1 y Nivel 2.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_admin_user, get_any_authenticated
from app.models.indicator import Indicator, FormulaTipo
from app.models.indicador_nivel2 import IndicadorNivel2
from app.models.user import User

router = APIRouter(prefix="/indicadores", tags=["Indicadores"])
logger = logging.getLogger(__name__)


# ── Schemas ───────────────────────────────────────────────────────────────────

class Nivel1Create(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    formula_tipo: FormulaTipo = FormulaTipo.promedio_simple
    peso: float = 1.0
    activo: bool = True


class Nivel1Update(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    formula_tipo: Optional[FormulaTipo] = None
    peso: Optional[float] = None
    activo: Optional[bool] = None


class Nivel1Response(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    formula_tipo: str
    peso: float
    activo: bool
    total_nivel2: int = 0
    total_templates: int = 0

    model_config = {"from_attributes": True}


class Nivel2Create(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    indicador_nivel1_id: int
    activo: bool = True


class Nivel2Update(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    indicador_nivel1_id: Optional[int] = None
    activo: Optional[bool] = None


class Nivel2Response(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    indicador_nivel1_id: int
    indicador_nivel1_nombre: Optional[str] = None
    activo: bool
    total_templates: int = 0

    model_config = {"from_attributes": True}


# ── Level 1 endpoints ─────────────────────────────────────────────────────────

@router.get("/nivel1", response_model=list[Nivel1Response])
async def list_nivel1(
    activo: Optional[bool] = None,
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> list[Nivel1Response]:
    """Lista todos los indicadores de Nivel 1."""
    query = select(Indicator)
    if activo is not None:
        query = query.where(Indicator.activo == activo)
    query = query.order_by(Indicator.id)
    result = await db.execute(query)
    indicators = result.scalars().all()

    response = []
    for ind in indicators:
        # Count nivel2 and templates
        n2_count = await db.scalar(
            select(func.count()).select_from(IndicadorNivel2).where(
                IndicadorNivel2.indicador_nivel1_id == ind.id
            )
        ) or 0
        from app.models.template import Template
        t_count = await db.scalar(
            select(func.count()).select_from(Template).where(
                Template.indicador_nivel1_id == ind.id
            )
        ) or 0
        response.append(Nivel1Response(
            id=ind.id,
            nombre=ind.nombre,
            descripcion=ind.descripcion,
            formula_tipo=ind.formula_tipo.value,
            peso=float(ind.peso),
            activo=ind.activo,
            total_nivel2=n2_count,
            total_templates=t_count,
        ))
    return response


@router.post("/nivel1", response_model=Nivel1Response, status_code=status.HTTP_201_CREATED)
async def create_nivel1(
    body: Nivel1Create,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Nivel1Response:
    """Crea un indicador de Nivel 1."""
    ind = Indicator(
        nombre=body.nombre,
        descripcion=body.descripcion,
        formula_tipo=body.formula_tipo,
        peso=body.peso,
        activo=body.activo,
    )
    db.add(ind)
    await db.flush()
    await db.commit()
    await db.refresh(ind)
    return Nivel1Response(
        id=ind.id,
        nombre=ind.nombre,
        descripcion=ind.descripcion,
        formula_tipo=ind.formula_tipo.value,
        peso=float(ind.peso),
        activo=ind.activo,
        total_nivel2=0,
        total_templates=0,
    )


@router.put("/nivel1/{indicador_id}", response_model=Nivel1Response)
async def update_nivel1(
    indicador_id: int,
    body: Nivel1Update,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Nivel1Response:
    """Actualiza un indicador de Nivel 1."""
    result = await db.execute(select(Indicator).where(Indicator.id == indicador_id))
    ind = result.scalar_one_or_none()
    if ind is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indicador no encontrado")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(ind, field, value)
    await db.commit()
    await db.refresh(ind)

    n2_count = await db.scalar(
        select(func.count()).select_from(IndicadorNivel2).where(
            IndicadorNivel2.indicador_nivel1_id == ind.id
        )
    ) or 0
    from app.models.template import Template
    t_count = await db.scalar(
        select(func.count()).select_from(Template).where(
            Template.indicador_nivel1_id == ind.id
        )
    ) or 0
    return Nivel1Response(
        id=ind.id,
        nombre=ind.nombre,
        descripcion=ind.descripcion,
        formula_tipo=ind.formula_tipo.value,
        peso=float(ind.peso),
        activo=ind.activo,
        total_nivel2=n2_count,
        total_templates=t_count,
    )


@router.delete("/nivel1/{indicador_id}", status_code=status.HTTP_200_OK)
async def delete_nivel1(
    indicador_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Elimina (desactiva) un indicador de Nivel 1."""
    result = await db.execute(select(Indicator).where(Indicator.id == indicador_id))
    ind = result.scalar_one_or_none()
    if ind is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indicador no encontrado")

    ind.activo = False
    await db.commit()
    return {"detail": "Indicador desactivado exitosamente"}


# ── Level 2 endpoints ─────────────────────────────────────────────────────────

@router.get("/nivel2", response_model=list[Nivel2Response])
async def list_nivel2(
    nivel1_id: Optional[int] = Query(None),
    activo: Optional[bool] = None,
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> list[Nivel2Response]:
    """Lista indicadores de Nivel 2 con filtro opcional por nivel1_id."""
    query = select(IndicadorNivel2)
    if nivel1_id is not None:
        query = query.where(IndicadorNivel2.indicador_nivel1_id == nivel1_id)
    if activo is not None:
        query = query.where(IndicadorNivel2.activo == activo)
    query = query.order_by(IndicadorNivel2.id)

    result = await db.execute(query)
    items = result.scalars().all()

    response = []
    from app.models.template import Template
    for item in items:
        t_count = await db.scalar(
            select(func.count()).select_from(Template).where(
                Template.indicador_nivel2_id == item.id
            )
        ) or 0
        n1_nombre = None
        if item.indicador_nivel1:
            n1_nombre = item.indicador_nivel1.nombre
        response.append(Nivel2Response(
            id=item.id,
            nombre=item.nombre,
            descripcion=item.descripcion,
            indicador_nivel1_id=item.indicador_nivel1_id,
            indicador_nivel1_nombre=n1_nombre,
            activo=item.activo,
            total_templates=t_count,
        ))
    return response


@router.post("/nivel2", response_model=Nivel2Response, status_code=status.HTTP_201_CREATED)
async def create_nivel2(
    body: Nivel2Create,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Nivel2Response:
    """Crea un indicador de Nivel 2."""
    # Verify nivel1 exists
    n1_result = await db.execute(
        select(Indicator).where(Indicator.id == body.indicador_nivel1_id)
    )
    if n1_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Indicador Nivel 1 no encontrado",
        )

    item = IndicadorNivel2(
        nombre=body.nombre,
        descripcion=body.descripcion,
        indicador_nivel1_id=body.indicador_nivel1_id,
        activo=body.activo,
    )
    db.add(item)
    await db.flush()
    await db.commit()
    await db.refresh(item)

    return Nivel2Response(
        id=item.id,
        nombre=item.nombre,
        descripcion=item.descripcion,
        indicador_nivel1_id=item.indicador_nivel1_id,
        indicador_nivel1_nombre=item.indicador_nivel1.nombre if item.indicador_nivel1 else None,
        activo=item.activo,
        total_templates=0,
    )


@router.put("/nivel2/{indicador_id}", response_model=Nivel2Response)
async def update_nivel2(
    indicador_id: int,
    body: Nivel2Update,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Nivel2Response:
    """Actualiza un indicador de Nivel 2."""
    result = await db.execute(
        select(IndicadorNivel2).where(IndicadorNivel2.id == indicador_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indicador Nivel 2 no encontrado")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)

    from app.models.template import Template
    t_count = await db.scalar(
        select(func.count()).select_from(Template).where(
            Template.indicador_nivel2_id == item.id
        )
    ) or 0

    return Nivel2Response(
        id=item.id,
        nombre=item.nombre,
        descripcion=item.descripcion,
        indicador_nivel1_id=item.indicador_nivel1_id,
        indicador_nivel1_nombre=item.indicador_nivel1.nombre if item.indicador_nivel1 else None,
        activo=item.activo,
        total_templates=t_count,
    )


@router.delete("/nivel2/{indicador_id}", status_code=status.HTTP_200_OK)
async def delete_nivel2(
    indicador_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Elimina (desactiva) un indicador de Nivel 2."""
    result = await db.execute(
        select(IndicadorNivel2).where(IndicadorNivel2.id == indicador_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indicador Nivel 2 no encontrado")

    item.activo = False
    await db.commit()
    return {"detail": "Indicador Nivel 2 desactivado exitosamente"}

"""
app/routers/bi_dashboard.py — Dashboard BI de Planes Regionales de Búsqueda.

Admin:
  POST /admin/bi/upload   → carga un Excel con la misma estructura del BI
  GET  /admin/bi/status   → info del dataset cargado
  DELETE /admin/bi        → limpia todos los datos BI

Público:
  GET /bi/filters            → opciones de filtros (regionales, gitts, líneas, indicadores)
  GET /bi/kpis               → KPIs agregados con filtros
  GET /bi/by-regional        → avance agrupado por Regional
  GET /bi/by-gitt            → avance agrupado por GITT
  GET /bi/by-indicador       → avance agrupado por Indicador
  GET /bi/by-linea           → avance agrupado por Línea Estratégica
  GET /bi/monthly-evolution  → serie mensual de avance acumulado
  GET /bi/data               → tabla paginada con filtros
"""
import io
import logging
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bi_data import BiDataset, BiEstructura, BiHistorico, BiPRB
from app.models.user import User
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/admin/bi", tags=["BI Admin"])
public_router = APIRouter(prefix="/bi", tags=["BI Público"])


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

async def _get_admin(current_user: User = Depends(get_current_user)) -> User:
    from app.models.user import UserRole
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Solo administradores")
    return current_user


def _safe_float(v) -> float:
    try:
        if pd.isna(v):
            return 0.0
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(v) -> int:
    try:
        if pd.isna(v):
            return 0
        return int(v)
    except (TypeError, ValueError):
        return 0


def _safe_str(v) -> Optional[str]:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return str(v).strip()


def _apply_filters(query, *, regional=None, gitt=None, cod_linea=None,
                   cod_indicador=None, anio=None, prb_codes=None):
    """Aplica filtros comunes a una query sobre BiHistorico."""
    if prb_codes:
        query = query.where(BiHistorico.cod_prb.in_(prb_codes))
    if cod_indicador:
        query = query.where(BiHistorico.cod_indicador == cod_indicador)
    if anio:
        query = query.where(BiHistorico.anio == anio)
    return query


async def _resolve_prb_codes(db: AsyncSession, regional=None, gitt=None) -> Optional[list[int]]:
    """Retorna códigos PRB que coinciden con regional/gitt. None si no hay filtro."""
    if not regional and not gitt:
        return None
    conds = []
    if regional:
        conds.append(BiPRB.regional == regional)
    if gitt:
        conds.append(BiPRB.gitt == gitt)
    result = await db.execute(select(BiPRB.cod).where(and_(*conds)))
    return [r[0] for r in result.all()]


async def _resolve_indicador_codes(db: AsyncSession, cod_linea=None) -> Optional[list[int]]:
    if not cod_linea:
        return None
    result = await db.execute(
        select(BiEstructura.cod_indicador).where(BiEstructura.cod_linea == cod_linea)
    )
    return [r[0] for r in result.all()]


# ══════════════════════════════════════════════════════════════════════════════
# Admin: upload Excel
# ══════════════════════════════════════════════════════════════════════════════

@admin_router.post("/upload")
async def upload_bi_excel(
    file: UploadFile = File(...),
    current_user: User = Depends(_get_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Carga un Excel con hojas: 'PRB', 'EstructuraIndicadores', 'Historico'.
    Hace TRUNCATE + REPLACE de todos los datos BI (operación destructiva).
    """
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Archivo debe ser .xlsx o .xls")

    try:
        content = await file.read()
        xl = pd.ExcelFile(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el Excel: {exc}")

    required = ["PRB", "EstructuraIndicadores", "Historico"]
    missing = [s for s in required if s not in xl.sheet_names]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Faltan hojas obligatorias: {missing}. Hojas encontradas: {xl.sheet_names}",
        )

    try:
        df_prb = pd.read_excel(xl, sheet_name="PRB")
        df_est = pd.read_excel(xl, sheet_name="EstructuraIndicadores")
        df_hist = pd.read_excel(xl, sheet_name="Historico")
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Error leyendo hojas: {exc}")

    # ── TRUNCATE ──
    await db.execute(delete(BiHistorico))
    await db.execute(delete(BiEstructura))
    await db.execute(delete(BiPRB))
    await db.execute(delete(BiDataset))

    # ── PRB ──
    prb_count = 0
    for _, row in df_prb.iterrows():
        cod = _safe_int(row.get("COD"))
        if not cod:
            continue
        db.add(BiPRB(
            cod=cod,
            prb=_safe_str(row.get("PRB")) or f"PRB {cod}",
            regional=_safe_str(row.get("Regional")),
            gitt=_safe_str(row.get("GITT")),
        ))
        prb_count += 1

    # ── Estructura ──
    est_count = 0
    for _, row in df_est.iterrows():
        cod_ind = _safe_int(row.get("Cod_Indicador"))
        if not cod_ind:
            continue
        db.add(BiEstructura(
            cod_indicador=cod_ind,
            codigo_indicador=_safe_str(row.get("Código del Indicador")),
            indicador=_safe_str(row.get("Indicador")),
            cod_linea=_safe_int(row.get("Cod_Linea")) or None,
            linea=_safe_str(row.get("Linea")),
            cod_resultado=_safe_int(row.get("Cod_Resultado_estrategico")) or None,
            resultado=_safe_str(row.get("Resultado_Estrategico")),
        ))
        est_count += 1

    # ── Histórico ──
    # Some column headers may have spaces/newlines — normalize access
    def col(name, fallback=None):
        if name in df_hist.columns:
            return name
        return fallback

    hist_count = 0
    anios = set()
    indicadores_unicos = set()
    for _, row in df_hist.iterrows():
        cod_prb = _safe_int(row.get("CodPRB"))
        cod_ind = _safe_int(row.get("Cod_Indicador"))
        if not cod_prb or not cod_ind:
            continue

        # Filas con AÑO en blanco (PRBs "Sin Determinar") se descartan: el BI
        # las excluye también al aplicar el filtro de año 2026.
        anio_val = _safe_int(row.get("AÑO") if "AÑO" in df_hist.columns else row.get("AÑO "))
        if not anio_val:
            continue
        anios.add(anio_val)
        indicadores_unicos.add(cod_ind)

        db.add(BiHistorico(
            cod_prb=cod_prb,
            prb=_safe_str(row.get("PRB")),
            cod_indicador=cod_ind,
            codigo_indicador=_safe_str(row.get("Código del Indicador")),
            indicador=_safe_str(row.get("Indicador")),
            anio=anio_val,
            linea_base=_safe_float(row.get("Línea Base 2025") or row.get("Línea Base")),
            meta=_safe_float(row.get("Meta")),
            mes_1=_safe_float(row.get("Mes 1")),
            mes_2=_safe_float(row.get("Mes 2")),
            mes_3=_safe_float(row.get("Mes 3")),
            mes_4=_safe_float(row.get("Mes 4")),
            mes_5=_safe_float(row.get("Mes 5")),
            mes_6=_safe_float(row.get("Mes 6")),
            mes_7=_safe_float(row.get("Mes 7")),
            mes_8=_safe_float(row.get("Mes 8")),
            mes_9=_safe_float(row.get("Mes 9")),
            mes_10=_safe_float(row.get("Mes 10")),
            mes_11=_safe_float(row.get("Mes 11")),
            mes_12=_safe_float(row.get("Mes 12")),
            trim_i=_safe_float(row.get("Trim I")),
            trim_ii=_safe_float(row.get("Trim II")),
            trim_iii=_safe_float(row.get("Trim III")),
            trim_iv=_safe_float(row.get("Trim IV")),
            avance_total=_safe_float(row.get("Avance Total")),
            pct_avance=_safe_float(row.get("% de Avance")),
            variacion=_safe_float(
                row.get("Variación Respectp a 2025")
                or row.get("Variación Respecto a 2025")
            ),
        ))
        hist_count += 1

    ds = BiDataset(
        filename=file.filename,
        uploaded_by=current_user.nombre_completo or current_user.email,
        total_rows=hist_count,
        total_prb=prb_count,
        total_indicadores=len(indicadores_unicos),
        anio=max(anios) if anios else None,
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(ds)

    await db.commit()

    return {
        "ok": True,
        "filename": file.filename,
        "total_rows": hist_count,
        "total_prb": prb_count,
        "total_indicadores": len(indicadores_unicos),
        "anios": sorted(anios),
        "mensaje": f"Cargados {hist_count} registros históricos, {prb_count} PRB, "
                   f"{est_count} indicadores estructura.",
    }


@admin_router.get("/status")
async def bi_status(
    current_user: User = Depends(_get_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Información del dataset BI cargado."""
    result = await db.execute(
        select(BiDataset).order_by(BiDataset.uploaded_at.desc()).limit(1)
    )
    ds = result.scalar_one_or_none()
    if not ds:
        return {"loaded": False, "message": "No hay datos BI cargados aún."}

    total_hist = await db.scalar(select(func.count(BiHistorico.id))) or 0
    return {
        "loaded": True,
        "filename": ds.filename,
        "uploaded_by": ds.uploaded_by,
        "uploaded_at": ds.uploaded_at.isoformat() if ds.uploaded_at else None,
        "total_rows": total_hist,
        "total_prb": ds.total_prb,
        "total_indicadores": ds.total_indicadores,
        "anio": ds.anio,
    }


@admin_router.delete("")
async def clear_bi(
    current_user: User = Depends(_get_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Borra todos los datos BI."""
    await db.execute(delete(BiHistorico))
    await db.execute(delete(BiEstructura))
    await db.execute(delete(BiPRB))
    await db.execute(delete(BiDataset))
    await db.commit()
    return {"ok": True, "mensaje": "Datos BI eliminados."}


# ══════════════════════════════════════════════════════════════════════════════
# Público: filtros disponibles
# ══════════════════════════════════════════════════════════════════════════════

@public_router.get("/filters")
async def get_filters(db: AsyncSession = Depends(get_db)) -> dict:
    """Opciones para los dropdowns del dashboard."""
    regionales = await db.execute(
        select(BiPRB.regional).where(BiPRB.regional.isnot(None)).distinct().order_by(BiPRB.regional)
    )
    gitts = await db.execute(
        select(BiPRB.gitt).where(BiPRB.gitt.isnot(None)).distinct().order_by(BiPRB.gitt)
    )
    lineas = await db.execute(
        select(BiEstructura.cod_linea, BiEstructura.linea)
        .where(BiEstructura.cod_linea.isnot(None))
        .distinct()
        .order_by(BiEstructura.cod_linea)
    )
    indicadores = await db.execute(
        select(BiEstructura.cod_indicador, BiEstructura.codigo_indicador, BiEstructura.indicador)
        .order_by(BiEstructura.cod_indicador)
    )
    anios = await db.execute(
        select(BiHistorico.anio).distinct().order_by(BiHistorico.anio)
    )
    return {
        "regionales": [r[0] for r in regionales.all()],
        "gitts": [g[0] for g in gitts.all()],
        "lineas": [{"cod": c, "nombre": n} for c, n in lineas.all()],
        "indicadores": [
            {"cod": c, "codigo": co, "nombre": n}
            for c, co, n in indicadores.all()
        ],
        "anios": [int(a[0]) for a in anios.all() if a[0]],
    }


# ══════════════════════════════════════════════════════════════════════════════
# Público: agregaciones KPI
# ══════════════════════════════════════════════════════════════════════════════

@public_router.get("/kpis")
async def get_kpis(
    regional: Optional[str] = None,
    gitt: Optional[str] = None,
    cod_linea: Optional[int] = None,
    cod_indicador: Optional[int] = None,
    anio: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """KPIs agregados: total meta, total avance, % promedio, nº PRBs, nº indicadores."""
    prb_codes = await _resolve_prb_codes(db, regional, gitt)
    if cod_linea and not cod_indicador:
        lin_codes = await _resolve_indicador_codes(db, cod_linea)
        if lin_codes:
            # Restrict cod_indicador to matching set via filter
            extra_filter = lin_codes
        else:
            extra_filter = [-1]  # no matches
    else:
        extra_filter = None

    conds = []
    if prb_codes is not None:
        conds.append(BiHistorico.cod_prb.in_(prb_codes) if prb_codes else BiHistorico.cod_prb == -1)
    if cod_indicador:
        conds.append(BiHistorico.cod_indicador == cod_indicador)
    elif extra_filter is not None:
        conds.append(BiHistorico.cod_indicador.in_(extra_filter))
    if anio:
        conds.append(BiHistorico.anio == anio)

    base_where = and_(*conds) if conds else None

    total_meta = await db.scalar(
        select(func.coalesce(func.sum(BiHistorico.meta), 0)).where(base_where) if base_where is not None
        else select(func.coalesce(func.sum(BiHistorico.meta), 0))
    ) or 0
    total_avance = await db.scalar(
        select(func.coalesce(func.sum(BiHistorico.avance_total), 0)).where(base_where) if base_where is not None
        else select(func.coalesce(func.sum(BiHistorico.avance_total), 0))
    ) or 0
    avg_pct = await db.scalar(
        select(func.coalesce(func.avg(BiHistorico.pct_avance), 0)).where(base_where) if base_where is not None
        else select(func.coalesce(func.avg(BiHistorico.pct_avance), 0))
    ) or 0
    total_prbs = await db.scalar(
        select(func.count(func.distinct(BiHistorico.cod_prb))).where(base_where) if base_where is not None
        else select(func.count(func.distinct(BiHistorico.cod_prb)))
    ) or 0
    total_indicadores = await db.scalar(
        select(func.count(func.distinct(BiHistorico.cod_indicador))).where(base_where) if base_where is not None
        else select(func.count(func.distinct(BiHistorico.cod_indicador)))
    ) or 0
    total_registros = await db.scalar(
        select(func.count(BiHistorico.id)).where(base_where) if base_where is not None
        else select(func.count(BiHistorico.id))
    ) or 0

    total_dato_2025 = await db.scalar(
        select(func.coalesce(func.sum(BiHistorico.linea_base), 0)).where(base_where) if base_where is not None
        else select(func.coalesce(func.sum(BiHistorico.linea_base), 0))
    ) or 0

    return {
        "total_meta": float(total_meta),
        "total_avance": float(total_avance),
        "total_dato_2025": float(total_dato_2025),
        "pct_global": (float(total_avance) / float(total_meta) * 100) if total_meta else 0.0,
        "pct_promedio": float(avg_pct) * 100 if avg_pct and avg_pct < 2 else float(avg_pct),
        "total_prbs": int(total_prbs),
        "total_indicadores": int(total_indicadores),
        "total_registros": int(total_registros),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Público: agrupaciones para gráficas
# ══════════════════════════════════════════════════════════════════════════════

async def _grouped_chart(
    db: AsyncSession,
    *,
    group_col,
    group_name,
    join_prb: bool = False,
    join_est: bool = False,
    regional=None, gitt=None, cod_linea=None, cod_indicador=None, anio=None,
):
    """Helper para gráficos agregados (meta vs avance) agrupados por una columna."""
    q = select(
        group_col.label("grupo"),
        func.coalesce(func.sum(BiHistorico.meta), 0).label("meta"),
        func.coalesce(func.sum(BiHistorico.avance_total), 0).label("avance"),
    )
    if join_prb:
        q = q.join(BiPRB, BiPRB.cod == BiHistorico.cod_prb)
    if join_est:
        q = q.join(BiEstructura, BiEstructura.cod_indicador == BiHistorico.cod_indicador)

    if regional:
        if not join_prb:
            q = q.join(BiPRB, BiPRB.cod == BiHistorico.cod_prb)
        q = q.where(BiPRB.regional == regional)
    if gitt:
        if not join_prb and not regional:
            q = q.join(BiPRB, BiPRB.cod == BiHistorico.cod_prb)
        q = q.where(BiPRB.gitt == gitt)
    if cod_linea:
        if not join_est:
            q = q.join(BiEstructura, BiEstructura.cod_indicador == BiHistorico.cod_indicador)
        q = q.where(BiEstructura.cod_linea == cod_linea)
    if cod_indicador:
        q = q.where(BiHistorico.cod_indicador == cod_indicador)
    if anio:
        q = q.where(BiHistorico.anio == anio)

    q = q.group_by(group_col).order_by(group_col)
    result = await db.execute(q)
    rows = result.all()
    return [
        {
            "grupo": r.grupo,
            "meta": float(r.meta),
            "avance": float(r.avance),
            "pct": (float(r.avance) / float(r.meta) * 100) if r.meta else 0.0,
        }
        for r in rows if r.grupo is not None
    ]


@public_router.get("/by-regional")
async def by_regional(
    gitt: Optional[str] = None, cod_linea: Optional[int] = None,
    cod_indicador: Optional[int] = None, anio: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    return await _grouped_chart(
        db, group_col=BiPRB.regional, group_name="regional", join_prb=True,
        gitt=gitt, cod_linea=cod_linea, cod_indicador=cod_indicador, anio=anio,
    )


@public_router.get("/by-gitt")
async def by_gitt(
    regional: Optional[str] = None, cod_linea: Optional[int] = None,
    cod_indicador: Optional[int] = None, anio: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    return await _grouped_chart(
        db, group_col=BiPRB.gitt, group_name="gitt", join_prb=True,
        regional=regional, cod_linea=cod_linea, cod_indicador=cod_indicador, anio=anio,
    )


@public_router.get("/by-indicador")
async def by_indicador(
    regional: Optional[str] = None, gitt: Optional[str] = None,
    cod_linea: Optional[int] = None, anio: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    return await _grouped_chart(
        db, group_col=BiEstructura.codigo_indicador, group_name="codigo", join_est=True,
        regional=regional, gitt=gitt, cod_linea=cod_linea, anio=anio,
    )


@public_router.get("/by-linea")
async def by_linea(
    regional: Optional[str] = None, gitt: Optional[str] = None,
    cod_indicador: Optional[int] = None, anio: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    return await _grouped_chart(
        db, group_col=BiEstructura.linea, group_name="linea", join_est=True,
        regional=regional, gitt=gitt, cod_indicador=cod_indicador, anio=anio,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Público: evolución mensual
# ══════════════════════════════════════════════════════════════════════════════

@public_router.get("/monthly-evolution")
async def monthly_evolution(
    regional: Optional[str] = None, gitt: Optional[str] = None,
    cod_linea: Optional[int] = None, cod_indicador: Optional[int] = None,
    anio: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Serie mensual acumulada. Retorna [{mes:1..12, valor:..., meta_acumulada:...}]."""
    month_cols = [
        BiHistorico.mes_1, BiHistorico.mes_2, BiHistorico.mes_3, BiHistorico.mes_4,
        BiHistorico.mes_5, BiHistorico.mes_6, BiHistorico.mes_7, BiHistorico.mes_8,
        BiHistorico.mes_9, BiHistorico.mes_10, BiHistorico.mes_11, BiHistorico.mes_12,
    ]
    select_cols = [func.coalesce(func.sum(c), 0).label(f"m{i+1}") for i, c in enumerate(month_cols)]
    select_cols.append(func.coalesce(func.sum(BiHistorico.meta), 0).label("meta"))

    q = select(*select_cols)
    needs_prb = bool(regional or gitt)
    needs_est = bool(cod_linea)
    if needs_prb:
        q = q.join(BiPRB, BiPRB.cod == BiHistorico.cod_prb)
    if needs_est:
        q = q.join(BiEstructura, BiEstructura.cod_indicador == BiHistorico.cod_indicador)
    if regional:
        q = q.where(BiPRB.regional == regional)
    if gitt:
        q = q.where(BiPRB.gitt == gitt)
    if cod_linea:
        q = q.where(BiEstructura.cod_linea == cod_linea)
    if cod_indicador:
        q = q.where(BiHistorico.cod_indicador == cod_indicador)
    if anio:
        q = q.where(BiHistorico.anio == anio)

    # dato 2025 (línea base) — agregado constante que se dibuja como línea horizontal
    dato_2025_q = select(func.coalesce(func.sum(BiHistorico.linea_base), 0))
    if needs_prb:
        dato_2025_q = dato_2025_q.join(BiPRB, BiPRB.cod == BiHistorico.cod_prb)
    if needs_est:
        dato_2025_q = dato_2025_q.join(BiEstructura, BiEstructura.cod_indicador == BiHistorico.cod_indicador)
    if regional:
        dato_2025_q = dato_2025_q.where(BiPRB.regional == regional)
    if gitt:
        dato_2025_q = dato_2025_q.where(BiPRB.gitt == gitt)
    if cod_linea:
        dato_2025_q = dato_2025_q.where(BiEstructura.cod_linea == cod_linea)
    if cod_indicador:
        dato_2025_q = dato_2025_q.where(BiHistorico.cod_indicador == cod_indicador)
    if anio:
        dato_2025_q = dato_2025_q.where(BiHistorico.anio == anio)
    dato_2025 = float(await db.scalar(dato_2025_q) or 0)

    row = (await db.execute(q)).one()
    monthly = [float(row[i]) for i in range(12)]
    meta_total = float(row[12]) or 0.0
    meta_mensual_objetivo = meta_total / 12 if meta_total else 0

    acumulado = 0.0
    meta_acum = 0.0
    series = []
    for i, v in enumerate(monthly):
        acumulado += v
        meta_acum += meta_mensual_objetivo
        series.append({
            "mes": i + 1,
            "mes_nombre": ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                           "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"][i],
            "valor": v,
            "acumulado": acumulado,
            "meta_acumulada": meta_acum,
            "dato_2025": dato_2025,
        })
    return series


# ══════════════════════════════════════════════════════════════════════════════
# Público: tarjetas de indicadores (Página 1 del BI)
# ══════════════════════════════════════════════════════════════════════════════

@public_router.get("/indicadores-summary")
async def indicadores_summary(
    regional: Optional[str] = None, gitt: Optional[str] = None,
    cod_linea: Optional[int] = None, cod_indicador: Optional[int] = None,
    anio: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """
    Una tarjeta por indicador con Dato 2025 (línea base), Avance 2026, Meta 2026 y %.
    Respeta los filtros activos.
    """
    q = select(
        BiHistorico.cod_indicador.label("cod"),
        BiHistorico.codigo_indicador.label("codigo"),
        BiHistorico.indicador.label("nombre"),
        func.coalesce(func.sum(BiHistorico.linea_base), 0).label("dato_2025"),
        func.coalesce(func.sum(BiHistorico.avance_total), 0).label("avance"),
        func.coalesce(func.sum(BiHistorico.meta), 0).label("meta"),
    )

    needs_prb = bool(regional or gitt)
    needs_est = bool(cod_linea)
    if needs_prb:
        q = q.join(BiPRB, BiPRB.cod == BiHistorico.cod_prb)
    if needs_est:
        q = q.join(BiEstructura, BiEstructura.cod_indicador == BiHistorico.cod_indicador)
    if regional:
        q = q.where(BiPRB.regional == regional)
    if gitt:
        q = q.where(BiPRB.gitt == gitt)
    if cod_linea:
        q = q.where(BiEstructura.cod_linea == cod_linea)
    if cod_indicador:
        q = q.where(BiHistorico.cod_indicador == cod_indicador)
    if anio:
        q = q.where(BiHistorico.anio == anio)

    q = q.group_by(
        BiHistorico.cod_indicador,
        BiHistorico.codigo_indicador,
        BiHistorico.indicador,
    ).order_by(BiHistorico.cod_indicador)  # orden natural del Excel (111..123)

    rows = (await db.execute(q)).all()
    return [
        {
            "cod": r.cod,
            "codigo": r.codigo,
            "nombre": r.nombre,
            "dato_2025": float(r.dato_2025 or 0),
            "avance": float(r.avance or 0),
            "meta": float(r.meta or 0),
            "pct": (float(r.avance) / float(r.meta) * 100) if r.meta else 0.0,
        }
        for r in rows
    ]


# ══════════════════════════════════════════════════════════════════════════════
# Público: comparación A vs B (Página 2 del BI)
# ══════════════════════════════════════════════════════════════════════════════

@public_router.get("/comparison")
async def comparison(
    a_tipo: str = Query(..., description="'gitt' | 'prb' | 'regional' | 'meta'"),
    a_valor: Optional[str] = None,
    b_tipo: str = Query(..., description="'gitt' | 'prb' | 'regional' | 'meta'"),
    b_valor: Optional[str] = None,
    anio: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Compara dos selecciones jerárquicas (GITT, PRB, Regional, o META global)
    devolviendo, por cada indicador, el avance de cada grupo.
    """
    async def _fetch(tipo: str, valor: Optional[str]):
        q = select(
            BiHistorico.codigo_indicador.label("codigo"),
            BiHistorico.indicador.label("nombre"),
            func.coalesce(func.sum(BiHistorico.avance_total), 0).label("avance"),
            func.coalesce(func.sum(BiHistorico.meta), 0).label("meta"),
        )
        if tipo == "meta":
            # Grupo META → usa la META global (total de metas)
            pass
        elif tipo == "regional":
            q = q.join(BiPRB, BiPRB.cod == BiHistorico.cod_prb)
            if valor:
                q = q.where(BiPRB.regional == valor)
        elif tipo == "gitt":
            q = q.join(BiPRB, BiPRB.cod == BiHistorico.cod_prb)
            if valor:
                q = q.where(BiPRB.gitt == valor)
        elif tipo == "prb":
            if valor:
                q = q.where(BiHistorico.prb == valor)
        if anio:
            q = q.where(BiHistorico.anio == anio)

        q = q.group_by(BiHistorico.codigo_indicador, BiHistorico.indicador) \
             .order_by(BiHistorico.codigo_indicador)
        rows = (await db.execute(q)).all()
        return {r.codigo: {"codigo": r.codigo, "nombre": r.nombre,
                           "avance": float(r.avance or 0),
                           "meta": float(r.meta or 0)} for r in rows}

    a_data = await _fetch(a_tipo, a_valor)
    b_data = await _fetch(b_tipo, b_valor)

    # Para el grupo META el "valor" es la meta sumada → lo usamos como barra
    if a_tipo == "meta":
        for k, v in a_data.items():
            v["avance"] = v["meta"]
    if b_tipo == "meta":
        for k, v in b_data.items():
            v["avance"] = v["meta"]

    # Unión de indicadores
    codigos = sorted(set(list(a_data.keys()) + list(b_data.keys())))
    indicadores = []
    sum_a = 0.0
    sum_b = 0.0
    max_gap = (0.0, None, None)  # gap absoluto, indicador, ventaja
    for cod in codigos:
        a = a_data.get(cod)
        b = b_data.get(cod)
        nombre = (a or b).get("nombre") if (a or b) else cod
        av_a = a["avance"] if a else 0.0
        av_b = b["avance"] if b else 0.0
        sum_a += av_a
        sum_b += av_b
        gap = av_a - av_b
        if abs(gap) > abs(max_gap[0]):
            max_gap = (gap, cod, nombre)
        indicadores.append({
            "codigo": cod,
            "nombre": nombre,
            "a": av_a,
            "b": av_b,
        })

    # Narrativa
    hallazgo = ""
    if max_gap[1]:
        ventaja = "A supera a B" if max_gap[0] > 0 else "B supera a A"
        pct_gap = (abs(max_gap[0]) / max(abs(sum_a), abs(sum_b)) * 100) if max(sum_a, sum_b) else 0
        hallazgo = f"La mayor diferencia se observa en el indicador '{max_gap[2]}', donde {ventaja} en {pct_gap:.1f}%."

    def _estado(tot, label):
        if tot >= 70:
            return f"{label} | 🟢 Óptimo"
        if tot >= 40:
            return f"{label} | 🟡 Moderado"
        if tot > 0:
            return f"{label} | 🟠 En progreso"
        return f"{label} | 🔴 Crítico"

    total_pct_a = (sum_a / sum(d["meta"] for d in a_data.values()) * 100) if a_data and sum(d["meta"] for d in a_data.values()) else 0
    total_pct_b = (sum_b / sum(d["meta"] for d in b_data.values()) * 100) if b_data and sum(d["meta"] for d in b_data.values()) else 0

    brecha = sum_a - sum_b
    if brecha > 0:
        brecha_txt = f"A supera a B en {brecha:,.0f} unidades de avance."
    elif brecha < 0:
        brecha_txt = f"B supera a A en {abs(brecha):,.0f} unidades de avance."
    else:
        brecha_txt = "A y B tienen el mismo nivel de avance."

    return {
        "a": {"tipo": a_tipo, "valor": a_valor, "total": sum_a, "pct": total_pct_a},
        "b": {"tipo": b_tipo, "valor": b_valor, "total": sum_b, "pct": total_pct_b},
        "indicadores": indicadores,
        "hallazgo": hallazgo,
        "estado_a": _estado(total_pct_a, f"{a_tipo.upper()}{(' | ' + a_valor) if a_valor else ''}"),
        "estado_b": _estado(total_pct_b, f"{b_tipo.upper()}{(' | ' + b_valor) if b_valor else ''}"),
        "brecha": brecha_txt,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Público: listado de valores para filtros jerárquicos
# ══════════════════════════════════════════════════════════════════════════════

@public_router.get("/hierarchy-values")
async def hierarchy_values(
    tipo: str = Query(..., description="'gitt' | 'prb' | 'regional'"),
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    """Devuelve los valores disponibles para un tipo de jerarquía."""
    if tipo == "gitt":
        r = await db.execute(select(BiPRB.gitt).where(BiPRB.gitt.isnot(None)).distinct().order_by(BiPRB.gitt))
    elif tipo == "regional":
        r = await db.execute(select(BiPRB.regional).where(BiPRB.regional.isnot(None)).distinct().order_by(BiPRB.regional))
    elif tipo == "prb":
        r = await db.execute(select(BiPRB.prb).where(BiPRB.prb.isnot(None)).distinct().order_by(BiPRB.prb))
    else:
        raise HTTPException(status_code=400, detail=f"Tipo inválido: {tipo}")
    return [row[0] for row in r.all() if row[0]]


# ══════════════════════════════════════════════════════════════════════════════
# Público: tabla de datos paginada
# ══════════════════════════════════════════════════════════════════════════════

@public_router.get("/data")
async def get_data(
    regional: Optional[str] = None, gitt: Optional[str] = None,
    cod_linea: Optional[int] = None, cod_indicador: Optional[int] = None,
    anio: Optional[int] = None,
    page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    conds = []
    needs_prb = bool(regional or gitt)
    needs_est = bool(cod_linea)

    q = select(
        BiHistorico, BiPRB.regional, BiPRB.gitt,
    ).outerjoin(BiPRB, BiPRB.cod == BiHistorico.cod_prb)

    if needs_est:
        q = q.outerjoin(BiEstructura, BiEstructura.cod_indicador == BiHistorico.cod_indicador)
    if regional:
        conds.append(BiPRB.regional == regional)
    if gitt:
        conds.append(BiPRB.gitt == gitt)
    if cod_linea:
        conds.append(BiEstructura.cod_linea == cod_linea)
    if cod_indicador:
        conds.append(BiHistorico.cod_indicador == cod_indicador)
    if anio:
        conds.append(BiHistorico.anio == anio)

    where = and_(*conds) if conds else None
    if where is not None:
        q = q.where(where)

    # count
    count_q = select(func.count()).select_from(q.subquery())
    total = await db.scalar(count_q) or 0

    q = q.order_by(BiHistorico.cod_prb, BiHistorico.cod_indicador) \
         .offset((page - 1) * size).limit(size)
    rows = (await db.execute(q)).all()

    items = []
    for h, regional_name, gitt_name in rows:
        items.append({
            "id": str(h.id),
            "cod_prb": h.cod_prb,
            "prb": h.prb,
            "regional": regional_name,
            "gitt": gitt_name,
            "codigo_indicador": h.codigo_indicador,
            "indicador": h.indicador,
            "anio": h.anio,
            "linea_base": h.linea_base,
            "meta": h.meta,
            "avance_total": h.avance_total,
            "pct_avance": h.pct_avance,
            "variacion": h.variacion,
            "meses": [h.mes_1, h.mes_2, h.mes_3, h.mes_4, h.mes_5, h.mes_6,
                      h.mes_7, h.mes_8, h.mes_9, h.mes_10, h.mes_11, h.mes_12],
            "trims": [h.trim_i, h.trim_ii, h.trim_iii, h.trim_iv],
        })

    return {"total": total, "page": page, "size": size, "items": items}

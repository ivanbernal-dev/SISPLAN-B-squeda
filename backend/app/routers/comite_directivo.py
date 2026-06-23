"""Visor de solo lectura para el Comité Directivo.

El catálogo anual se conserva como una referencia versionada y los reportes
mensuales aprobados se leen desde ``formularios_respondidos``. Este módulo no
modifica formularios, validaciones, estadísticas ni el dashboard BI.
"""
from __future__ import annotations

import copy
import json
import re
import unicodedata
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.form import Form, FormStatus


router = APIRouter(prefix="/comite-directivo", tags=["Comité Directivo"])

PERIODOS = [
    {"key": "ene_feb", "label": "Ene–Feb"},
    {"key": "marzo", "label": "Mar"},
    {"key": "abril", "label": "Abr"},
    {"key": "mayo", "label": "May"},
    {"key": "junio", "label": "Jun"},
    {"key": "julio", "label": "Jul"},
    {"key": "agosto", "label": "Ago"},
    {"key": "septiembre", "label": "Sep"},
    {"key": "octubre", "label": "Oct"},
    {"key": "noviembre", "label": "Nov"},
    {"key": "diciembre", "label": "Dic"},
]
PERIODO_ORDEN = {periodo["key"]: index for index, periodo in enumerate(PERIODOS)}
CATALOGO_PATH = Path(__file__).resolve().parents[1] / "data" / "comite_directivo_2026.json"


def _normalizar_texto(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text).strip().casefold()


def _dependencia_canonica(value: Any) -> str:
    text = str(value or "").strip()
    normalized = _normalizar_texto(text)
    if normalized in {"sgh", "subdireccion gestion humana", "subdireccion de gestion humana"}:
        return "Subdirección de Gestión Humana"
    return text


@lru_cache(maxsize=1)
def _catalogo_base() -> tuple[dict[str, Any], ...]:
    if not CATALOGO_PATH.exists():
        raise RuntimeError(f"No existe el catálogo anual: {CATALOGO_PATH}")
    with CATALOGO_PATH.open("r", encoding="utf-8") as file:
        raw = json.load(file)
    if not isinstance(raw, list):
        raise RuntimeError("El catálogo de Comité Directivo debe ser una lista JSON.")
    return tuple(raw)


def _dato(data: dict[str, Any], *names: str) -> Any:
    for name in names:
        value = data.get(name)
        if value not in (None, ""):
            return value
    return None


def _numero(value: Any) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("%", "").replace(" ", "")
    if not text:
        return None
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def _periodo_key(value: Any, fallback: date | datetime | None = None) -> str | None:
    if isinstance(value, (date, datetime)):
        month = value.month
    else:
        text = _normalizar_texto(value)
        if not text and fallback:
            month = fallback.month
        elif re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", text):
            month = int(text.split("-")[1])
        elif text.isdigit() and 1 <= int(text) <= 12:
            month = int(text)
        else:
            aliases = {
                "enero": "ene_feb", "febrero": "ene_feb", "enero - febrero": "ene_feb",
                "enero-febrero": "ene_feb", "ene_feb": "ene_feb", "marzo": "marzo",
                "abril": "abril", "mayo": "mayo", "junio": "junio", "julio": "julio",
                "agosto": "agosto", "septiembre": "septiembre", "setiembre": "septiembre",
                "octubre": "octubre", "noviembre": "noviembre", "diciembre": "diciembre",
            }
            return aliases.get(text)
    if month in (1, 2):
        return "ene_feb"
    return {
        3: "marzo", 4: "abril", 5: "mayo", 6: "junio", 7: "julio",
        8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
    }.get(month)


def _vigencia_formulario(form: Form) -> int | None:
    data = form.datos_dinamicos or {}
    raw = _dato(data, "vigencia", "anio", "año")
    if raw is not None:
        match = re.search(r"20\d{2}", str(raw))
        if match:
            return int(match.group())
    if form.fecha_usuario:
        return form.fecha_usuario.year
    if form.fecha_carga:
        return form.fecha_carga.year
    return None


def _variables_formulario(data: dict[str, Any]) -> list[dict[str, Any]]:
    variables: list[dict[str, Any]] = []
    for index in range(1, 8):
        name = _dato(data, f"variable_{index}", f"nombre_variable_{index}")
        monthly = _dato(
            data,
            f"reporte_cuantitativo_variable_{index}",
            f"valor_variable_{index}",
            f"dato_variable_{index}",
        )
        accumulated = _dato(
            data,
            f"acumulado_variable_{index}",
            f"valor_acumulado_variable_{index}",
        )
        if name is None and monthly is None and accumulated is None:
            continue
        variables.append({
            "numero": index,
            "nombre": str(name or f"Variable {index}"),
            "valor_mes": monthly,
            "valor_acumulado": accumulated,
            "acumulado_calculado": False,
        })
    return variables


def _reporte_formulario(form: Form, period_key: str) -> dict[str, Any]:
    data = form.datos_dinamicos or {}
    result = _dato(data, "calculo_formula", "resultado_indicador", "resultado", "valor_resultado")
    progress = _numero(_dato(data, "avance", "porcentaje_avance", "calculo_formula"))
    display = str(result) if result not in (None, "") else "Sin reporte"
    if progress is not None and "%" not in display and _normalizar_texto(_dato(data, "unidad_medida", "unidad")) == "porcentaje":
        display = f"{progress:g}%"
    return {
        "label": next(item["label"] for item in PERIODOS if item["key"] == period_key),
        "resultado": result,
        "resultado_acumulado": _dato(data, "resultado_acumulado", "calculo_formula_acumulado"),
        "display": display,
        "avance": progress,
        "tipo": "formulario_aprobado",
        "analisis": str(_dato(data, "informe_cualitativo", "analisis_cualitativo") or form.informe_cualitativo or ""),
        "logros": str(_dato(data, "logros_dificultades", "avances_logros", "logros", "retrasos_dificultades") or ""),
        "observaciones": str(_dato(data, "observaciones", "comentarios_extra", "comentarios_adicionales") or ""),
        "observacionOap": str(_dato(data, "obs_oap", "observacion_oap", "comentario_oap") or ""),
        "estadoOap": str(_dato(data, "obs_oap_estado", "estado_observacion_oap") or "Pendiente"),
        "variables": _variables_formulario(data),
        "fuente": "formulario_aprobado",
        "formulario_id": str(form.id),
        "fecha_validacion": form.fecha_validacion.isoformat() if form.fecha_validacion else None,
        "validado_por": form.validado_por.nombre_completo if form.validado_por else None,
    }


def _preparar_catalogo(vigencia: int) -> list[dict[str, Any]]:
    items = [copy.deepcopy(item) for item in _catalogo_base() if int(item.get("vigencia", 2026)) == vigencia]
    for item in items:
        item["dependencia"] = _dependencia_canonica(item.get("dependencia"))
        for period in PERIODOS:
            current = (item.get("meses") or {}).get(period["key"])
            if current is None:
                current = {
                    "label": period["label"], "resultado": None, "display": "Sin reporte",
                    "avance": None, "tipo": "sin_reporte", "analisis": "", "logros": "",
                    "observaciones": "", "observacionOap": "",
                }
            current.setdefault("variables", [])
            current.setdefault("estadoOap", "Pendiente")
            current.setdefault("fuente", "catalogo_2026")
            item.setdefault("meses", {})[period["key"]] = current
    return items


def _seleccionar_indicador(form: Form, items: list[dict[str, Any]]) -> dict[str, Any] | None:
    data = form.datos_dinamicos or {}
    code = _normalizar_texto(_dato(data, "codigo_indicador", "codigo", "no_indicador", "id_indicador"))
    name = _normalizar_texto(_dato(data, "indicador", "nombre_indicador"))
    dependency = _normalizar_texto(form.dependency.nombre if form.dependency else _dato(data, "dependencia"))

    candidates = items
    if name:
        by_name = [item for item in candidates if _normalizar_texto(item.get("nombre")) == name]
        if len(by_name) == 1:
            return by_name[0]
        if by_name:
            candidates = by_name
    if code:
        by_code = [item for item in candidates if _normalizar_texto(item.get("codigo")) == code]
        if len(by_code) == 1:
            return by_code[0]
        if by_code:
            candidates = by_code
    if dependency and len(candidates) > 1:
        by_dependency = [
            item for item in candidates
            if _normalizar_texto(_dependencia_canonica(item.get("dependencia"))) == dependency
        ]
        if len(by_dependency) == 1:
            return by_dependency[0]
    return candidates[0] if len(candidates) == 1 and (code or name) else None


def _calcular_acumulados(items: list[dict[str, Any]]) -> None:
    for item in items:
        totals: dict[int, float] = {}
        for period in PERIODOS:
            report = item["meses"][period["key"]]
            for variable in report.get("variables") or []:
                number = int(variable["numero"])
                explicit = variable.get("valor_acumulado")
                monthly_number = _numero(variable.get("valor_mes"))
                if explicit not in (None, ""):
                    explicit_number = _numero(explicit)
                    if explicit_number is not None:
                        totals[number] = explicit_number
                    continue
                if monthly_number is None:
                    variable["valor_acumulado"] = None
                    continue
                totals[number] = totals.get(number, 0.0) + monthly_number
                variable["valor_acumulado"] = totals[number]
                variable["acumulado_calculado"] = True


def _ultimo_avance(item: dict[str, Any]) -> float | None:
    for period in reversed(PERIODOS):
        value = _numero(item["meses"][period["key"]].get("avance"))
        if value is not None:
            return value
    return None


async def _obtener_indicadores(db: AsyncSession, vigencia: int) -> list[dict[str, Any]]:
    items = _preparar_catalogo(vigencia)
    result = await db.execute(
        select(Form)
        .where(
            Form.estado == FormStatus.approved,
            or_(Form.fecha_usuario.is_(None), Form.fecha_usuario.between(date(vigencia, 1, 1), date(vigencia, 12, 31))),
        )
        .options(selectinload(Form.dependency), selectinload(Form.validado_por))
        .order_by(Form.fecha_usuario.asc().nulls_last(), Form.fecha_validacion.asc().nulls_last())
    )
    for form in result.scalars().all():
        if _vigencia_formulario(form) != vigencia:
            continue
        data = form.datos_dinamicos or {}
        period_key = _periodo_key(_dato(data, "mes_reporte", "periodo_reporte", "mes"), form.fecha_usuario)
        item = _seleccionar_indicador(form, items)
        if period_key and item:
            item["meses"][period_key] = _reporte_formulario(form, period_key)
    _calcular_acumulados(items)
    return items


def _filtrar(
    items: list[dict[str, Any]], linea: str | None, dependencia: str | None,
    estado: str | None, query: str | None,
) -> list[dict[str, Any]]:
    search = _normalizar_texto(query)
    result: list[dict[str, Any]] = []
    for item in items:
        if linea and linea != "Todas" and item.get("linea") != linea:
            continue
        if dependencia and dependencia != "Todas" and item.get("dependencia") != dependencia:
            continue
        if estado and estado != "Todos" and _normalizar_texto(item.get("estado")) != _normalizar_texto(estado):
            continue
        haystack = _normalizar_texto(" ".join(str(item.get(key, "")) for key in ("codigo", "nombre", "dependencia")))
        if search and search not in haystack:
            continue
        result.append(item)
    return result


@router.get("/indicadores", summary="Indicadores ejecutivos aprobados")
async def listar_indicadores(
    vigencia: int = Query(2026, ge=2020, le=2100),
    linea: str | None = Query(None),
    dependencia: str | None = Query(None),
    estado: str | None = Query(None),
    q: str | None = Query(None, max_length=120),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        all_items = await _obtener_indicadores(db, vigencia)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    items = _filtrar(all_items, linea, dependencia, estado, q)
    advances = [value for item in items if (value := _ultimo_avance(item)) is not None]
    oap = sum(
        1 for item in items for report in item.get("meses", {}).values()
        if str(report.get("observacionOap") or "").strip()
    )
    filters = {
        "lineas": sorted({item["linea"] for item in all_items if item.get("linea")}),
        "dependencias": sorted({item["dependencia"] for item in all_items if item.get("dependencia")}),
        "estados": sorted({item["estado"] for item in all_items if item.get("estado")}),
    }
    return {
        "vigencia": vigencia,
        "periodos": PERIODOS,
        "filtros": filters,
        "resumen": {
            "total": len(items),
            "activos": sum(1 for item in items if _normalizar_texto(item.get("estado")) == "activo"),
            "inactivos": sum(1 for item in items if _normalizar_texto(item.get("estado")) == "inactivo"),
            "avance_promedio": round(sum(advances) / len(advances), 1) if advances else 0,
            "observaciones_oap": oap,
        },
        "items": items,
    }


@router.get("/resumen", summary="Resumen del visor ejecutivo")
async def resumen_comite_directivo(
    vigencia: int = Query(2026, ge=2020, le=2100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    response = await listar_indicadores(
        vigencia=vigencia,
        linea=None,
        dependencia=None,
        estado=None,
        q=None,
        db=db,
    )
    return {"vigencia": vigencia, **response["resumen"]}

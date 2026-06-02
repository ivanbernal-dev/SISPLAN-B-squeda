"""
app/routers/script_pipeline.py

Editor de script Python para el pipeline de indicadores KPI.

Endpoints admin:
  GET  /admin/script-pipeline          → script activo + KPIs actuales
  POST /admin/script-pipeline/save     → guardar script
  POST /admin/script-pipeline/run      → ejecutar (modo prueba o producción)
  GET  /admin/script-pipeline/tables   → tablas de BD con número de filas

Endpoints públicos (sin auth):
  GET  /stats/kpis                     → KPIs nivel 1
  GET  /stats/kpis/{kpi_key}           → KPIs nivel 2 de un padre
"""

import io
import logging
import textwrap
import threading
import traceback
import re
from datetime import datetime, timezone
from typing import Any, Optional

from app.services.pipeline_logger import (
    annotate_script_error,
    pipeline_run,
)

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.kpi import KpiResultado, PipelineScript
from app.routers.auth import get_current_user
from app.models.user import User, UserRole

# ── Helpers de autorización ───────────────────────────────────────────────────

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")
    return current_user


# ── Routers ───────────────────────────────────────────────────────────────────

admin_router = APIRouter(prefix="/admin/script-pipeline", tags=["Script Pipeline"])
public_router = APIRouter(prefix="/stats/kpis", tags=["KPIs Públicos"])


# ── Script de ejemplo ─────────────────────────────────────────────────────────

EJEMPLO_SCRIPT = textwrap.dedent("""\
# ============================================================
# UBPD — Script de Pipeline de Indicadores
# ============================================================
# Variables disponibles al ejecutar:
#   dfs   → dict con un DataFrame por template aprobado
#           Clave: nombre del template | Valor: DataFrame con datos_dinamicos
#   pd    → pandas ya importado
#
# El script debe definir la variable 'resultado' con la estructura:
#
# resultado = {
#     "nivel1": [
#         {"key": "kpi1", "label": "Nombre", "valor": 75.0, "descripcion": "..."},
#         ...  (5 recomendado)
#     ],
#     "nivel2": {
#         "kpi1": [
#             {"key": "kpi1_sub1", "label": "Sub-nombre", "valor": 60.0},
#             ...  (5 recomendado)
#         ]
#     }
# }
# ============================================================

# ── 1. Diagnóstico de datos ───────────────────────────────────
print("=== Datos disponibles ===")
total_registros = 0
for nombre, df in dfs.items():
    print(f"  Template: '{nombre}' → {len(df)} filas, {len(df.columns)} columnas")
    total_registros += len(df)
print(f"\\n  Total registros aprobados: {total_registros}")


# ── 2. Funciones auxiliares ───────────────────────────────────
def calcular_completitud(df):
    # % de campos no nulos en el DataFrame
    if df.empty:
        return 0.0
    total = df.size
    llenos = df.notna().sum().sum()
    return round((llenos / total) * 100, 1) if total else 0.0


# ── 3. Cálculo de KPIs ───────────────────────────────────────
cobertura_valor   = min(100.0, round(total_registros * 2.5, 1))

vals_comp = [calcular_completitud(df) for df in dfs.values() if not df.empty]
completitud_valor = round(sum(vals_comp) / len(vals_comp), 1) if vals_comp else 0.0

oportunidad_valor = 0.0
calidad_valor     = 0.0
gestion_valor     = 0.0

print("\\n=== Resultados ===")
print(f"  Cobertura:   {cobertura_valor}%")
print(f"  Completitud: {completitud_valor}%")
print(f"  Oportunidad: {oportunidad_valor}%")
print(f"  Calidad:     {calidad_valor}%")
print(f"  Gestión:     {gestion_valor}%")


# ── 4. Definir resultado ──────────────────────────────────────
resultado = {
    "nivel1": [
        {"key": "kpi_cobertura",   "label": "Cobertura",   "valor": cobertura_valor,   "descripcion": "Cobertura institucional de los registros"},
        {"key": "kpi_completitud", "label": "Completitud", "valor": completitud_valor, "descripcion": "Completitud promedio de los campos"},
        {"key": "kpi_oportunidad", "label": "Oportunidad", "valor": oportunidad_valor, "descripcion": "Oportunidad en la entrega de información"},
        {"key": "kpi_calidad",     "label": "Calidad",     "valor": calidad_valor,     "descripcion": "Calidad de los datos registrados"},
        {"key": "kpi_gestion",     "label": "Gestión",     "valor": gestion_valor,     "descripcion": "Eficiencia en la gestión documental"},
    ],
    "nivel2": {
        "kpi_cobertura": [
            {"key": "kpi_cob_regional",      "label": "Regional",       "valor": 0.0},
            {"key": "kpi_cob_poblacional",   "label": "Poblacional",    "valor": 0.0},
            {"key": "kpi_cob_territorial",   "label": "Territorial",    "valor": 0.0},
            {"key": "kpi_cob_institucional", "label": "Institucional",  "valor": 0.0},
            {"key": "kpi_cob_tematica",      "label": "Temática",       "valor": 0.0},
        ],
        "kpi_completitud": [
            {"key": "kpi_comp_campos",      "label": "Campos básicos",  "valor": completitud_valor},
            {"key": "kpi_comp_adjuntos",    "label": "Adjuntos",        "valor": 0.0},
            {"key": "kpi_comp_firmas",      "label": "Firmas",          "valor": 0.0},
            {"key": "kpi_comp_fechas",      "label": "Fechas",          "valor": 0.0},
            {"key": "kpi_comp_referencias", "label": "Referencias",     "valor": 0.0},
        ],
        "kpi_oportunidad": [
            {"key": "kpi_op_entrega",       "label": "Entrega a tiempo",     "valor": 0.0},
            {"key": "kpi_op_validacion",    "label": "Validación oportuna",  "valor": 0.0},
            {"key": "kpi_op_respuesta",     "label": "Tiempo de respuesta",  "valor": 0.0},
            {"key": "kpi_op_actualizacion", "label": "Actualización",        "valor": 0.0},
            {"key": "kpi_op_seguimiento",   "label": "Seguimiento",          "valor": 0.0},
        ],
        "kpi_calidad": [
            {"key": "kpi_cal_exactitud",    "label": "Exactitud",      "valor": 0.0},
            {"key": "kpi_cal_coherencia",   "label": "Coherencia",     "valor": 0.0},
            {"key": "kpi_cal_consistencia", "label": "Consistencia",   "valor": 0.0},
            {"key": "kpi_cal_validez",      "label": "Validez",        "valor": 0.0},
            {"key": "kpi_cal_integridad",   "label": "Integridad",     "valor": 0.0},
        ],
        "kpi_gestion": [
            {"key": "kpi_ges_proceso",      "label": "Proceso",         "valor": 0.0},
            {"key": "kpi_ges_recursos",     "label": "Recursos",        "valor": 0.0},
            {"key": "kpi_ges_resultado",    "label": "Resultados",      "valor": 0.0},
            {"key": "kpi_ges_impacto",      "label": "Impacto",         "valor": 0.0},
            {"key": "kpi_ges_mejora",       "label": "Mejora continua", "valor": 0.0},
        ],
    },
}

print("\\n✓ Script ejecutado correctamente")
""")


# ── Schemas ───────────────────────────────────────────────────────────────────

class ScriptSaveBody(BaseModel):
    codigo: str
    nombre: str = "Pipeline Principal"


class ScriptRunBody(BaseModel):
    codigo: str
    modo: str = "test"  # "test" | "produccion"


class KpiOut(BaseModel):
    key: str
    label: str
    valor: float
    descripcion: str | None = None
    nivel1_key: str | None = None
    updated_at: datetime | None = None


# ── Ejecución del script ──────────────────────────────────────────────────────

def _run_script_sync(code: str, dfs: dict) -> dict[str, Any]:
    """Ejecuta el script en un hilo con captura de stdout y timeout de 60s."""
    output_lines: list[str] = []
    result_holder: dict[str, Any] = {}

    def captured_print(*args, **kwargs):
        sep = kwargs.get("sep", " ")
        end = kwargs.get("end", "\n")
        output_lines.append(sep.join(str(a) for a in args) + end)

    try:
        import pandas as pd  # noqa: F401
        import numpy as np   # noqa: F401
    except ImportError:
        pass

    import builtins as _builtins

    safe_builtins: dict = {
        "print": captured_print,
        "len": len, "range": range, "enumerate": enumerate,
        "zip": zip, "sum": sum, "min": min, "max": max,
        "abs": abs, "round": round, "sorted": sorted, "reversed": reversed,
        "list": list, "dict": dict, "set": set, "tuple": tuple,
        "str": str, "int": int, "float": float, "bool": bool,
        "isinstance": isinstance, "type": type, "hasattr": hasattr,
        "getattr": getattr, "setattr": setattr, "vars": vars, "dir": dir,
        "map": map, "filter": filter, "any": any, "all": all,
        "format": format, "repr": repr, "frozenset": frozenset,
        "object": object, "super": super, "property": property,
        "staticmethod": staticmethod, "classmethod": classmethod,
        "True": True, "False": False, "None": None,
        # __build_class__ es indispensable para ejecutar sentencias `class`
        "__build_class__": _builtins.__build_class__,
        "__name__": "__pipeline__",
        "__import__": __import__,
    }

    import sys
    globals_env: dict[str, Any] = {
        "__builtins__": safe_builtins,
        "dfs": dfs.get("dfs", dfs) if (isinstance(dfs, dict) and "dfs" in dfs) else dfs,
        "template_meta": dfs.get("meta", {}) if (isinstance(dfs, dict) and "meta" in dfs) else {},
    }
    # Inject available libs
    for lib_name in ("pandas", "numpy", "math", "re", "json", "datetime", "collections"):
        try:
            globals_env[lib_name.split(".")[0]] = __import__(lib_name)
        except ImportError:
            pass
    globals_env["pd"] = globals_env.get("pandas")
    globals_env["np"] = globals_env.get("numpy")

    def _exec():
        try:
            exec(compile(code, "<pipeline_script>", "exec"), globals_env)
            result_holder["resultado"] = globals_env.get("resultado")
            result_holder["error"] = None
        except Exception:
            result_holder["error"] = traceback.format_exc()
            result_holder["resultado"] = None

    thread = threading.Thread(target=_exec, daemon=True)
    thread.start()
    thread.join(timeout=60)

    if thread.is_alive():
        result_holder["error"] = "⏱ Timeout: el script tardó más de 60 segundos."
        result_holder["resultado"] = None

    return {
        "stdout": "".join(output_lines),
        "error": result_holder.get("error"),
        "resultado": result_holder.get("resultado"),
    }


async def _load_dataframes(
    db: AsyncSession,
    plog: logging.Logger | None = None,
) -> tuple[dict, dict]:
    """Carga formularios aprobados como DataFrames y metadatos de templates.

    Si se pasa `plog`, registra detalle de qué se cargó (templates, filas,
    columnas) para que cualquier discrepancia entre datos esperados y datos
    procesados quede explícita en el log.
    """
    try:
        import pandas as pd
    except ImportError:
        if plog: plog.error("pandas no está disponible en el contenedor")
        return {}, {}

    from app.models.form import Form, FormStatus
    from app.models.template import Template

    if plog: plog.info("Cargando formularios APROBADOS desde la BD...")
    rows = await db.execute(
        select(
            Form.datos_dinamicos,
            Template.nombre.label("template_nombre"),
            Template.id.label("template_id"),
            Template.codigo.label("template_codigo"),
        )
        .join(Template, Form.plantilla_id == Template.id)
        .where(Form.estado == FormStatus.approved)
    )
    grouped: dict[str, list] = {}
    meta: dict[str, dict] = {}
    total_rows = 0
    for datos, nombre, tid, codigo in rows.all():
        key = codigo or nombre
        grouped.setdefault(key, []).append(datos or {})
        meta[key] = {"id": str(tid), "nombre": nombre, "codigo": codigo}
        total_rows += 1

    dfs = {name: pd.DataFrame(rs) for name, rs in grouped.items()}

    if plog:
        plog.info("Templates con datos: %d | filas totales aprobadas: %d",
                  len(dfs), total_rows)
        for tkey, df in sorted(dfs.items()):
            plog.info("  · %s → %d filas, %d columnas", tkey, len(df), len(df.columns))
        if not dfs:
            plog.warning("No hay formularios aprobados en la BD: el pipeline "
                         "no tendrá datos sobre los cuales calcular KPIs.")
    return dfs, meta


async def _get_active_script(db: AsyncSession) -> PipelineScript | None:
    result = await db.execute(
        select(PipelineScript).where(PipelineScript.activo == True).limit(1)
    )
    return result.scalar_one_or_none()


# ── Admin: GET script activo ──────────────────────────────────────────────────

@admin_router.get("")
async def get_script(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    script = await _get_active_script(db)
    if script:
        codigo, nombre = script.codigo, script.nombre
    else:
        # Fallback: leer el PAI default del filesystem del backend en vez de
        # caer en EJEMPLO_SCRIPT (genérico). Si tampoco existe el seed,
        # usar el ejemplo.
        from pathlib import Path
        seed = Path(__file__).resolve().parent.parent / "seeds" / "pipeline_pai_default.py"
        if seed.exists():
            codigo = seed.read_text(encoding="utf-8")
            nombre = "Pipeline PAI 2026 (default)"
        else:
            codigo, nombre = EJEMPLO_SCRIPT, "Pipeline Principal"

    # KPIs actuales
    kpis_res = await db.execute(
        select(KpiResultado).order_by(KpiResultado.nivel, KpiResultado.kpi_key)
    )
    kpis = kpis_res.scalars().all()

    return {
        "nombre": nombre,
        "codigo": codigo,
        "kpis": [
            {
                "key": k.kpi_key, "label": k.kpi_label, "valor": k.valor,
                "nivel": k.nivel, "nivel1_key": k.nivel1_key,
                "updated_at": k.updated_at.isoformat() if k.updated_at else None,
            }
            for k in kpis
        ],
    }


# ── Admin: POST guardar script ────────────────────────────────────────────────

@admin_router.post("/save")
async def save_script(
    body: ScriptSaveBody,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    script = await _get_active_script(db)
    if script:
        script.codigo = body.codigo
        script.nombre = body.nombre
        script.updated_at = datetime.now(timezone.utc)
    else:
        script = PipelineScript(codigo=body.codigo, nombre=body.nombre)
        db.add(script)
    await db.commit()
    return {"ok": True, "mensaje": "Script guardado correctamente"}


# ── Admin: POST ejecutar script ───────────────────────────────────────────────

@admin_router.post("/run")
async def run_script(
    body: ScriptRunBody,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_admin_user),
):
    with pipeline_run(mode=body.modo, user=current.username or current.email) as plog:
        plog.info("Script recibido: %d caracteres", len(body.codigo or ""))

        # En modo PRODUCCIÓN siempre se ejecuta el script ACTIVO de la BD,
        # NO lo que viene en el body. Esto evita que alguien ejecute por
        # accidente un script viejo / de prueba en producción y machaque
        # los KPIs que estaban bien (caso real: el editor cargó el ejemplo
        # genérico y al pulsar Ejecutar borró las 6 líneas del PAI).
        # En modo "test" se sigue ejecutando lo del body (para validar
        # cambios antes de guardar).
        code_to_run = body.codigo
        editor_difiere_de_activo = False
        active_nombre = None
        if body.modo == "produccion":
            active = await _get_active_script(db)
            if active and active.codigo:
                code_to_run = active.codigo
                active_nombre = active.nombre
                if code_to_run != body.codigo:
                    editor_difiere_de_activo = True
                    plog.warning(
                        "modo=produccion: ignorando el código del editor y usando "
                        "el script ACTIVO en BD ('%s', %d chars). Para que tus "
                        "cambios surtan efecto, GUARDA primero y luego Ejecuta.",
                        active.nombre, len(active.codigo),
                    )
            else:
                plog.error("modo=produccion sin script activo en BD — abortando")
                return {
                    "ok": False,
                    "stdout": "",
                    "stderr": "No hay un script activo guardado en la BD. Guarda primero (botón Guardar) y luego ejecuta.",
                    "modo": body.modo,
                    "guardado": False,
                    "log_file": str(getattr(plog, "run_file", "")),
                }

        dfs, template_meta = await _load_dataframes(db, plog=plog)
        combined = {"dfs": dfs, "meta": template_meta}

        plog.info("Ejecutando script (timeout 60s)...")
        result = _run_script_sync(code_to_run, combined)

        output = result["stdout"]
        error = result["error"]
        resultado = result["resultado"]

        if output:
            plog.info("STDOUT del script (%d chars):\n%s",
                      len(output), output[:4000])

        if error:
            annotated = annotate_script_error(code_to_run, error)
            plog.error("El script falló:\n%s", annotated)
            return {
                "ok": False,
                "stdout": output,
                "stderr": annotated,
                "modo": body.modo,
                "guardado": False,
                "log_file": str(getattr(plog, "run_file", "")),
            }

        # Validar estructura de resultado
        if body.modo == "produccion":
            if not isinstance(resultado, dict) or "nivel1" not in resultado:
                plog.error("La variable `resultado` no tiene la estructura esperada "
                           "({nivel1:[...], nivel2:{...}}). Se recibió: %s",
                           type(resultado).__name__)
                return {
                    "ok": False,
                    "stdout": output,
                    "stderr": "Error: la variable 'resultado' no tiene la estructura esperada ({nivel1: [...], nivel2: {...}}).",
                    "modo": body.modo,
                    "guardado": False,
                    "log_file": str(getattr(plog, "run_file", "")),
                }
            # Guardar en BD
            try:
                import json as _json

                def _payload(item: dict) -> str | None:
                    extra = {k: v for k, v in item.items()
                             if k in ("anual", "por_trimestre", "n_forms")}
                    return _json.dumps(extra, ensure_ascii=False) if extra else None

                nivel1_items = resultado.get("nivel1", [])
                nivel2_map = resultado.get("nivel2", {})
                plog.info("Guardando KPIs: nivel1=%d, nivel2_grupos=%d (total nivel2=%d)",
                          len(nivel1_items), len(nivel2_map),
                          sum(len(v) for v in nivel2_map.values()))

                for item in nivel1_items:
                    key = item.get("key", "")
                    existing = await db.execute(
                        select(KpiResultado).where(KpiResultado.kpi_key == key)
                    )
                    kpi = existing.scalar_one_or_none()
                    if kpi:
                        kpi.kpi_label = item.get("label", key)
                        kpi.valor = float(item.get("valor", 0.0))
                        kpi.descripcion = item.get("descripcion")
                        kpi.payload_json = _payload(item)
                        kpi.updated_at = datetime.now(timezone.utc)
                    else:
                        db.add(KpiResultado(
                            nivel=1, kpi_key=key,
                            kpi_label=item.get("label", key),
                            valor=float(item.get("valor", 0.0)),
                            descripcion=item.get("descripcion"),
                            payload_json=_payload(item),
                        ))
                    plog.info("  · N1 %s = %.2f", key, float(item.get("valor", 0.0)))

                for parent_key, sub_items in nivel2_map.items():
                    for item in sub_items:
                        key = item.get("key", "")
                        existing = await db.execute(
                            select(KpiResultado).where(KpiResultado.kpi_key == key)
                        )
                        kpi = existing.scalar_one_or_none()
                        tid = item.get("template_id")
                        if kpi:
                            kpi.kpi_label = item.get("label", key)
                            kpi.valor = float(item.get("valor", 0.0))
                            kpi.nivel1_key = parent_key
                            kpi.payload_json = _payload(item)
                            if tid:
                                kpi.template_id = str(tid)
                            kpi.updated_at = datetime.now(timezone.utc)
                        else:
                            db.add(KpiResultado(
                                nivel=2, kpi_key=key,
                                kpi_label=item.get("label", key),
                                valor=float(item.get("valor", 0.0)),
                                nivel1_key=parent_key,
                                template_id=str(tid) if tid else None,
                                payload_json=_payload(item),
                            ))

                await db.commit()
                plog.info("Persistencia OK: %d nivel-1 + %d nivel-2 guardados.",
                          len(nivel1_items),
                          sum(len(v) for v in nivel2_map.values()))
                # Aviso destacado si el editor tenía contenido distinto al
                # script activo (frecuente: el usuario editó pero no guardó).
                if editor_difiere_de_activo:
                    output = (
                        "⚠️  AVISO: tu editor tiene cambios SIN GUARDAR.\n"
                        f"   Se ejecutó el script ACTIVO guardado ('{active_nombre}'),\n"
                        "   NO lo que tienes en pantalla. Para correr tus cambios:\n"
                        "     1) Pulsa 'Guardar'\n"
                        "     2) Vuelve a pulsar 'Ejecutar en producción'\n\n"
                    ) + output
                output += f"\n\n✅ Producción: {len(nivel1_items)} KPIs nivel-1 y {sum(len(v) for v in nivel2_map.values())} KPIs nivel-2 guardados en la base de datos."
                output += f"\n📝 Script ejecutado: '{active_nombre or 'Pipeline'}'"
                output += f"\n📝 Log: {getattr(plog, 'run_file', '')}"
                # Resumen explícito de los primeros KPIs guardados (para que
                # el operador vea de un vistazo los valores que quedaron).
                preview = []
                for it in nivel1_items[:6]:
                    preview.append(f"   N1  {it.get('key',''):4s} = {float(it.get('valor',0)):.2f}%")
                if preview:
                    output += "\n\n📊 KPIs nivel-1 guardados:\n" + "\n".join(preview)
                return {
                    "ok": True, "stdout": output, "stderr": None,
                    "modo": body.modo, "guardado": True,
                    "editor_difiere_de_activo": editor_difiere_de_activo,
                    "script_activo_nombre": active_nombre,
                    "log_file": str(getattr(plog, "run_file", "")),
                }

            except Exception as exc:
                await db.rollback()
                plog.exception("Falló la persistencia de KPIs en BD")
                return {
                    "ok": False,
                    "stdout": output,
                    "stderr": f"Error guardando en BD: {exc}",
                    "modo": body.modo,
                    "guardado": False,
                    "log_file": str(getattr(plog, "run_file", "")),
                }

        # Modo prueba: solo devolver output (sin persistir)
        plog.info("Modo prueba — KPIs NO se guardan en BD")
        return {
            "ok": True,
            "stdout": output,
            "stderr": None,
            "modo": body.modo,
            "guardado": False,
            "resultado_preview": resultado,
            "log_file": str(getattr(plog, "run_file", "")),
        }


# ── Admin: GET tablas de BD ───────────────────────────────────────────────────

@admin_router.get("/tables")
async def list_tables(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    query = text("""
        SELECT
            t.table_name,
            COALESCE(s.n_live_tup, 0) AS row_estimate,
            pg_size_pretty(pg_total_relation_size(quote_ident(t.table_name))) AS size
        FROM information_schema.tables t
        LEFT JOIN pg_stat_user_tables s ON s.relname = t.table_name
        WHERE t.table_schema = 'public'
          AND t.table_type = 'BASE TABLE'
        ORDER BY s.n_live_tup DESC NULLS LAST, t.table_name
    """)
    result = await db.execute(query)
    rows = result.fetchall()
    return [
        {"tabla": row[0], "filas": int(row[1]), "tamaño": row[2]}
        for row in rows
    ]


# ── Público: GET KPIs nivel 1 ─────────────────────────────────────────────────

# Mapping from nivel1 kpi_key → line prefix used in Template.codigo
_LINEA_KEY_TO_PREFIX = {
    "kpi_linea1": "L1",
    "kpi_linea2": "L2",
    "kpi_linea3": "L3",
    "kpi_linea4": "L4",
    "kpi_linea5": "L5",
}

_PERIODO_TRIM = {
    "trim1": "TRIMESTRE 1", "trim2": "TRIMESTRE 2",
    "trim3": "TRIMESTRE 3", "trim4": "TRIMESTRE 4",
    "t1":    "TRIMESTRE 1", "t2":    "TRIMESTRE 2",
    "t3":    "TRIMESTRE 3", "t4":    "TRIMESTRE 4",
}


def _valor_por_periodo(kpi: KpiResultado, periodo: str | None) -> tuple[float, dict | None]:
    """
    Dado un KpiResultado y un período (None|anual|trim1..trim4) devuelve
    (valor, payload_dict). Si no hay payload_json o el período no aplica,
    devuelve el valor plano original.

    Si el payload trae `pct: None` (significa "Sin Reporte" — el pipeline
    omitió actividades sin proyección) devuelve 0.0 para no romper el
    velocímetro, pero conserva el payload para que la UI pueda mostrar el
    estado "Sin Reporte" si lo necesita.
    """
    import json as _json

    def _num(v, fallback=0.0):
        if v is None:
            return float(fallback)
        try:
            return float(v)
        except (TypeError, ValueError):
            return float(fallback)

    payload = None
    if kpi.payload_json:
        try:
            payload = _json.loads(kpi.payload_json)
        except Exception:
            payload = None

    if not payload:
        return (_num(kpi.valor), None)

    if periodo in (None, "anual", "year", ""):
        anual = payload.get("anual") or {}
        return (_num(anual.get("pct"), fallback=_num(kpi.valor)), payload)

    trim_key = _PERIODO_TRIM.get((periodo or "").lower())
    if not trim_key:
        return (_num(kpi.valor), payload)

    pt = (payload.get("por_trimestre") or {}).get(trim_key) or {}
    return (_num(pt.get("pct")), payload)


@public_router.get("")
async def get_kpis_nivel1(
    periodo: Optional[str] = Query(None, description="anual | trim1 | trim2 | trim3 | trim4"),
    db: AsyncSession = Depends(get_db),
):
    """
    KPIs nivel 1 (Línea Estratégica) — velocímetros del primer nivel.

    ?periodo=anual            → ratio acumulado año (default)
    ?periodo=trim1..trim4     → % avance ponderado de ese trimestre
    """
    result = await db.execute(
        select(KpiResultado)
        .where(KpiResultado.nivel == 1, KpiResultado.activo.isnot(False))
        .order_by(KpiResultado.kpi_key)
    )
    kpis = result.scalars().all()

    if not kpis:
        defaults = [
            ("L1", "Línea 1 — Investigación Humanitaria y Extrajudicial", ""),
            ("L2", "Línea 2 — Memoria y Legado", ""),
            ("L3", "Línea 3 — Articulación Interinstitucional", ""),
            ("L4", "Línea 4 — Comunicaciones y Pedagogía", ""),
            ("L5", "Línea 5 — Participación de Familias y Personas Buscadoras", ""),
            ("L6", "Línea 6 — Soporte Estratégico y Operativo", ""),
        ]
        return [{"key": k, "label": l, "valor": 0.0, "descripcion": d, "updated_at": None,
                 "periodo": periodo or "anual"} for k, l, d in defaults]

    items = []
    for k in kpis:
        valor, payload = _valor_por_periodo(k, periodo)
        items.append({
            "key": k.kpi_key, "label": k.kpi_label,
            "valor": valor,
            "descripcion": k.descripcion,
            "periodo": periodo or "anual",
            "anual": (payload or {}).get("anual"),
            "por_trimestre": (payload or {}).get("por_trimestre"),
            "updated_at": k.updated_at.isoformat() if k.updated_at else None,
        })
    return items


# ── Público: GET formularios aprobados de un KPI nivel 2 ─────────────────────

@public_router.get("/{kpi_key}/forms")
async def get_kpi_forms(
    kpi_key: str,
    page: int = 1,
    size: int = 20,
    periodo: Optional[str] = Query(None, description="anual | trim1 | trim2 | trim3 | trim4"),
    db: AsyncSession = Depends(get_db),
):
    """Devuelve formularios aprobados asociados al template de este sub-KPI.

    Filtra por trimestre (`periodo_reporte` en datos_dinamicos) o muestra
    todos los registros del año si periodo es 'anual' o None.
    """
    from app.models.form import Form, FormStatus
    from app.models.template import Template
    from sqlalchemy import and_, func as sqlfunc
    import uuid as _uuid

    # Buscar template_id del KPI. Si el script no lo guardó, hacer fallback por
    # código (kpi_key suele coincidir con Template.codigo en el PAI).
    kpi_res = await db.execute(
        select(KpiResultado).where(KpiResultado.kpi_key == kpi_key)
    )
    kpi = kpi_res.scalar_one_or_none()
    template_id = kpi.template_id if kpi else None
    if not template_id:
        tpl_lookup = await db.execute(select(Template.id).where(Template.codigo == kpi_key))
        template_id = tpl_lookup.scalar_one_or_none()
    if not template_id:
        return {"total": 0, "page": page, "size": size, "items": [],
                "kpi_label": kpi.kpi_label if kpi else kpi_key, "template_nombre": None}
    # Asegurar UUID (puede venir como str del KpiResultado)
    if isinstance(template_id, str):
        try:
            template_id = _uuid.UUID(template_id)
        except ValueError:
            return {"total": 0, "page": page, "size": size, "items": [],
                    "kpi_label": kpi.kpi_label if kpi else kpi_key, "template_nombre": None}

    base_filters = [Form.plantilla_id == template_id, Form.estado == FormStatus.approved]
    # Filtro por trimestre: revisa datos_dinamicos->>'periodo_reporte'
    periodo_norm = (periodo or "anual").lower()
    trim_value = _PERIODO_TRIM.get(periodo_norm)
    if trim_value:
        base_filters.append(
            Form.datos_dinamicos["periodo_reporte"].astext == trim_value
        )

    total = await db.scalar(
        select(sqlfunc.count(Form.id)).where(and_(*base_filters))
    ) or 0

    rows = await db.execute(
        select(Form)
        .where(and_(*base_filters))
        .order_by(Form.fecha_carga.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    forms = rows.scalars().all()

    # Nombre del template
    tmpl_res = await db.execute(select(Template.nombre).where(Template.id == template_id))
    template_nombre = tmpl_res.scalar_one_or_none()

    return {
        "total": total,
        "page": page,
        "size": size,
        "kpi_label": kpi.kpi_label if kpi else kpi_key,
        "template_nombre": template_nombre,
        "template_id": template_id,
        "items": [
            {
                "id": str(f.id),
                "dependency": f.dependency.nombre if f.dependency else "—",
                "usuario": f.usuario.nombre_completo if f.usuario else "—",
                "fecha_carga": f.fecha_carga.isoformat() if f.fecha_carga else None,
                "fecha_usuario": str(f.fecha_usuario) if f.fecha_usuario else None,
                "datos_dinamicos": f.datos_dinamicos,
                "estado": f.estado.value,
            }
            for f in forms
        ],
    }


# ── Público: GET KPIs nivel 2 por padre ──────────────────────────────────────

@public_router.get("/{kpi_key}")
async def get_kpis_nivel2(
    kpi_key: str,
    periodo: Optional[str] = Query(None, description="anual | trim1 | trim2 | trim3 | trim4"),
    db: AsyncSession = Depends(get_db),
):
    """
    KPIs nivel 2 (Producto) — velocímetros del segundo nivel para una línea.

    Acepta el mismo `?periodo=` que el endpoint nivel 1.
    """
    result = await db.execute(
        select(KpiResultado)
        .where(
            KpiResultado.nivel == 2,
            KpiResultado.nivel1_key == kpi_key,
            KpiResultado.activo.isnot(False),
        )
        .order_by(KpiResultado.kpi_key)
    )
    kpis = result.scalars().all()
    if not kpis:
        return []

    items = []
    for k in kpis:
        valor, payload = _valor_por_periodo(k, periodo)
        items.append({
            "key": k.kpi_key, "label": k.kpi_label,
            "valor": valor,
            "nivel1_key": k.nivel1_key,
            "template_id": k.template_id,
            "periodo": periodo or "anual",
            "anual": (payload or {}).get("anual"),
            "por_trimestre": (payload or {}).get("por_trimestre"),
            "updated_at": k.updated_at.isoformat() if k.updated_at else None,
        })
    return items

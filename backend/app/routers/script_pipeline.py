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
import textwrap
import threading
import traceback
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
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
    \\"\\"\\"% de campos no nulos en el DataFrame.\\"\\"\\"
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

    safe_builtins: dict = {
        "print": captured_print,
        "len": len, "range": range, "enumerate": enumerate,
        "zip": zip, "sum": sum, "min": min, "max": max,
        "abs": abs, "round": round, "sorted": sorted, "reversed": reversed,
        "list": list, "dict": dict, "set": set, "tuple": tuple,
        "str": str, "int": int, "float": float, "bool": bool,
        "isinstance": isinstance, "type": type, "hasattr": hasattr,
        "getattr": getattr, "vars": vars, "dir": dir,
        "True": True, "False": False, "None": None,
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


async def _load_dataframes(db: AsyncSession) -> tuple[dict, dict]:
    """Carga formularios aprobados como DataFrames y metadatos de templates."""
    try:
        import pandas as pd
    except ImportError:
        return {}, {}

    from app.models.form import Form, FormStatus
    from app.models.template import Template

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
    for datos, nombre, tid, codigo in rows.all():
        grouped.setdefault(nombre, []).append(datos or {})
        meta[nombre] = {"id": str(tid), "nombre": nombre, "codigo": codigo}

    dfs = {name: pd.DataFrame(rows) for name, rows in grouped.items()}
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
    codigo = script.codigo if script else EJEMPLO_SCRIPT
    nombre = script.nombre if script else "Pipeline Principal"

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
    _: User = Depends(get_admin_user),
):
    dfs, template_meta = await _load_dataframes(db)
    combined = {"dfs": dfs, "meta": template_meta}
    result = _run_script_sync(body.codigo, combined)

    output = result["stdout"]
    error = result["error"]
    resultado = result["resultado"]

    if error:
        return {
            "ok": False,
            "stdout": output,
            "stderr": error,
            "modo": body.modo,
            "guardado": False,
        }

    # Validar estructura de resultado
    if body.modo == "produccion":
        if not isinstance(resultado, dict) or "nivel1" not in resultado:
            return {
                "ok": False,
                "stdout": output,
                "stderr": "Error: la variable 'resultado' no tiene la estructura esperada ({nivel1: [...], nivel2: {...}}).",
                "modo": body.modo,
                "guardado": False,
            }
        # Guardar en BD
        try:
            nivel1_items = resultado.get("nivel1", [])
            nivel2_map = resultado.get("nivel2", {})

            # Upsert nivel 1
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
                    kpi.updated_at = datetime.now(timezone.utc)
                else:
                    db.add(KpiResultado(
                        nivel=1, kpi_key=key,
                        kpi_label=item.get("label", key),
                        valor=float(item.get("valor", 0.0)),
                        descripcion=item.get("descripcion"),
                    ))

            # Upsert nivel 2
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
                        ))

            await db.commit()
            output += f"\n\n✅ Producción: {len(nivel1_items)} KPIs nivel-1 y {sum(len(v) for v in nivel2_map.values())} KPIs nivel-2 guardados en la base de datos."
            return {"ok": True, "stdout": output, "stderr": None, "modo": body.modo, "guardado": True}

        except Exception as exc:
            await db.rollback()
            return {
                "ok": False,
                "stdout": output,
                "stderr": f"Error guardando en BD: {exc}",
                "modo": body.modo,
                "guardado": False,
            }

    # Modo prueba: solo devolver output
    return {
        "ok": True,
        "stdout": output,
        "stderr": None,
        "modo": body.modo,
        "guardado": False,
        "resultado_preview": resultado,
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

@public_router.get("")
async def get_kpis_nivel1(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KpiResultado)
        .where(KpiResultado.nivel == 1)
        .order_by(KpiResultado.kpi_key)
    )
    kpis = result.scalars().all()

    # Si no hay KPIs en BD, devolver los 5 por defecto con valor 0
    if not kpis:
        defaults = [
            ("kpi_cobertura",   "Cobertura",   "Cobertura institucional de los registros"),
            ("kpi_completitud", "Completitud", "Completitud promedio de los campos"),
            ("kpi_oportunidad", "Oportunidad", "Oportunidad en la entrega de información"),
            ("kpi_calidad",     "Calidad",     "Calidad de los datos registrados"),
            ("kpi_gestion",     "Gestión",     "Eficiencia en la gestión documental"),
        ]
        return [
            {"key": k, "label": l, "valor": 0.0, "descripcion": d, "updated_at": None}
            for k, l, d in defaults
        ]

    return [
        {
            "key": k.kpi_key, "label": k.kpi_label, "valor": k.valor,
            "descripcion": k.descripcion,
            "updated_at": k.updated_at.isoformat() if k.updated_at else None,
        }
        for k in kpis
    ]


# ── Público: GET formularios aprobados de un KPI nivel 2 ─────────────────────

@public_router.get("/{kpi_key}/forms")
async def get_kpi_forms(
    kpi_key: str,
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Devuelve formularios aprobados asociados al template de este sub-KPI."""
    from app.models.form import Form, FormStatus
    from app.models.template import Template

    # Buscar template_id del KPI
    kpi_res = await db.execute(
        select(KpiResultado).where(KpiResultado.kpi_key == kpi_key)
    )
    kpi = kpi_res.scalar_one_or_none()
    if not kpi or not kpi.template_id:
        return {"total": 0, "page": page, "size": size, "items": [], "kpi_label": kpi_key, "template_nombre": None}

    from sqlalchemy import func as sqlfunc

    total = await db.scalar(
        select(sqlfunc.count(Form.id))
        .where(Form.plantilla_id == kpi.template_id, Form.estado == FormStatus.approved)
    ) or 0

    rows = await db.execute(
        select(Form)
        .where(Form.plantilla_id == kpi.template_id, Form.estado == FormStatus.approved)
        .order_by(Form.fecha_carga.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    forms = rows.scalars().all()

    # Nombre del template
    tmpl_res = await db.execute(select(Template.nombre).where(Template.id == kpi.template_id))
    template_nombre = tmpl_res.scalar_one_or_none()

    return {
        "total": total,
        "page": page,
        "size": size,
        "kpi_label": kpi.kpi_label,
        "template_nombre": template_nombre,
        "template_id": kpi.template_id,
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
async def get_kpis_nivel2(kpi_key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KpiResultado)
        .where(KpiResultado.nivel == 2, KpiResultado.nivel1_key == kpi_key)
        .order_by(KpiResultado.kpi_key)
    )
    kpis = result.scalars().all()

    # Defaults nivel 2 por padre
    NIVEL2_DEFAULTS: dict[str, list] = {
        "kpi_cobertura":   [("Regional", "kpi_cob_regional"), ("Poblacional", "kpi_cob_poblacional"), ("Territorial", "kpi_cob_territorial"), ("Institucional", "kpi_cob_institucional"), ("Temática", "kpi_cob_tematica")],
        "kpi_completitud": [("Campos básicos", "kpi_comp_campos"), ("Adjuntos", "kpi_comp_adjuntos"), ("Firmas", "kpi_comp_firmas"), ("Fechas", "kpi_comp_fechas"), ("Referencias", "kpi_comp_referencias")],
        "kpi_oportunidad": [("Entrega a tiempo", "kpi_op_entrega"), ("Validación oportuna", "kpi_op_validacion"), ("Tiempo de respuesta", "kpi_op_respuesta"), ("Actualización", "kpi_op_actualizacion"), ("Seguimiento", "kpi_op_seguimiento")],
        "kpi_calidad":     [("Exactitud", "kpi_cal_exactitud"), ("Coherencia", "kpi_cal_coherencia"), ("Consistencia", "kpi_cal_consistencia"), ("Validez", "kpi_cal_validez"), ("Integridad", "kpi_cal_integridad")],
        "kpi_gestion":     [("Proceso", "kpi_ges_proceso"), ("Recursos", "kpi_ges_recursos"), ("Resultados", "kpi_ges_resultado"), ("Impacto", "kpi_ges_impacto"), ("Mejora continua", "kpi_ges_mejora")],
    }

    if not kpis:
        sub_defaults = NIVEL2_DEFAULTS.get(kpi_key, [])
        return [
            {"key": k, "label": l, "valor": 0.0, "nivel1_key": kpi_key, "updated_at": None}
            for l, k in sub_defaults
        ]

    return [
        {
            "key": k.kpi_key, "label": k.kpi_label, "valor": k.valor,
            "nivel1_key": k.nivel1_key,
            "updated_at": k.updated_at.isoformat() if k.updated_at else None,
        }
        for k in kpis
    ]

"""
app/routers/test_data.py — Seed y limpieza de datos de prueba E2E.

POST   /admin/test-data/seed     → crea usuarios, templates, formularios aprobados/rechazados
DELETE /admin/test-data/clean    → elimina todos los datos marcados con TEST_E2E
GET    /admin/test-data/status   → estado actual de datos de prueba
POST   /admin/test-data/install-script → guarda el script de prueba en el editor de pipeline
"""
import random
import textwrap
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.dependency import Dependency
from app.models.form import Form, FormStatus
from app.models.kpi import PipelineScript
from app.models.template import Template
from app.models.user import User, UserRole
from app.routers.auth import get_current_user
from app.services.auth_service import hash_password

TEST_MARKER = "[TEST_E2E]"
TEST_DEP_CODE = "TEST_E2E_DEP"
TEST_USER_PREFIX = "test_e2e_"
TEST_TMPL_PREFIX = "TEST_E2E_"

router = APIRouter(prefix="/admin/test-data", tags=["Test Data E2E"])


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")
    return current_user


# ── Script de prueba que se instala en el editor ──────────────────────────────

def _build_test_pipeline_script(template_names: list[str]) -> str:
    names_repr = repr(template_names)
    return textwrap.dedent(f"""\
# ============================================================
# UBPD — Script Pipeline de PRUEBA E2E
# Procesa {len(template_names)} templates de prueba y calcula KPIs
# ============================================================
# Variables disponibles:
#   dfs           → dict nombre_template → DataFrame (formularios aprobados)
#   template_meta → dict nombre_template → {{id, nombre, codigo}}
#   pd            → pandas
# ============================================================

TEST_MARKER = "{TEST_MARKER}"
TEST_TEMPLATE_NAMES = {names_repr}

print("=== PIPELINE DE PRUEBA E2E ===")
print(f"Templates disponibles: {{list(dfs.keys())}}")
print()

# ── Filtrar solo templates de prueba ────────────────────────
test_dfs = {{name: df for name, df in dfs.items() if TEST_MARKER in name}}
print(f"Templates de prueba encontrados: {{len(test_dfs)}}")

nivel2_items = []
for i, nombre in enumerate(sorted(test_dfs.keys())[:3]):
    df = test_dfs[nombre]
    meta = template_meta.get(nombre, {{}})
    tid = meta.get('id')
    label = nombre.replace(TEST_MARKER, "").strip()

    if not df.empty and 'valor_numerico' in df.columns:
        serie = df['valor_numerico'].dropna()
        try:
            media = float(serie.astype(float).mean())
        except Exception:
            media = 0.0
        valor = round(min(100.0, max(0.0, media)), 1)
    else:
        valor = 0.0

    print(f"  KPI sub-{{i+1}} [{{label}}]: {{valor}}% (n={{len(df)}})")
    nivel2_items.append({{
        "key": f"kpi_test_{{i+1}}",
        "label": label,
        "valor": valor,
        "template_id": tid,
    }})

# Nivel 1: promedio de sub-KPIs
n1_valor = round(sum(r['valor'] for r in nivel2_items) / len(nivel2_items), 1) if nivel2_items else 0.0
print(f"\\nKPI Nivel 1 'Cobertura' = {{n1_valor}}%")

# Rellenar hasta 5 sub-KPIs si hay menos de 3 templates
while len(nivel2_items) < 5:
    nivel2_items.append({{
        "key": f"kpi_test_{{len(nivel2_items)+1}}",
        "label": f"Sub-indicador {{len(nivel2_items)+1}}",
        "valor": 0.0,
    }})

resultado = {{
    "nivel1": [
        {{"key": "kpi_cobertura",   "label": "Cobertura",   "valor": n1_valor, "descripcion": "Promedio de los indicadores de prueba"}},
        {{"key": "kpi_completitud", "label": "Completitud", "valor": 0.0}},
        {{"key": "kpi_oportunidad", "label": "Oportunidad", "valor": 0.0}},
        {{"key": "kpi_calidad",     "label": "Calidad",     "valor": 0.0}},
        {{"key": "kpi_gestion",     "label": "Gestión",     "valor": 0.0}},
    ],
    "nivel2": {{
        "kpi_cobertura":   nivel2_items,
        "kpi_completitud": [{{"key": f"kpi_comp_{{i}}", "label": f"Comp {{i}}", "valor": 0.0}} for i in range(1,6)],
        "kpi_oportunidad": [{{"key": f"kpi_op_{{i}}",   "label": f"Op {{i}}",   "valor": 0.0}} for i in range(1,6)],
        "kpi_calidad":     [{{"key": f"kpi_cal_{{i}}",  "label": f"Cal {{i}}",  "valor": 0.0}} for i in range(1,6)],
        "kpi_gestion":     [{{"key": f"kpi_ges_{{i}}",  "label": f"Gest {{i}}", "valor": 0.0}} for i in range(1,6)],
    }},
}}

print("\\n✓ Script de prueba ejecutado correctamente")
""")


# ── GET status ────────────────────────────────────────────────────────────────

@router.get("/status")
async def test_data_status(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    dep = (await db.execute(
        select(Dependency).where(Dependency.codigo == TEST_DEP_CODE)
    )).scalar_one_or_none()

    users = (await db.execute(
        select(User).where(User.username.like(f"{TEST_USER_PREFIX}%"))
    )).scalars().all()

    templates = (await db.execute(
        select(Template).where(Template.codigo.like(f"{TEST_TMPL_PREFIX}%"))
    )).scalars().all()

    tmpl_ids = [t.id for t in templates]
    form_count = 0
    if tmpl_ids:
        form_count = await db.scalar(
            select(__import__("sqlalchemy", fromlist=["func"]).func.count(Form.id))
            .where(Form.plantilla_id.in_(tmpl_ids))
        ) or 0

    return {
        "tiene_datos": dep is not None,
        "dependencia": dep.nombre if dep else None,
        "usuarios": [u.username for u in users],
        "templates": [t.nombre for t in templates],
        "formularios": form_count,
    }


# ── POST seed ─────────────────────────────────────────────────────────────────

@router.post("/seed")
async def seed_test_data(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    # Verificar si ya existe
    existing = (await db.execute(
        select(Dependency).where(Dependency.codigo == TEST_DEP_CODE)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existen datos de prueba. Ejecuta /admin/test-data/clean primero.",
        )

    # 1. Dependencia de prueba
    dep = Dependency(
        nombre=f"Dependencia de Pruebas {TEST_MARKER}",
        codigo=TEST_DEP_CODE,
        descripcion=f"Creada automáticamente por el seeder E2E",
    )
    db.add(dep)
    await db.flush()

    # 2. Templates (3) con campo valor_numerico
    TEMPLATES_DEF = [
        ("Hallazgos Humanitarios", "TEST_E2E_T1"),
        ("Procesos Extrajudiciales", "TEST_E2E_T2"),
        ("Entrega Digna", "TEST_E2E_T3"),
    ]
    templates = []
    for base_nombre, codigo in TEMPLATES_DEF:
        nombre = f"{base_nombre} {TEST_MARKER}"
        campos = {
            "fields": [
                {"key": "nombre_caso",    "label": "Nombre del caso",    "type": "text",     "required": True},
                {"key": "region",         "label": "Región",             "type": "text",     "required": True},
                {"key": "valor_numerico", "label": "Valor numérico (%)", "type": "number",   "required": True},
                {"key": "observaciones",  "label": "Observaciones",      "type": "textarea", "required": False},
            ]
        }
        markdown = (
            f"# {base_nombre}\n\n"
            "## Datos del registro\n\n"
            "| Campo | Valor |\n|---|---|\n"
            "| Nombre del caso | {nombre_caso} |\n"
            "| Región | {region} |\n"
            "| Valor numérico | {valor_numerico}% |\n"
        )
        t = Template(
            nombre=nombre,
            descripcion=f"Template de prueba E2E — {base_nombre}",
            codigo=codigo,
            codigo_markdown=markdown,
            configuracion_campos=campos,
        )
        db.add(t)
        templates.append(t)
    await db.flush()

    # 3. Usuarios de prueba
    dep_user = User(
        username=f"{TEST_USER_PREFIX}dep_user",
        nombre_completo=f"Usuario Dependencia {TEST_MARKER}",
        email="test_dep@test.e2e.local",
        role=UserRole.dependency_user,
        password_hash=hash_password("Test@E2E2024!"),
        dependency_id=dep.id,
        requires_password_change=False,
    )
    validator_user = User(
        username=f"{TEST_USER_PREFIX}validator",
        nombre_completo=f"Validador {TEST_MARKER}",
        email="test_val@test.e2e.local",
        role=UserRole.validator,
        password_hash=hash_password("Test@E2E2024!"),
        requires_password_change=False,
    )
    db.add_all([dep_user, validator_user])
    await db.flush()

    # 4. Formularios (10 por template: 7 aprobados, 3 rechazados)
    random.seed(42)
    REGIONES = ["Antioquia", "Bogotá", "Valle del Cauca", "Bolívar", "Cundinamarca"]
    VALORES = [23.5, 41.0, 67.8, 52.3, 88.1, 34.7, 76.2, 91.0, 45.5, 60.0]

    total_forms = 0
    for t in templates:
        for i in range(10):
            aprobado = i < 7
            valor = VALORES[i % len(VALORES)]
            form = Form(
                plantilla_id=t.id,
                usuario_id=dep_user.id,
                dependency_id=dep.id,
                datos_dinamicos={
                    "nombre_caso": f"Caso #{i+1} — {t.nombre.replace(TEST_MARKER, '').strip()}",
                    "region": REGIONES[i % len(REGIONES)],
                    "valor_numerico": valor,
                    "observaciones": f"Registro de prueba #{i+1} generado por seeder E2E.",
                },
                estado=FormStatus.approved if aprobado else FormStatus.rejected,
                validado_por_id=validator_user.id,
                fecha_validacion=datetime.now(timezone.utc),
                fecha_usuario=date.today(),
                comentario_rechazo=None if aprobado else "Información incompleta — datos de prueba",
            )
            db.add(form)
            total_forms += 1

    await db.commit()

    template_names = [t.nombre for t in templates]
    pipeline_script = _build_test_pipeline_script(template_names)

    return {
        "ok": True,
        "dependencia_id": str(dep.id),
        "template_ids": [str(t.id) for t in templates],
        "template_nombres": template_names,
        "dep_user": dep_user.username,
        "dep_password": "Test@E2E2024!",
        "validator": validator_user.username,
        "validator_password": "Test@E2E2024!",
        "formularios_creados": total_forms,
        "formularios_aprobados": 7 * len(templates),
        "formularios_rechazados": 3 * len(templates),
        "pipeline_script": pipeline_script,
        "mensaje": (
            f"Datos de prueba creados correctamente. "
            f"{total_forms} formularios en {len(templates)} templates. "
            "Usa /admin/test-data/install-script para instalar el script de pipeline."
        ),
    }


# ── POST install-script ───────────────────────────────────────────────────────

@router.post("/install-script")
async def install_test_script(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    """Instala el script de pipeline de prueba en el editor."""
    # Buscar templates de prueba para generar el script
    templates = (await db.execute(
        select(Template).where(Template.codigo.like(f"{TEST_TMPL_PREFIX}%"))
    )).scalars().all()

    if not templates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay datos de prueba. Ejecuta /admin/test-data/seed primero.",
        )

    script = _build_test_pipeline_script([t.nombre for t in templates])

    # Guardar o actualizar en DB
    existing = (await db.execute(
        select(PipelineScript).where(PipelineScript.activo == True).limit(1)
    )).scalar_one_or_none()

    if existing:
        existing.codigo = script
        existing.nombre = "Pipeline de Prueba E2E"
        existing.updated_at = datetime.now(timezone.utc)
    else:
        db.add(PipelineScript(codigo=script, nombre="Pipeline de Prueba E2E"))

    await db.commit()
    return {"ok": True, "mensaje": "Script de prueba instalado en el editor de pipeline."}


# ── DELETE clean ──────────────────────────────────────────────────────────────

@router.delete("/clean")
async def clean_test_data(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    # 1. Templates de prueba
    templates = (await db.execute(
        select(Template).where(Template.codigo.like(f"{TEST_TMPL_PREFIX}%"))
    )).scalars().all()
    tmpl_ids = [t.id for t in templates]

    forms_deleted = 0
    if tmpl_ids:
        # Formularios de esos templates
        res = await db.execute(
            delete(Form).where(Form.plantilla_id.in_(tmpl_ids))
        )
        forms_deleted = res.rowcount

    # 2. Usuarios de prueba
    users_res = await db.execute(
        delete(User).where(User.username.like(f"{TEST_USER_PREFIX}%"))
    )
    users_deleted = users_res.rowcount

    # 3. Templates
    tmpls_deleted = 0
    for t in templates:
        await db.delete(t)
        tmpls_deleted += 1

    # 4. Dependencia de prueba
    dep = (await db.execute(
        select(Dependency).where(Dependency.codigo == TEST_DEP_CODE)
    )).scalar_one_or_none()
    dep_deleted = 0
    if dep:
        await db.delete(dep)
        dep_deleted = 1

    await db.commit()

    return {
        "ok": True,
        "formularios_eliminados": forms_deleted,
        "usuarios_eliminados": users_deleted,
        "templates_eliminados": tmpls_deleted,
        "dependencias_eliminadas": dep_deleted,
        "mensaje": "Datos de prueba eliminados correctamente.",
    }

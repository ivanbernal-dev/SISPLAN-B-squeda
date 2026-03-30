"""
scripts/seed_linea3.py — Seed del template de la Línea Estratégica No. 3.

Una sola hoja del Excel = 1 IndicadorNivel2 + 1 Template.
Crea (o reutiliza) el Indicador Nivel 1 de Línea 3.

Uso:
    python scripts/seed_linea3.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings

# ── Texto institucional ────────────────────────────────────────────────────────

LINEA_ESTRATEGICA = (
    "Línea 3. Articulación interinstitucional e intersectorial para el "
    "fortalecimiento de las acciones de búsqueda humanitaria y extrajudicial"
)

RESULTADO_ESTRATEGICO = (
    "R3. La UBPD fortalece las condiciones de trabajo conjunto y coordinado con "
    "actores corresponsables en el proceso de búsqueda humanitaria y extrajudicial "
    "en el ámbito local, nacional e internacional para facilitar su actuación y "
    "aumentar el impacto de su intervención"
)

RESULTADO_2026 = (
    "Consolidar la búsqueda humanitaria y extrajudicial y la sostenibilidad del "
    "proceso, a través de alianzas estratégicas basadas en la complementariedad "
    "técnica y financiera, y la implementación de una Política Pública Integral "
    "territorializada y co-creada que garantice la corresponsabilidad de los "
    "actores del SNB"
)

OBJETIVO_PRODUCTO = (
    "Consolidar el modelo de gobernanza y coordinación interinstitucional e "
    "intersectorial para la búsqueda de personas dadas por desaparecidas (PDD), "
    "mediante la implementación territorial de políticas públicas y planes de "
    "articulación que aseguren la eficiencia operativa y el impacto social de las "
    "intervenciones en el marco del Sistema Nacional de Búsqueda (SNB)."
)

# ── Constructores de campos (mismo patrón que seed_templates_excel.py) ─────────

def ro_text(name, label, default=""):
    return {"name": name, "label": label, "tipo": "text",
            "readonly": True, "requerido": False, "default": default}

def ro_textarea(name, label, default=""):
    return {"name": name, "label": label, "tipo": "textarea",
            "readonly": True, "requerido": False, "default": default}

def ed_date(name, label, requerido=True):
    return {"name": name, "label": label, "tipo": "date",
            "readonly": False, "requerido": requerido, "default": None}

def ed_select(name, label, opciones, requerido=True):
    return {"name": name, "label": label, "tipo": "select",
            "readonly": False, "requerido": requerido,
            "opciones": opciones, "default": None}

def ed_textarea(name, label, requerido=False, placeholder=""):
    return {"name": name, "label": label, "tipo": "textarea",
            "readonly": False, "requerido": requerido,
            "default": None, "placeholder": placeholder}

def ed_text(name, label, requerido=False, placeholder=""):
    return {"name": name, "label": label, "tipo": "text",
            "readonly": False, "requerido": requerido,
            "default": None, "placeholder": placeholder}

def ed_number(name, label, requerido=True, placeholder=""):
    return {"name": name, "label": label, "tipo": "number",
            "readonly": False, "requerido": requerido,
            "default": None, "placeholder": placeholder}

def computed(name, label, formula):
    return {"name": name, "label": label, "tipo": "computed",
            "readonly": True, "requerido": False,
            "formula": formula, "default": None}


# ── Definición del template L3-P1-DPE-2026 ───────────────────────────────────

INDICADORES_L3_P1 = [
    (
        "Porcentaje de instrumentos relacionamiento (convenios/protocolos) vigentes "
        "y con seguimiento técnico. Formula: (V1 / V2) x 100"
    ),
    (
        "Índice de Barreras Resueltas = ((Barreras con plan de acción + Barreras "
        "resueltas) / Total de Barreras Identificadas) X 100"
    ),
    (
        "Porcentaje de avance físico de las metas del Plan Estratégico del SNB. "
        "Índice = (Hitos cumplidos / Hitos Programados - hitos reprogramados "
        "justificados) X 100"
    ),
    (
        "Tasa de implementación de acciones de mejora derivadas de informes de "
        "gestión. Tasa = (Informes sistematizados con al menos 1 acción mejora "
        "formulada / Total Informes) x 100"
    ),
    (
        "Fase de diseño de la Política Pública culminada con validación de actores. "
        "Índice de Avance = (Fases del diseño completadas y validadas / Total de "
        "Fases Definidas) x 100"
    ),
]

CAMPOS_L3_P1 = (
    [
        ed_date("mes_reporte", "Mes de Reporte"),
        ro_textarea("linea_estrategica", "Línea estratégica", LINEA_ESTRATEGICA),
        ro_textarea("resultado_estrategico_2024_2028",
                    "Resultados Estratégico 2024 - 2028", RESULTADO_ESTRATEGICO),
        ro_textarea("resultado_2026", "Resultado 2026", RESULTADO_2026),
        ro_text("codigo_producto", "Código del Producto", "L3-P1-DPE-2026"),
        ro_text("producto", "Producto",
                "Plan de Consolidación de la Articulación Interinstitucional "
                "e Intersectorial para la respuesta Integral en la Búsqueda"),
        ro_textarea("objetivo_producto", "Objetivo del Producto", OBJETIVO_PRODUCTO),
        ro_text("area_responsable", "Área Responsable", "Oficina Asesora de Planeación"),
        ro_text("area_implementadora_1", "Área implementadora o corresponsable 1",
                "Dirección General (Asesor relacionamiento y articulación)"),
        ro_text("area_implementadora_2", "Área implementadora o corresponsable 2", ""),
        ro_text("area_implementadora_3", "Área implementadora o corresponsable 3", ""),
    ] + [
        ed_select("indicador", "Indicador", INDICADORES_L3_P1),
        ed_textarea("ejes_actividades_clave", "Ejes y Actividades Clave",
                    placeholder="Describa el eje y actividades clave del indicador seleccionado"),
        ed_text("variable_1", "Variable 1",
                placeholder="Descripción de la variable de medición mensual"),
        ed_number("reporte_cuantitativo_variable_1", "Reporte Cuantitativo Variable 1",
                  placeholder="Valor numérico del avance en el mes"),
        ed_text("variable_2", "Variable 2",
                placeholder="Descripción de la meta / denominador"),
        ed_number("reporte_cuantitativo_variable_2", "Reporte Cuantitativo Variable 2",
                  placeholder="Meta numérica total — denominador"),
        computed("calculo_formula", "Cálculo Fórmula",
                 "reporte_cuantitativo_variable_1 / reporte_cuantitativo_variable_2"),
        ed_text("meta_anual", "Meta Anual",
                placeholder="Descripción de la meta anual del indicador seleccionado"),
        ed_text("entregable", "Entregable",
                placeholder="Nombre del entregable asociado al indicador"),
        ed_textarea("informe_cualitativo", "Informe cualitativo",
                    placeholder="Descripción cualitativa del avance del mes"),
        {"name": "soportes_archivos", "label": "Soportes / Archivos",
         "tipo": "archivos", "readonly": False, "requerido": False, "default": None},
    ]
)

TEMPLATES_DATA = [
    {
        "codigo": "L3-P1-DPE-2026",
        "nombre": "L3-P1-DPE-2026 — Plan de Consolidación de la Articulación",
        "nivel2_nombre": (
            "Plan de Consolidación de la Articulación Interinstitucional e "
            "Intersectorial para la respuesta Integral en la Búsqueda"
        ),
        "nivel2_desc": (
            "Mide el avance en la consolidación del modelo de gobernanza y "
            "coordinación interinstitucional e intersectorial para la búsqueda."
        ),
        "campos": CAMPOS_L3_P1,
    }
]


# ── Seed ──────────────────────────────────────────────────────────────────────

async def run_seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as db:
        from app.models.indicator import Indicator
        from app.models.indicador_nivel2 import IndicadorNivel2
        from app.models.template import Template

        # 1. Buscar o crear Indicador Nivel 1 para Línea 3
        result = await db.execute(
            select(Indicator).where(Indicator.nombre.ilike("%Línea 3%"))
        )
        nivel1 = result.scalar_one_or_none()

        if nivel1 is None:
            nivel1 = Indicator(
                nombre="Línea 3 — Articulación interinstitucional e intersectorial",
                descripcion=(
                    "Fortalecimiento de las condiciones de trabajo conjunto y coordinado "
                    "con actores corresponsables en el proceso de búsqueda humanitaria "
                    "y extrajudicial."
                ),
                activo=True,
            )
            db.add(nivel1)
            await db.flush()
            print(f"Creado Indicador Nivel 1: {nivel1.nombre} (id={nivel1.id})")
        else:
            print(f"Usando Indicador Nivel 1 existente: {nivel1.nombre} (id={nivel1.id})")

        # 2. Limpiar registros anteriores de este seed
        codigos = [t["codigo"] for t in TEMPLATES_DATA]
        nombres_nivel2 = [t["nivel2_nombre"] for t in TEMPLATES_DATA]

        existing_templates = (await db.execute(
            select(Template).where(Template.codigo.in_(codigos))
        )).scalars().all()
        for tmpl in existing_templates:
            await db.delete(tmpl)

        existing_n2 = (await db.execute(
            select(IndicadorNivel2).where(IndicadorNivel2.nombre.in_(nombres_nivel2))
        )).scalars().all()
        for n2 in existing_n2:
            await db.delete(n2)

        await db.flush()

        # 3. Crear IndicadorNivel2 + Template
        for tdata in TEMPLATES_DATA:
            nivel2 = IndicadorNivel2(
                nombre=tdata["nivel2_nombre"],
                descripcion=tdata["nivel2_desc"],
                indicador_nivel1_id=nivel1.id,
                activo=True,
            )
            db.add(nivel2)
            await db.flush()
            print(f"\n  IndicadorNivel2: {nivel2.nombre} (id={nivel2.id})")

            campos = tdata["campos"]
            n_edit = sum(1 for c in campos if not c.get("readonly") and c.get("tipo") != "computed")
            n_ro   = sum(1 for c in campos if c.get("readonly"))
            n_comp = sum(1 for c in campos if c.get("tipo") == "computed")

            template = Template(
                codigo=tdata["codigo"],
                nombre=tdata["nombre"],
                descripcion=tdata["nivel2_desc"],
                codigo_markdown="",
                configuracion_campos={"campos": campos},
                activo=True,
                indicador_nivel2_id=nivel2.id,
            )
            db.add(template)
            await db.flush()
            print(f"    Template: {template.nombre} (id={template.id})")
            print(f"    Campos: {len(campos)} total — {n_ro} readonly, {n_edit} editables, {n_comp} computed")

        await db.commit()
        print("\nSeed Línea 3 completado exitosamente.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_seed())

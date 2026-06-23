"""
scripts/seed_templates_excel.py — Seed de los 6 templates de la Línea Estratégica No. 1.

Cada hoja del Excel = 1 IndicadorNivel2 + 1 Template con todos sus campos.
Campos READONLY: datos institucionales fijos del producto (no los edita el usuario).
Campos EDITABLE: datos que llena la dependencia por reporte mensual.
Campos SELECT:   Indicador (el usuario elige cuál está reportando).
Campo COMPUTED:  calculo_formula = variable_1 / variable_2.

Uso:
    python scripts/seed_templates_excel.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings

# ── Texto institucional común ──────────────────────────────────────────────────
LINEA_ESTRATEGICA = (
    "Línea 1. Investigación Humanitaria y Extrajudicial "
    "(Gestión de información e Investigación para la Búsqueda)"
)

RESULTADO_ESTRATEGICO = (
    "R1. La investigación humanitaria y extrajudicial, aplicada, participativa y territorial, "
    "sustentada en el fortalecimiento de las capacidades y competencias en procesos forenses de "
    "prospección, recuperación, identificación y las nuevas metodologías forenses implementadas "
    "en la UBPD, agilizan e impulsan la búsqueda para encontrar a las PDD y responder a las "
    "personas, familias y OCMP que buscan, garantizando su derecho al acceso a la información."
)


# ── Constructores de campos ────────────────────────────────────────────────────

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


# ── Bloques reutilizables ──────────────────────────────────────────────────────

def campos_producto_fijos(codigo, producto, objetivo, resultado_2026,
                           area_resp, area_impl1="", area_impl2="", area_impl3=""):
    return [
        ed_date("mes_reporte", "Mes de Reporte"),
        ro_textarea("linea_estrategica", "Línea estratégica", LINEA_ESTRATEGICA),
        ro_textarea("resultado_estrategico_2024_2028",
                    "Resultados Estratégico 2024 - 2028", RESULTADO_ESTRATEGICO),
        ro_textarea("resultado_2026", "Resultado 2026", resultado_2026),
        ro_text("codigo_producto", "Código del Producto", codigo),
        ro_text("producto", "Producto", producto),
        ro_textarea("objetivo_producto", "Objetivo del Producto", objetivo),
        ro_text("area_responsable", "Área Responsable", area_resp),
        ro_text("area_implementadora_1", "Área implementadora o corresponsable 1", area_impl1),
        ro_text("area_implementadora_2", "Área implementadora o corresponsable 2", area_impl2),
        ro_text("area_implementadora_3", "Área implementadora o corresponsable 3", area_impl3),
    ]


def campos_indicador_y_reporte(indicadores_opciones):
    return [
        ed_select("indicador", "Indicador", indicadores_opciones),
        ed_textarea("ejes_actividades_clave", "Ejes y Actividades Clave",
                    placeholder="Describa el eje y actividades clave del indicador seleccionado"),
        ed_text("variable_1", "Variable 1",
                placeholder="Descripción de la variable de medición mensual"),
        ed_number("reporte_cuantitativo_variable_1", "Reporte Cuantitativo Variable 1",
                  placeholder="Valor numérico del avance en el mes (ej: 0.75)"),
        ed_text("variable_2", "Variable 2",
                placeholder="Descripción de la meta / denominador (ej: 100% de los documentos publicados)"),
        ed_number("reporte_cuantitativo_variable_2", "Reporte Cuantitativo Variable 2",
                  placeholder="Meta numérica total — denominador (ej: 1.0 para 100%)"),
        computed("calculo_formula", "Cálculo Fórmula",
                 "reporte_cuantitativo_variable_1 / reporte_cuantitativo_variable_2"),
        ed_text("meta_anual", "Meta Anual",
                placeholder="Descripción de la meta anual del indicador seleccionado"),
    ]


def campos_cierre(entregables_count=1):
    campos = []
    if entregables_count == 1:
        campos.append(ed_text("entregable", "Entregable",
                               placeholder="Nombre del entregable asociado al indicador"))
    else:
        for i in range(1, entregables_count + 1):
            campos.append(ed_text(f"entregable_{i}", f"Entregable {i}",
                                   placeholder=f"Nombre del entregable {i}"))
    campos.append(ed_textarea("informe_cualitativo", "Informe cualitativo",
                               placeholder="Descripción cualitativa del avance del mes"))
    campos.append({"name": "soportes_archivos", "label": "Soportes / Archivos",
                   "tipo": "archivos", "readonly": False, "requerido": False, "default": None})
    return campos


# ── Definición de los 6 templates (uno por hoja del Excel) ────────────────────

TEMPLATES_DATA = [
    # ────────────────────────────────────────────────────────────────────────────
    {
        "codigo": "L1-P1-DPE-2026",
        "nombre": "L1-P1-DPE-2026 — Modelo operativo descentralizado",
        "nivel2_nombre": "Modelo operativo descentralizado de búsqueda humanitaria y extrajudicial fortalecido",
        "nivel2_desc": "Mide el avance en el fortalecimiento del modelo operativo descentralizado de búsqueda.",
        "campos": (
            campos_producto_fijos(
                codigo="L1-P1-DPE-2026",
                producto="Modelo operativo descentralizado de búsqueda humanitaria y extrajudicial fortalecido",
                objetivo=(
                    "Consolidar la coherencia operativa del despliegue nacional mediante la integración "
                    "de las capacidades regionales y territoriales, incorporando las particularidades del "
                    "territorio; de modo que la planeación diferenciada asegure el cumplimiento armonizado "
                    "de la estrategia institucional."
                ),
                resultado_2026=(
                    "Un modelo de búsqueda humanitaria y extrajudicial territorializado donde la estrategia "
                    "nacional se traduce en acciones locales pertinentes, logrando una respuesta institucional "
                    "ágil, articulada y con capacidad técnica suficiente para abordar las particularidades "
                    "de la búsqueda en cada contexto regional."
                ),
                area_resp="Subdirección General Técnica y Territorial (Líder)",
                area_impl1="Grupos Internos de Trabajo Regional",
                area_impl2="Grupos Internos de Trabajo Territorial",
                area_impl3="Oficina Asesora de Planeación (Corresponsable)",
            ) +
            campos_indicador_y_reporte([
                "Porcentaje de avance en la publicación de los documentos",
                "Porcentaje de avance en la formulación y socialización de la estrategia de articulación para la IHE entre los equipos técnicos.",
                "Número de espacios técnicos realizados",
            ]) +
            campos_cierre(entregables_count=2)
        ),
    },
    # ────────────────────────────────────────────────────────────────────────────
    {
        "codigo": "L1-P1-IHE-2026",
        "nombre": "L1-P1-IHE-2026 — Estrategia planificación IHE",
        "nivel2_nombre": "Estrategia para la planificación de la IHE Fortalecida",
        "nivel2_desc": "Mide el avance en la sistematización del ciclo de diseño y planificación investigativa.",
        "campos": (
            campos_producto_fijos(
                codigo="L1-P1-IHE-2026",
                producto="Estrategia para la planificación de la IHE Fortalecida",
                objetivo=(
                    "Sistematizar el ciclo de diseño y planificación investigativa mediante la implementación "
                    "de modelos de investigación dinámicos (esquemas procedimentales flexibles) y modelos de "
                    "análisis retrospectivo con enfoque predictivo (modelado de escenarios de búsqueda), que "
                    "permitan la validación técnica de nuevas hipótesis y aseguren la rigurosidad científica, "
                    "la trazabilidad de la información y la interoperabilidad de los procesos en escenarios "
                    "de alta complejidad."
                ),
                resultado_2026=(
                    "Planes Regionales de Búsqueda fortalecidos técnicamente mediante la adopción de esquemas "
                    "de planificación dinámicos y herramientas de análisis retrospectivo predictivo, "
                    "garantizando la gestión sistematizada de la información para agilizar las investigaciones "
                    "territoriales."
                ),
                area_resp="Subdirección Técnica de Investigación Humanitaria",
                area_impl1="GIT Metodología e Innovación para la búsqueda (Líder)",
                area_impl2="GITT Ciencia de Datos para la Búsqueda (Corresponsable)",
                area_impl3="N/A",
            ) +
            campos_indicador_y_reporte([
                "Porcentaje de avance en la parametrización de modelos analíticos",
                "Número de herramientas de análisis estratégico y validación adoptadas oficialmente.",
                "Porcentaje de actualización de la arquitectura documental institucional para la IHE",
                "Planes Regionales de Búsqueda (PRB) formulados o actualizados a partir de la implementación de reingeniería y automatización",
            ]) +
            campos_cierre(entregables_count=1)
        ),
    },
    # ────────────────────────────────────────────────────────────────────────────
    {
        "codigo": "L1-P2-IHE-2026",
        "nombre": "L1-P2-IHE-2026 — Sistema SIM Busquemos v2.0",
        "nivel2_nombre": "Sistema de Información Misional SIM Busquemos versión 2.0 Implementado",
        "nivel2_desc": "Mide el avance en la implementación del SIM 2.0 como ecosistema de información unificado.",
        "campos": (
            campos_producto_fijos(
                codigo="L1-P2-IHE-2026",
                producto="Sistema de Información Misional SIM Busquemos versión 2.0 Implementado",
                objetivo=(
                    "Potenciar la investigación humanitaria y extrajudicial de búsqueda mediante la "
                    "implementación del SIM 2.0, consolidando un ecosistema de información unificado que "
                    "garantice la trazabilidad, integridad y análisis de datos (ciclo de vida de la "
                    "información) sobre personas dadas por desaparecidas, personas buscadoras, sitios de "
                    "interés forense, acciones de recuperación de cuerpos con fines de identificación y "
                    "acciones de participación con enfoque diferencial."
                ),
                resultado_2026=(
                    "Los procesos de investigación humanitaria e identificación forense son más ágiles y "
                    "eficientes, garantizando la trazabilidad, calidad y análisis estratégico de la "
                    "información de las personas dadas por desaparecidas, para ofrecer respuestas oportunas "
                    "y certeras a las familias desde una operación territorial fortalecida."
                ),
                area_resp="Subdirección Técnica de Investigación Humanitaria",
                area_impl1="GIT Sistema de Información Misional (Líder)",
                area_impl2="GIT Ciencia de Datos para la Búsqueda (Corresponsable)",
                area_impl3="",
            ) +
            campos_indicador_y_reporte([
                "Índice de definición de reglas de negocio por módulo misional.",
                "Índice de integración Misional: Número de módulos (PDD, RNFCIS, etc.) integrados y sincronizados",
                "Tasa de Integridad del Dato",
                "Índice de integración o migración de la información",
                "Tasa de automatización de reportes",
            ]) +
            campos_cierre(entregables_count=3)
        ),
    },
    # ────────────────────────────────────────────────────────────────────────────
    {
        "codigo": "L1-P3-IHE-2026",
        "nombre": "L1-P3-IHE-2026 — Estrategia Gestión Integral del Dato",
        "nivel2_nombre": "Estrategia de Gestión Integral del Dato y Soporte de Analítica avanzada para la Investigación Humanitaria",
        "nivel2_desc": "Mide la implementación del ecosistema de inteligencia de datos y analítica avanzada.",
        "campos": (
            campos_producto_fijos(
                codigo="L1-P3-IHE-2026",
                producto="Estrategia de Gestión Integral del Dato y Soporte de Analítica avanzada para la Investigación Humanitaria",
                objetivo=(
                    "Implementar un modelo de gestión integral de datos y analítica avanzada (Ecosistema de "
                    "Inteligencia de Datos) que garantice la integridad de los datos y habilite capacidades "
                    "analíticas retrospectivas con enfoque predictivo, optimizando la toma de decisiones "
                    "estratégicas en la investigación humanitaria."
                ),
                resultado_2026=(
                    "La investigación humanitaria y los procesos forenses de recuperación e identificación "
                    "se fortalecen mediante modelos de análisis retrospectivo y predictivo basados en datos "
                    "íntegros y de alta calidad, optimizando la respuesta institucional y el cumplimiento "
                    "de los estándares de investigación."
                ),
                area_resp="Subdirección Técnica de Investigación Humanitaria",
                area_impl1="GITT Ciencia de datos para la Búsqueda (Líder)",
                area_impl2="GITT Metodología e Innovación para la Búsqueda (Corresponsable)",
                area_impl3="GITT SIM (Corresponsable)",
            ) +
            campos_indicador_y_reporte([
                "Porcentaje de implementación del marco de gobernanza de datos",
                "Índice de Calidad del Dato (Completitud, Unicidad y Consistencia).",
                "Número de fuentes de datos (internas/externas) centralizadas en el ecosistema.",
                "Tasa de detección automática de vínculos de PDD en el Universo",
                "Precisión de modelos",
                "Porcentaje de investigaciones activas que utilizan el Ecosistema de Datos como soporte",
                "Porcentaje de investigadores y equipos forenses clave capacitados en el uso de la herramienta.",
            ]) +
            campos_cierre(entregables_count=4)
        ),
    },
    # ────────────────────────────────────────────────────────────────────────────
    {
        "codigo": "L1-P4-IHE-2026",
        "nombre": "L1-P4-IHE-2026 — Estrategia Aportantes Consolidada",
        "nivel2_nombre": "Estrategia Aportantes Consolidada",
        "nivel2_desc": "Mide la implementación del modelo de relacionamiento y gestión de información de aportantes.",
        "campos": (
            campos_producto_fijos(
                codigo="L1-P4-IHE-2026",
                producto="Estrategia Aportantes Consolidada",
                objetivo=(
                    "Implementar y consolidar un modelo integral de relacionamiento y gestión de la "
                    "información con personas que participaron en las hostilidades, sistematizando la "
                    "recolección, valoración y análisis de sus aportes técnicos y testimoniales, para "
                    "cualificar los insumos de la Investigación Humanitaria y Extrajudicial orientada a "
                    "la búsqueda, localización e identificación de personas dadas por desaparecidas."
                ),
                resultado_2026=(
                    "La Investigación Humanitaria y Extrajudicial se fortalece a través de la contribución "
                    "estructurada de la información técnica y testimonial aportada por personas que "
                    "participaron directa o indirectamente en las hostilidades sobre ubicación de sitios de "
                    "interés forense, personas dadas por desaparecidas, etc."
                ),
                area_resp="Subdirección Técnica Forense",
                area_impl1="N/A",
                area_impl2="N/A",
                area_impl3="N/A",
            ) +
            campos_indicador_y_reporte([
                "Porcentaje de Cumplimiento de la Ruta de Aporte",
                "Tasa de Acreditación de Aportes",
                "Porcentaje de Ejecución de Planes de Trabajo con Aportantes.",
                "Efectividad de Acciones de Localización y Prospección derivadas de Aportes.",
            ]) +
            campos_cierre(entregables_count=1)
        ),
    },
    # ────────────────────────────────────────────────────────────────────────────
    {
        "codigo": "L1-P5-IHE-2026",
        "nombre": "L1-P5-IHE-2026 — Estrategia Misión Identificación",
        "nivel2_nombre": "Estrategia Misión Identificación",
        "nivel2_desc": "Mide el avance en la identificación ágil de cuerpos recuperados mediante convergencia multimodal.",
        "campos": (
            campos_producto_fijos(
                codigo="L1-P5-IHE-2026",
                producto="Estrategia Misión identificación",
                objetivo=(
                    "Impulsar la identificación ágil de los cuerpos recuperados por la UBPD, disminuyendo "
                    "el rezago forense nacional a través de un modelo de convergencia multimodal que integre "
                    "la lofoscopia forense, la verificación de correspondencia in situ, el abordaje "
                    "antropológico y la aplicación de tecnología avanzada en genética. Este modelo posiciona "
                    "a los CIAFI como centros técnicos, capaces de dinamizar el procesamiento y ofrecer "
                    "respuestas efectivas en contextos complejos."
                ),
                resultado_2026=(
                    "Para finales de 2026, el resultado estratégico de la Estrategia Misión Identificación "
                    "es la transición hacia un modelo de identificación multimodal. Este modelo garantiza "
                    "que el rezago en la intervención forense se gestione mediante un flujo técnico continuo, "
                    "donde cada hallazgo es sometido a un proceso de identificación ágil y certero."
                ),
                area_resp="Subdirección Técnica Forense",
                area_impl1="",
                area_impl2="",
                area_impl3="",
            ) +
            campos_indicador_y_reporte([
                "Porcentaje de CIAFI con modelo de operación formalizados.",
                "Manuales de actividades y roles específicos para los equipos interdisciplinarios de abordaje forense",
                "Porcentaje de implementación del sistema de monitoreo en tiempo real.",
                "Porcentaje casos VCIPM Positivos Identificados",
                "Porcentaje de cuerpos abordados por los equipos interdisciplinarios de la UBPD bajo la metodología de Examen Forense Preliminar en Cementerios.",
                "Tasa de identificación de cuerpos en relación al número de coincidencias de Necrodactilias sometidas a AFIS",
                "Cuerpos intervenidos por Abordaje Integral y otro tipo de análisis Forenses en Laboratorio",
                "Porcentaje de restos óseos con perfil biológico digital y análisis multivariado.",
                "Porcentaje de muestras enviadas a terceros con reporte técnico recibido.",
                "Porcentaje de registros técnicos sincronizados con bases de datos aliadas",
                "Porcentaje de cuerpos identificados mediante acciones de impulso genético",
            ]) +
            campos_cierre(entregables_count=1)
        ),
    },
]


# ── Seed ──────────────────────────────────────────────────────────────────────

async def run_seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as db:
        from app.models.indicator import Indicator
        from app.models.indicador_nivel2 import IndicadorNivel2
        from app.models.template import Template

        # 1. Obtener primer Indicador Nivel 1
        result = await db.execute(select(Indicator).order_by(Indicator.id).limit(1))
        nivel1 = result.scalar_one_or_none()
        if nivel1 is None:
            print("ERROR: No hay indicadores de Nivel 1. Inicia el servidor primero.")
            return
        print(f"Usando Indicador Nivel 1: {nivel1.nombre} (id={nivel1.id})")

        # 2. Limpiar registros anteriores del seed
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

        # 3. Crear IndicadorNivel2 + Template por cada hoja del Excel
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
                codigo_markdown="",          # Templates basados en campos, sin cuerpo Markdown
                configuracion_campos={"campos": campos},
                activo=True,
                indicador_nivel2_id=nivel2.id,
            )
            db.add(template)
            await db.flush()
            print(f"    Template: {template.nombre} (id={template.id})")
            print(f"    Campos: {len(campos)} total — {n_ro} readonly, {n_edit} editables, {n_comp} computed")

        await db.commit()
        print("\nSeed completado exitosamente.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_seed())

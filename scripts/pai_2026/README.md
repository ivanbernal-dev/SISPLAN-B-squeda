# PAI 2026 — Setup de templates e indicadores

Reproducción del estado de la base de datos para el **Plan de Acción Institucional 2026** del UBPD.

## Estructura

```
scripts/pai_2026/
├── README.md
├── setup_pai.py          # Excel  → JSON (genera la lista de templates)
├── load_pai.py           # JSON   → BD (crea indicadores Nivel 2 + Templates)
├── pipeline_pai.py       # Código del PipelineScript activo
└── data/
    ├── PAI_DEFINITIVO_2026.xlsx   # Excel fuente del PAI (14 hojas = 14 productos)
    └── pai_templates.json         # Salida de setup_pai.py
```

## Convención

- **Indicador Nivel 1** = Línea Estratégica (L1, L2, …, L6) — 6 entradas
- **Indicador Nivel 2** = Producto del PAI (cada hoja del Excel) — 14 entradas
- **Template**          = ligado a su Indicador Nivel 2, `codigo` = nombre de hoja
  (ej. `L1-P1-DPE-2026`)

Cada template define **29 campos** mapeados desde las columnas del Excel:
constantes del producto (readonly, pre-llenados), variables de la actividad
editables por la dependencia, ponderaciones calculadas, comentarios y
observaciones del validador (OAP).

## Campos especiales

Cada template marca campos con dos flags personalizados:

### `validator_only: true`
La dependencia NO ve el campo. Sólo el validador lo edita al aprobar el form.
Aplica a `obs_oap` y `obs_oap_estado` (las Observaciones y Recomendaciones OAP).

### `auto_calculate: "<nombre>"`
El frontend lo recalcula en tiempo real al editar los inputs, y el backend lo
recalcula al guardar / cargar Excel (sobreescribe cualquier valor enviado).

| Campo | Fórmula | Detalle |
|---|---|---|
| `pct_avance_final` | `ratio_alcanzado_proyectado` | `alcanzado / proyectado` (si proyectado=0 → `None` / "No Aplica") |
| `estado_actividad` | `estado_cumplimiento_from_pct_final` | ≥90% Cumple, 70–89% Parcial, <70% No Cumple, sin dato → No Aplica |

## Cómo correr el setup desde cero

> ⚠️ **Borra todos los formularios respondidos, KPIs y templates existentes.**

### 1. Limpiar BD y crear los 6 indicadores Nivel 1

```bash
docker exec ubpd_postgres psql -U ubpd_user -d ubpd_db <<'SQL'
DELETE FROM archivos;
DELETE FROM formularios_respondidos;
DELETE FROM kpi_resultados;
DELETE FROM fact_stats;
DELETE FROM templates;
DELETE FROM indicadores_nivel2;
DELETE FROM indicadores_nivel1;

INSERT INTO indicadores_nivel1 (id, nombre, descripcion, formula_tipo, peso, activo) VALUES
 (1, 'Línea 1 — Investigación Humanitaria y Extrajudicial', 'Gestión de información e Investigación para la Búsqueda', 'promedio_ponderado', 1.0, true),
 (2, 'Línea 2 — Memoria y Legado', 'Estrategia de memoria, legado y construcción de paz', 'promedio_ponderado', 1.0, true),
 (3, 'Línea 3 — Articulación Interinstitucional', 'Coordinación y articulación con actores corresponsables', 'promedio_ponderado', 1.0, true),
 (4, 'Línea 4 — Comunicaciones y Pedagogía', 'Estrategia integral de comunicaciones y pedagogía', 'promedio_ponderado', 1.0, true),
 (5, 'Línea 5 — Participación de Familias y Personas Buscadoras', 'Macro-estrategia de participación diferencial', 'promedio_ponderado', 1.0, true),
 (6, 'Línea 6 — Soporte Estratégico y Operativo', 'Gestión administrativa, financiera y de seguimiento', 'promedio_ponderado', 1.0, true);

SELECT setval('indicadores_nivel1_id_seq', 7, false);
SQL
```

### 2. Generar el JSON de templates desde el Excel

```bash
python3 scripts/pai_2026/setup_pai.py
# → escribe scripts/pai_2026/data/pai_templates.json
```

### 3. Cargar a la BD (crea Nivel 2 + Templates)

```bash
docker cp scripts/pai_2026/data/pai_templates.json ubpd_backend:/tmp/
docker cp scripts/pai_2026/load_pai.py             ubpd_backend:/tmp/
docker exec ubpd_backend python3 /tmp/load_pai.py
```

### 4. Activar el script del pipeline

```bash
docker cp scripts/pai_2026/pipeline_pai.py ubpd_backend:/tmp/
docker exec ubpd_backend python3 - <<'PY'
import asyncio
from sqlalchemy import update
from app.database import AsyncSessionLocal
from app.models.kpi import PipelineScript

async def main():
    code = open('/tmp/pipeline_pai.py').read()
    async with AsyncSessionLocal() as db:
        await db.execute(update(PipelineScript).values(activo=False))
        db.add(PipelineScript(nombre='Pipeline PAI 2026', codigo=code, activo=True))
        await db.commit()
        print('✓ Pipeline activado')

asyncio.run(main())
PY
```

## Resumen del estado esperado

| Tabla | Cantidad |
|---|---|
| `indicadores_nivel1` | 6  (L1–L6) |
| `indicadores_nivel2` | 14 (un Producto por hoja) |
| `templates`          | 14 (todos `activo=true`) |
| `pipeline_scripts` (activo) | 1 (Pipeline PAI 2026) |
| `formularios_respondidos`   | 0 (esperando carga) |
| `kpi_resultados`            | 0 (regenera al aprobar forms) |

## Jerarquía PAI 2026

```
L1 — Investigación Humanitaria y Extrajudicial         (6 productos)
   ├── L1-P1-DPE-2026  Modelo operativo descentralizado
   ├── L1-P1-IHE-2026  Estrategia para la planificación de la IHE
   ├── L1-P2-IHE-2026  Sistema de Información Misional SIM Busquemos v2.0
   ├── L1-P3-IHE-2026  Estrategia de Gestión Integral del Dato y Analítica
   ├── L1-P4-IHE-2026  Estrategia Aportantes Consolidada
   └── L1-P5-IHE-2026  Estrategia Misión Identificación
L2 — Memoria y Legado                                   (1)
   └── L2-P1-CP-2026   Estrategia de Memoria y Legado
L3 — Articulación Interinstitucional                    (1)
   └── L3-P1-DPE-2026  Plan de Consolidación de la Articulación
L4 — Comunicaciones y Pedagogía                         (1)
   └── L4-P1-CP-2026   Estrategia Integral de Comunicaciones y Pedagogía
L5 — Participación de Familias y Personas Buscadoras    (1)
   └── L5-P1-PED-2026  Macro-estrategia de participación diferencial
L6 — Soporte Estratégico y Operativo                    (4)
   ├── L6-P1-DPE-2026  MOP 360: Radar de Gestión
   ├── L6-P1-GAF-2026  Modelo Integrado de Gestión Administrativa y Operativa
   ├── L6-P1-SGH-2026  Plan de Fortalecimiento SIBICU
   └── L6-P2-DPE-2026  SISPLAN BÚSQUEDA: Seguimiento y Monitoreo
```

## Pipeline PAI 2026

El script (`pipeline_pai.py`) recibe los formularios `approved` agrupados por
template y produce la estructura `nivel1[].subkpis[]` que consume el dashboard
público:

- Por **producto** (Nivel 2): promedio de `% Avance ponderado`, desglose por
  trimestre, estado (Cumple / Cumple Parcialmente / No Cumple / Sin Reporte).
- Por **línea** (Nivel 1): promedio de los productos.
- Estados con umbrales: ≥90% Cumple, 70–89% Cumple Parcialmente, <70% No Cumple, 0% Sin Reporte.

Cuando una dependencia carga formularios y el validador los aprueba, el pipeline
se ejecuta automáticamente (Celery) y actualiza `kpi_resultados`, alimentando
las páginas `/estadisticas` (KPIs públicos) y `/admin/indicadores`.

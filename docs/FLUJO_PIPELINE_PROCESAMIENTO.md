# Flujo del Pipeline de Procesamiento — UBPD

Cómo se calculan los KPIs del PAI 2026 a partir de los formularios respondidos,
desde la captura hasta los velocímetros del portal público.

---

## 1. Componentes

| Pieza | Ubicación | Rol |
|-------|-----------|-----|
| Script PAI | `scripts/pai_2026/pipeline_pai.py` | Lógica oficial del cálculo. |
| Seed embebido | `backend/app/seeds/pipeline_pai_default.py` | Copia incluida en la imagen del backend. |
| Tabla `pipeline_scripts` | PostgreSQL | Versión que actualmente se ejecuta. Solo una `activo = true`. |
| Tabla `kpi_resultados` | PostgreSQL | Valores finales que muestran los velocímetros. |
| Endpoint `/admin/script-pipeline/run` | Backend | Ejecuta el script activo y persiste KPIs. |
| Endpoint `/admin/script-pipeline/reset-to-default` | Backend | Restaura el seed y lo ejecuta. Usado por `prod.sh pipeline-reset`. |
| Logs | `logs/backend/pipeline/` | Histórico + un archivo por ejecución (`runs/run_<ts>.log`). |

---

## 2. Jerarquía de indicadores (PAI 2026)

```
Nivel 1 — Línea Estratégica (6 líneas: L1..L6)
  └── Nivel 2 — Producto (14 productos en total)
        └── Nivel 3 — Actividad (filas dentro del formulario)
```

Cada línea agrupa N productos (mapeo en `LINEA_BY_TEMPLATE`). Cada producto
corresponde a UN template (p.ej. `L6-P2-DPE-2026`). Las filas del Excel/formulario
son las actividades del producto, distribuidas por trimestre.

---

## 3. Variables de entrada (por actividad)

Campos llenados por la dependencia en cada fila del Excel o formulario:

| Campo | Tipo | Significado |
|-------|------|-------------|
| `periodo_reporte` | select | `TRIMESTRE 1..4` |
| `eje`, `peso_actividad`, `peso_trimestre` | varios | Metadatos de la actividad |
| `pct_avance_proyectado` | número | % planeado de avance de esa actividad en el periodo (peso/contribución al 100% del producto). |
| `pct_avance_alcanzado` | número | % realmente logrado. |

Campos llenados por el validador al aprobar (`validator_only`):

| Campo | Significado |
|-------|-------------|
| `obs_oap` | Observaciones y Recomendaciones OAP |
| `obs_oap_estado` | Observaciones OAP del Estado de Cumplimiento |

Campos calculados automáticamente (`auto_calculate`) — backend y frontend
los sobreescriben en cada save:

| Campo | Fórmula |
|-------|---------|
| `pct_avance_final` | `pct_avance_alcanzado / pct_avance_proyectado × 100`. **Escala 0–100** (no 0–1). Si `proyectado <= 0` → `null` ("No Aplica"). |
| `estado_actividad` | A partir de `pct_avance_final`: `≥90 → Cumple`, `≥70 → Cumple Parcialmente`, `>0 → No Cumple`, `null → No Aplica`. |

---

## 4. Cálculo a nivel de Producto (Nivel 2)

Definido en `_producto_metricas()` del script PAI:

1. **Filtrar actividades aplicables**: solo entran filas con `pct_avance_proyectado > 0`. Filas con proyectado vacío o 0 se consideran **"no aplica este periodo"** y se omiten por completo.
2. **Por trimestre T**: subconjunto de filas con `periodo_reporte = T`.
3. **Avance del producto en T** = `Σ pct_avance_alcanzado` de las filas aplicables. Esto da el % del 100% del producto que se logró ese periodo.
4. **Anual** = `Σ pct_avance_alcanzado` de **todas** las filas aplicables del año.
5. **Estado** del producto = derivado del **ratio** `Σalc / Σproy × 100`:
   - `≥90 → Cumple`
   - `≥70 → Cumple Parcialmente`
   - `>0 → No Cumple`
   - sin datos → `Sin Reporte`

### Ejemplo

Producto con 2 actividades en Trim 1:

| Actividad | Proyectado | Alcanzado |
|-----------|-----------|-----------|
| 1.1 | 3% | 2% |
| 1.2 | 7% | 5% |

- **Avance del producto** = `2 + 5 = 7%` (del 100% del producto).
- Ratio = `7 / 10 × 100 = 70%` → estado `Cumple Parcialmente`.

> El **avance** es lo que se guarda en `KpiResultado.valor` y aparece en el velocímetro.
> El **ratio** se guarda en `payload_json` y se muestra como subtítulo "X% del proyectado".

---

## 5. Cálculo a nivel de Línea (Nivel 1)

Definido en `_linea_metricas()`:

- La línea agrupa N productos (según `LINEA_BY_TEMPLATE`).
- **Avance de la línea** = **promedio aritmético** de los avances de **todos** sus productos.
- Productos sin datos cuentan como **0** en el promedio — la línea NO se beneficia de tener productos sin reportar.

### Ejemplo: Línea 6

Tiene 4 productos. Si solo `L6-P2-DPE-2026` tiene datos (avance 7%) y los otros 3 están "Sin Reporte":

```
avance_L6 = (0 + 0 + 0 + 7) / 4 = 1.75%
```

El promedio refleja el estado real de la línea: 3 productos sin reportar penalizan el promedio.

---

## 6. Filtro temporal en `/estadisticas`

El selector **Anual / Trim 1 / Trim 2 / Trim 3 / Trim 4** del portal público cambia qué versión del cálculo se muestra:

- `anual` → suma de todos los trimestres.
- `trim1..4` → solo las filas con `periodo_reporte = TRIMESTRE N`.

Cada `KpiResultado` guarda en `payload_json` un objeto:

```json
{
  "anual":         {"pct": 7.0,  "alc": 7.0,  "proy": 10.0, "estado": "Cumple Parcialmente"},
  "por_trimestre": {
    "TRIMESTRE 1": {"pct": 7.0,  "alc": 7.0,  "proy": 10.0, "estado": "Cumple Parcialmente"},
    "TRIMESTRE 2": {"pct": null, "alc": null, "proy": null, "estado": "Sin Reporte"},
    "TRIMESTRE 3": {"pct": null, "alc": null, "proy": null, "estado": "Sin Reporte"},
    "TRIMESTRE 4": {"pct": null, "alc": null, "proy": null, "estado": "Sin Reporte"}
  }
}
```

El endpoint `/stats/kpis?periodo=trim1` extrae `payload.por_trimestre."TRIMESTRE 1".pct` y lo devuelve como `valor`.

---

## 7. Ejecución del pipeline

### Vía CLI (recomendado)

```bash
# Restaurar al seed oficial + ejecutar (operación más segura)
./scripts/prod.sh pipeline-reset

# Sincronizar `scripts/pai_2026/pipeline_pai.py` como script activo
./scripts/prod.sh pipeline-sync run
```

Ambos comandos imprimen al final los valores guardados en `kpi_resultados` para verificación.

### Vía UI (Admin → Script Pipeline)

1. Editar el script en el editor.
2. **Guardar** (obligatorio antes de ejecutar — el botón Ejecutar usa el script ACTIVO en BD, no el textarea).
3. **Ejecutar en producción** → persiste los KPIs nuevos.

> ⚠️ Si pulsas "Ejecutar" sin Guardar, el sistema usa el script activo de la BD
> (no tu edición). El output incluye un aviso destacado en ese caso.

### Vía API

```bash
TOKEN=$(curl -s -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"..."}' | jq -r .access_token)

curl -X POST http://localhost/api/admin/script-pipeline/reset-to-default \
  -H "Authorization: Bearer $TOKEN"
```

---

## 8. Logs y diagnóstico

Cada ejecución genera **un archivo dedicado** en `logs/backend/pipeline/runs/run_<timestamp>_<modo>_<id>.log` con:

- Modo (test / produccion / reset-default) y usuario.
- Templates con datos y conteo de filas.
- STDOUT del script (mensajes `print` del propio script).
- Errores con traceback completo + snippet del script.
- KPIs guardados (nivel 1 y nivel 2).

Para ver el último run:

```bash
ls -t logs/backend/pipeline/runs/ | head -1
tail -100 logs/backend/pipeline/runs/run_<archivo>.log
```

Para seguir el histórico en vivo:

```bash
tail -f logs/backend/pipeline/pipeline.log
```

---

## 9. Sandbox del script

El script se ejecuta con `exec(compile(code, ...))` dentro de un thread con
**timeout de 60s** y un `__builtins__` restringido. Variables inyectadas:

| Variable | Tipo | Contenido |
|----------|------|-----------|
| `dfs` | `dict[codigo, pd.DataFrame]` | Un DataFrame por template con los `datos_dinamicos` de los formularios APROBADOS. Las claves son los códigos de template (`L6-P2-DPE-2026`, etc.). |
| `template_meta` | `dict[codigo, dict]` | Metadatos: `id`, `nombre` (largo, p.ej. "L6-P2-DPE-2026 — SISPLAN - BÚSQUEDA: ..."), `codigo`. |
| `pd` / `pandas` | módulo | Pandas. |
| `np` / `numpy` | módulo | Numpy. |
| `math`, `re`, `json`, `datetime`, `collections` | módulos | Std lib útil. |

Builtins permitidos: tipos básicos, `len/range/zip/enumerate/sum/min/max`,
`isinstance/type`, `print` (capturado), `object/super/property/classmethod/staticmethod`,
`__build_class__` (necesario para definir clases).

**Output esperado**: la variable `resultado` debe ser un `dict` con `nivel1`
(lista) y `nivel2` (dict por línea con sub-listas). Estructura completa en
`scripts/pai_2026/pipeline_pai.py`.

---

## 10. Flujo completo (de la dependencia al velocímetro)

```
[Dependencia carga Excel]
        │
        ▼
formularios_respondidos.datos_dinamicos  (recalc auto_calculate en backend)
        │
        ▼
[Validador aprueba lote]  →  estado = approved, completa OAP
        │
        ▼
[Admin ejecuta pipeline]  →  pipeline-reset / pipeline-sync run / UI
        │
        ▼
_load_dataframes(db)  →  dfs[codigo] = pd.DataFrame(datos_dinamicos)
        │
        ▼
_producto_metricas(df)  →  por_trimestre + anual con pct=Σalc, estado=ratio
        │
        ▼
_linea_metricas(linea_id)  →  promedio aritmético de los productos
        │
        ▼
kpi_resultados  (UPSERT por kpi_key + payload_json con desglose)
        │
        ▼
GET /stats/kpis?periodo=...  →  velocímetros del portal público
```

---

## 11. Errores comunes y solución

| Síntoma | Causa | Solución |
|---------|-------|----------|
| Velocímetros en 0% con datos cargados | Pipeline nunca se ejecutó tras la carga | `./scripts/prod.sh pipeline-reset` |
| Aparecen indicadores genéricos (Calidad, Cobertura, …) | Script activo en BD es el ejemplo, no el PAI | `./scripts/prod.sh pipeline-reset` |
| Valores en BD distintos a los del velocímetro | Caché del navegador | `Cmd/Ctrl + Shift + R` |
| Pipeline falla con `SyntaxError __build_class__` | Sandbox sin `__build_class__` (fix ya aplicado en main) | Reconstruir backend: `./scripts/prod.sh build backend` |
| Editor muestra ejemplo en lugar del PAI | Tabla `pipeline_scripts` vacía | El backend siembra el PAI al arrancar; si no, ejecutar `pipeline-reset` |

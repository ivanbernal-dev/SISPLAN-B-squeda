#!/usr/bin/env python3
"""
Instala el script de pipeline oficial en el editor de admin.

Uso:
  python scripts/instalar_pipeline.py [BASE_URL] [USUARIO] [PASSWORD]
"""
import sys

try:
    import requests
except ImportError:
    print("ERROR: pip install requests"); sys.exit(1)

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost/api"
USUARIO  = sys.argv[2] if len(sys.argv) > 2 else "admin"
PASSWORD = sys.argv[3] if len(sys.argv) > 3 else "Admin@UBPD2024!"

# ─────────────────────────────────────────────────────────────────────────────
# SCRIPT DE PIPELINE
# Se guarda tal cual en el editor de admin (/admin/script-pipeline)
# ─────────────────────────────────────────────────────────────────────────────
PIPELINE_SCRIPT = r"""
# =============================================================================
# UBPD — Script Pipeline de Indicadores de Gestión
# =============================================================================
# Calcula indicadores de avance a partir de formularios aprobados.
#
# Variables disponibles:
#   dfs           → dict: nombre_template → DataFrame (formularios aprobados)
#   template_meta → dict: nombre_template → {id, nombre, codigo}
#   pd            → pandas
#
# Columna de cálculo principal:
#   reporte_cuantitativo_variable_1  →  numerador  (escala 0-1 ó 0-100)
#   reporte_cuantitativo_variable_2  →  denominador (meta)
#
# Estructura de salida:
#   resultado = {
#       "nivel1": [ {key, label, valor, descripcion} ... ],   # máx 5
#       "nivel2": { "kpi_key_padre": [ {key, label, valor, template_id} ... ] }
#   }
# =============================================================================

import re

# ── 1. Definición de líneas estratégicas (nivel 1) ────────────────────────────
LINEAS = {
    "L1": {
        "key":        "kpi_linea1",
        "label":      "Línea 1 — Investigación Humanitaria y Extrajudicial",
        "descripcion":"IHE: investigación, forense, identificación y búsqueda territorial",
    },
    "L2": {
        "key":        "kpi_linea2",
        "label":      "Línea 2 — Participación y Gestión Territorial",
        "descripcion":"Articulación con víctimas, familias y organizaciones de búsqueda",
    },
    "L3": {
        "key":        "kpi_linea3",
        "label":      "Línea 3 — Despliegue y Modelo Operativo",
        "descripcion":"Consolidación del modelo operativo descentralizado",
    },
    "L4": {
        "key":        "kpi_linea4",
        "label":      "Línea 4 — Gestión del Conocimiento",
        "descripcion":"Sistematización, aprendizaje institucional y gestión del dato",
    },
    "L5": {
        "key":        "kpi_linea5",
        "label":      "Línea 5 — Coordinación y Articulación Interinstitucional",
        "descripcion":"Coordinación con entidades del SIVJRNR y cooperación internacional",
    },
}

# ── 2. Columnas de cálculo ────────────────────────────────────────────────────
# var1: avance logrado del mes (fraccion 0-1 o porcentaje 0-100)
# var2: meta / denominador (si es mayor y distinta a var1, se usa como divisor)
COL_NUMERADOR   = "reporte_cuantitativo_variable_1"
COL_DENOMINADOR = "reporte_cuantitativo_variable_2"

print("=" * 60)
print("UBPD — Pipeline de Indicadores")
print("=" * 60)
print(f"Templates con datos: {[n for n, df in dfs.items() if not df.empty]}")
print()

def extraer_linea(codigo):
    # 'L1-P1-DPE-2026' -> 'L1'
    m = re.match(r"^(L\d+)", str(codigo).upper())
    return m.group(1) if m else None

def calcular_avance(df):
    # Promedio de var1 como fraccion de avance.
    # Si var2 existe y es significativamente mayor que var1 (denominador tipo conteo),
    # calcula var1/var2 por fila. En caso contrario usa var1 directamente.
    # Normaliza a escala 0-100 si los valores estan en rango 0-1.
    # Clampea al rango [0, 100].
    if df.empty:
        return 0.0

    num_col = COL_NUMERADOR if COL_NUMERADOR in df.columns else None
    den_col = COL_DENOMINADOR if COL_DENOMINADOR in df.columns else None

    if num_col is None:
        return 0.0

    numeradores = pd.to_numeric(df[num_col], errors="coerce").dropna()
    if numeradores.empty:
        return 0.0

    # Decidir si usar var2 como denominador real (tipo conteo):
    # solo cuando var2 existe y su media es notablemente mayor que la de var1
    usar_division = False
    if den_col and den_col in df.columns:
        denominadores = pd.to_numeric(df[den_col], errors="coerce").dropna()
        if len(denominadores) == len(numeradores) and not denominadores.empty:
            media_num = numeradores.mean()
            media_den = denominadores.mean()
            # Solo dividir si el denominador es al menos 1.5x mayor (conteo vs fraccion)
            if media_den > 0 and media_den > media_num * 1.5:
                ratios = []
                for n, d in zip(numeradores.values, denominadores.values):
                    if d and d > 0:
                        ratios.append(n / d)
                    else:
                        ratios.append(n)
                promedio = float(pd.Series(ratios).mean())
                usar_division = True

    if not usar_division:
        # Usar var1 directamente como proporcion de avance
        promedio = float(numeradores.mean())

    # Normalizar a 0-100
    if promedio <= 1.0:
        promedio *= 100.0

    return round(min(100.0, max(0.0, promedio)), 1)

# ── 3. Calcular KPIs nivel 2 (uno por template) ───────────────────────────────
nivel2_por_linea = {k: [] for k in LINEAS}

for nombre, df in dfs.items():
    meta     = template_meta.get(nombre, {})
    codigo   = meta.get("codigo", "")
    tid      = meta.get("id")
    linea_k  = extraer_linea(codigo)

    if not linea_k or linea_k not in LINEAS:
        print(f"  ⚠  Template sin línea reconocida: '{codigo}' — omitido")
        continue

    valor = calcular_avance(df)

    # Label: parte descriptiva del nombre (quitar el código del inicio)
    label = nombre
    for sep in [" — ", " - ", ": "]:
        if sep in nombre:
            label = nombre.split(sep, 1)[-1].strip()
            break
    label = label[:80]

    # Key única basada en el código
    key = "kpi_" + re.sub(r"[^a-z0-9]", "_", codigo.lower()).strip("_")

    print(f"  [{linea_k}] {codigo}")
    print(f"         Registros aprobados: {len(df)}")
    print(f"         Valor calculado:     {valor}%")
    print()

    nivel2_por_linea[linea_k].append({
        "key":         key,
        "label":       label,
        "valor":       valor,
        "template_id": tid,
    })

# ── 4. Calcular KPIs nivel 1 (promedio de los nivel 2 de cada línea) ──────────
nivel1_items  = []
nivel2_output = {}

print("─" * 60)
print("Resumen por línea estratégica:")
print()

for linea_k, linea_def in LINEAS.items():
    items_n2 = nivel2_por_linea[linea_k]

    # Valor nivel 1 = promedio de los KPIs nivel 2 que tienen datos
    con_datos = [i for i in items_n2 if i["valor"] > 0]
    if con_datos:
        valor_n1 = round(sum(i["valor"] for i in items_n2) / len(items_n2), 1)
    else:
        valor_n1 = 0.0

    print(f"  {linea_k}: {len(items_n2)} template(s) con datos → {valor_n1}%")

    nivel1_items.append({
        "key":         linea_def["key"],
        "label":       linea_def["label"],
        "valor":       valor_n1,
        "descripcion": linea_def["descripcion"],
    })

    # Rellenar hasta 5 sub-KPIs para la UI de velocímetros
    n2_ui = list(items_n2)
    while len(n2_ui) < 5:
        idx = len(n2_ui) + 1
        n2_ui.append({
            "key":   f"{linea_def['key']}_placeholder_{idx}",
            "label": f"Producto {idx}",
            "valor": 0.0,
        })

    nivel2_output[linea_def["key"]] = n2_ui[:5]   # la UI muestra máx 5

# ── 5. Construir resultado ────────────────────────────────────────────────────
resultado = {
    "nivel1": nivel1_items,
    "nivel2": nivel2_output,
}

print()
print("=" * 60)
print("KPIs nivel 1 calculados:")
for item in nivel1_items:
    barra = "█" * int(item["valor"] / 5) if item["valor"] > 0 else "·"
    print(f"  {item['label'][:45]:<45} {item['valor']:5.1f}%  {barra}")
print()
print("✓ Pipeline ejecutado correctamente")
""".strip()

# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(f"\nConectando a {BASE_URL} como '{USUARIO}'...")
    s = requests.Session()

    r = s.post(f"{BASE_URL}/auth/login",
               json={"username": USUARIO, "password": PASSWORD}, timeout=10)
    if r.status_code != 200:
        print(f"ERROR login: {r.status_code} {r.text[:200]}"); sys.exit(1)

    s.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})

    r = s.post(f"{BASE_URL}/admin/script-pipeline/save",
               json={"codigo": PIPELINE_SCRIPT, "nombre": "Pipeline Indicadores UBPD 2026"},
               timeout=15)
    if r.status_code == 200:
        print("✓ Script instalado correctamente en el editor de admin")
        print("  → Abre /admin/script-pipeline y ejecuta en modo prueba primero")
    else:
        print(f"ERROR al guardar: {r.status_code} {r.text[:300]}")
        sys.exit(1)

if __name__ == "__main__":
    main()

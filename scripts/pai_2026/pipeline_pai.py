"""
Pipeline PAI 2026 — UBPD
========================
Calcula los KPIs públicos consolidando los formularios respondidos por
template (= Producto del PAI), agrupándolos en sus respectivas Líneas
Estratégicas (Nivel 1).

Convención (espejo de la jerarquía en BD):
  Nivel 1 → Línea Estratégica   (L1, L2, ..., L6)
    Nivel 2 → Producto del PAI  (cada hoja del Excel)
      Template → Form (avance reportado por una dependencia)

Variables disponibles (inyectadas por el executor):
  dfs       — dict { template_codigo: pd.DataFrame de forms approved }
  pd        — pandas
  resultado — dict que el script DEBE poblar con la estructura final
"""

# ── 1) Mapa codigo_template → línea estratégica ────────────────────────────
# (Coincide con los Niveles 1 sembrados en la BD)
LINEA_BY_TEMPLATE = {
    "L1-P1-DPE-2026":  1, "L1-P1-IHE-2026": 1, "L1-P2-IHE-2026": 1,
    "L1-P3-IHE-2026":  1, "L1-P4-IHE-2026": 1, "L1-P5-IHE-2026": 1,
    "L2-P1-CP-2026":   2,
    "L3-P1-DPE-2026":  3,
    "L4-P1-CP-2026":   4,
    "L5-P1-PED-2026":  5,
    "L6-P1-DPE-2026":  6, "L6-P1-GAF-2026": 6,
    "L6-P1-SGH-2026":  6, "L6-P2-DPE-2026": 6,
}

LINEA_NOMBRE = {
    1: "Línea 1 — Investigación Humanitaria y Extrajudicial",
    2: "Línea 2 — Memoria y Legado",
    3: "Línea 3 — Articulación Interinstitucional",
    4: "Línea 4 — Comunicaciones y Pedagogía",
    5: "Línea 5 — Participación de Familias y Personas Buscadoras",
    6: "Línea 6 — Soporte Estratégico y Operativo",
}


def _avg_pct(serie):
    """Promedio robusto de una serie (ignora NaN)."""
    s = pd.to_numeric(serie, errors="coerce").dropna()
    return float(s.mean()) if len(s) else 0.0


def _proceso_template(codigo, df):
    """
    Para un template (= producto), calcula:
      pct_ponderado_promedio: promedio de '% Avance ponderado del producto'
      pct_alcanzado_promedio: promedio de '% Avance acumulado Alcanzado'
      n_forms:                cantidad de formularios approved
      por_trimestre:          promedio por trimestre
    """
    if df is None or len(df) == 0:
        return {
            "codigo": codigo,
            "n_forms": 0,
            "pct_ponderado": 0.0,
            "pct_alcanzado": 0.0,
            "por_trimestre": {},
            "estado": "Sin Reporte",
        }

    # Aplanar datos_dinamicos (los forms vienen ya como columnas en el df)
    pct_pond = _avg_pct(df.get("pct_avance_ponderado", []))
    pct_alc  = _avg_pct(df.get("pct_avance_alcanzado", []))

    # Por trimestre
    por_trim = {}
    if "periodo_reporte" in df.columns:
        for trim, sub in df.groupby("periodo_reporte"):
            por_trim[str(trim)] = round(_avg_pct(sub.get("pct_avance_alcanzado", [])) * 100, 2)

    # Estado consolidado a nivel de producto
    if   pct_pond >= 0.90: estado = "Cumple"
    elif pct_pond >= 0.70: estado = "Cumple Parcialmente"
    elif pct_pond >  0:    estado = "No Cumple"
    else:                  estado = "Sin Reporte"

    return {
        "codigo": codigo,
        "n_forms": int(len(df)),
        "pct_ponderado": round(pct_pond * 100, 2),   # como porcentaje 0-100
        "pct_alcanzado": round(pct_alc  * 100, 2),
        "por_trimestre": por_trim,
        "estado": estado,
    }


# ── 2) Procesar cada producto ──────────────────────────────────────────────
productos = []
for codigo in LINEA_BY_TEMPLATE.keys():
    df = dfs.get(codigo)
    productos.append(_proceso_template(codigo, df))


# ── 3) Agregar por línea estratégica ───────────────────────────────────────
nivel1 = []
for linea_id, linea_nombre in LINEA_NOMBRE.items():
    productos_linea = [p for p in productos
                       if LINEA_BY_TEMPLATE[p["codigo"]] == linea_id]
    pct_avg = round(
        sum(p["pct_ponderado"] for p in productos_linea) / max(len(productos_linea), 1),
        2,
    )
    n_total = sum(p["n_forms"] for p in productos_linea)

    if   pct_avg >= 90: estado = "Cumple"
    elif pct_avg >= 70: estado = "Cumple Parcialmente"
    elif pct_avg >  0:  estado = "No Cumple"
    else:               estado = "Sin Reporte"

    nivel1.append({
        "id":       linea_id,
        "key":      f"L{linea_id}",
        "nombre":   linea_nombre,
        "pct":      pct_avg,
        "estado":   estado,
        "n_forms":  n_total,
        "subkpis":  [
            {
                "key":     p["codigo"],
                "nombre":  p["codigo"],
                "pct":     p["pct_ponderado"],
                "estado":  p["estado"],
                "n_forms": p["n_forms"],
                "por_trimestre": p["por_trimestre"],
            }
            for p in productos_linea
        ],
    })


# ── 4) Resultado final que consume el dashboard público ────────────────────
resultado = {
    "version":  "PAI-2026",
    "nivel1":   nivel1,
    "totales":  {
        "n_lineas":      len(nivel1),
        "n_productos":   len(productos),
        "n_forms_total": sum(p["n_forms"] for p in productos),
        "pct_global":    round(
            sum(l["pct"] for l in nivel1) / max(len(nivel1), 1), 2
        ),
    },
}

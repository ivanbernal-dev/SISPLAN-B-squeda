"""
Pipeline PAI 2026 — UBPD
========================
Consolida los formularios aprobados de cada template (= Producto del PAI)
y produce velocímetros en dos niveles para el dashboard público de
/estadisticas:

  Nivel 1 → Línea Estratégica  (L1..L6) — velocímetro promedio de productos
  Nivel 2 → Producto del PAI   (uno por hoja del Excel) — velocímetro propio

Cada nivel se calcula por TRIMESTRE (T1..T4) y como ANUAL (acumulado).
El frontend escoge cuál mostrar según el selector temporal.

Fórmulas (replican el Excel original):
  pct_avance_ponderado(trim) = Σ alcanzado / Σ proyectado de las actividades de ese trim
  pct_avance_anual           = Σ pct_avance_alcanzado / Σ pct_avance_proyectado (todo el año)
  estado_ponderado(pct)      = >=90% Cumple, 70-89% Parcialmente, <70% No Cumple
"""

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

TRIMESTRES = ["TRIMESTRE 1", "TRIMESTRE 2", "TRIMESTRE 3", "TRIMESTRE 4"]


def _to_num_opt(s):
    """Convierte a número manteniendo NaN para vacíos (no rellena con 0)."""
    return pd.to_numeric(s, errors="coerce")


def _estado(pct):
    if pct is None:    return "Sin Reporte"
    if pct >= 90:      return "Cumple"
    if pct >= 70:      return "Cumple Parcialmente"
    if pct > 0:        return "No Cumple"
    return "Sin Reporte"


def _producto_metricas(df):
    """Calcula avance por trimestre y anual de un producto.

    Regla clave: una actividad/fila SOLO entra al cálculo si
    `pct_avance_proyectado` está reportado y > 0. Si la celda está vacía
    (o el proyectado es 0) significa que esa actividad NO APLICA ese
    periodo → se omite por completo. Si `pct_avance_alcanzado` está vacío
    pero el proyectado existe → cuenta como 0 logrado (no aplica = 0%).

    Si en un trimestre/anual no queda NINGUNA fila con proyección válida,
    el resultado es `pct: None, estado: "Sin Reporte"`. Esos productos NO
    deben entrar al promedio de la línea (se filtran en _linea_metricas).
    """
    vacio = {
        "n_forms": 0,
        "anual":   {"pct": None, "estado": "Sin Reporte", "n_forms": 0},
        "por_trimestre": {t: {"pct": None, "estado": "Sin Reporte", "n_forms": 0}
                          for t in TRIMESTRES},
    }
    if df is None or len(df) == 0:
        return vacio
    df = df.copy()
    for col in ("pct_avance_alcanzado", "pct_avance_proyectado"):
        if col not in df.columns:
            df[col] = None
    if "periodo_reporte" not in df.columns:
        df["periodo_reporte"] = "TRIMESTRE 1"

    df["_proy"] = _to_num_opt(df["pct_avance_proyectado"])
    # Alcanzado faltante → 0 logrado (siempre que haya proyección)
    df["_alc"]  = _to_num_opt(df["pct_avance_alcanzado"]).fillna(0)
    # Una fila aplica solo si tiene proyección reportada y > 0
    df["_aplica"] = df["_proy"].notna() & (df["_proy"] > 0)

    por_trim = {}
    for t in TRIMESTRES:
        sub = df[(df["periodo_reporte"] == t) & df["_aplica"]]
        if len(sub) == 0:
            por_trim[t] = {"pct": None, "estado": "Sin Reporte", "n_forms": 0}
        else:
            sub_proy = float(sub["_proy"].sum())
            sub_alc  = float(sub["_alc"].sum())
            pct = (sub_alc / sub_proy * 100.0) if sub_proy > 0 else None
            por_trim[t] = {
                "pct":     round(pct, 2) if pct is not None else None,
                "estado":  _estado(pct),
                "n_forms": int(len(sub)),
            }

    aplica_total = df[df["_aplica"]]
    if len(aplica_total) == 0:
        pct_anual = None
    else:
        tot_proy = float(aplica_total["_proy"].sum())
        tot_alc  = float(aplica_total["_alc"].sum())
        pct_anual = (tot_alc / tot_proy * 100.0) if tot_proy > 0 else None
    return {
        "n_forms": int(len(df)),
        "anual":   {
            "pct":     round(pct_anual, 2) if pct_anual is not None else None,
            "estado":  _estado(pct_anual),
            "n_forms": int(len(aplica_total)),
        },
        "por_trimestre": por_trim,
    }


# 1) Procesar cada producto
productos = {}
for codigo in LINEA_BY_TEMPLATE.keys():
    productos[codigo] = _producto_metricas(dfs.get(codigo))


# 2) Promediar por Línea — ignora productos/trimestres SIN proyección reportada
def _linea_metricas(linea_id):
    codigos = [c for c, l in LINEA_BY_TEMPLATE.items() if l == linea_id]
    plinea = [productos[c] for c in codigos]
    n_total = sum(p["n_forms"] for p in plinea)
    # Solo se promedian productos cuyo anual.pct NO sea None (es decir, que
    # tengan al menos una actividad con proyección reportada en el año).
    pcts = [p["anual"]["pct"] for p in plinea if p["anual"]["pct"] is not None]
    anual_pct = round(sum(pcts) / len(pcts), 2) if pcts else None
    por_trim = {}
    for t in TRIMESTRES:
        ts = [p["por_trimestre"][t]["pct"]
              for p in plinea if p["por_trimestre"][t]["pct"] is not None]
        ppct = round(sum(ts) / len(ts), 2) if ts else None
        por_trim[t] = {"pct": ppct, "estado": _estado(ppct)}
    return {
        "id":     linea_id,
        "key":    f"L{linea_id}",
        "label":  LINEA_NOMBRE[linea_id],
        "n_forms": n_total,
        "anual":  {"pct": anual_pct, "estado": _estado(anual_pct)},
        "por_trimestre": por_trim,
    }


nivel1_list = [_linea_metricas(lid) for lid in sorted(LINEA_NOMBRE)]

nivel2_dict = {}
for linea_id in LINEA_NOMBRE:
    key = f"L{linea_id}"
    items = []
    for codigo, l in LINEA_BY_TEMPLATE.items():
        if l != linea_id:
            continue
        p = productos[codigo]
        items.append({
            "key":     codigo,
            "label":   codigo,
            "n_forms": p["n_forms"],
            "anual":   p["anual"],
            "por_trimestre": p["por_trimestre"],
        })
    nivel2_dict[key] = items


# 3) Formato plano compatible con /stats/kpis. La columna valor del KPI
#    debe ser numérica (Float en la BD): si anual.pct es None ("Sin Reporte")
#    se guarda como 0.0 — el payload_json preserva el None para que la UI
#    pueda distinguir "0% logrado" vs "no aplica / sin reporte".
def _v(x):
    return float(x) if x is not None else 0.0


nivel1_plano = [
    {
        "key":         n["key"],
        "label":       n["label"],
        "valor":       _v(n["anual"]["pct"]),
        "descripcion": f"{n['n_forms']} formularios aprobados",
        "anual":       n["anual"],
        "por_trimestre": n["por_trimestre"],
    }
    for n in nivel1_list
]

nivel2_plano = {}
for k, items in nivel2_dict.items():
    nivel2_plano[k] = [
        {
            "key":         i["key"],
            "label":       i["label"],
            "valor":       _v(i["anual"]["pct"]),
            "descripcion": f"{i['n_forms']} formularios",
            "anual":       i["anual"],
            "por_trimestre": i["por_trimestre"],
        }
        for i in items
    ]


# 4) Resultado final
resultado = {
    "version":  "PAI-2026",
    "nivel1":   nivel1_plano,
    "nivel2":   nivel2_plano,
    "totales":  {
        "n_lineas":      len(nivel1_plano),
        "n_productos":   len(productos),
        "n_forms_total": sum(p["n_forms"] for p in productos.values()),
    },
}

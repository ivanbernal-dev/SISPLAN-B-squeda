"""
Pipeline PAI 2026 — UBPD
========================
Consolida los formularios aprobados de cada template (= Producto del PAI)
y produce velocímetros en dos niveles para el dashboard público de
/estadisticas:

  Nivel 1 → Línea Estratégica  (L1..L6) — promedio del avance real de TODOS sus productos
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

    Semántica: los valores `pct_avance_proyectado` y `pct_avance_alcanzado`
    de cada fila son CONTRIBUCIONES (pesos) al 100% del producto. Por eso
    el avance del producto en un periodo es la SUMA de los alcanzados de
    las actividades de ese periodo, NO el ratio.

    Reglas:
      - Una fila solo entra si pct_avance_proyectado > 0 (sino "no aplica").
      - Si alcanzado está vacío y proyectado existe, cuenta como 0 logrado.
      - pct = Σ alc (suma directa, sin dividir por proy).
      - estado se evalúa con el RATIO Σalc/Σproy (cumplimiento del periodo):
          ≥90% → Cumple, ≥70% → Cumple Parcialmente, >0 → No Cumple, sino → No Aplica.
      - Si no hay filas aplicables, pct=None, estado="Sin Reporte".
    """
    vacio = {
        "n_forms": 0,
        "anual":   {"pct": None, "alc": None, "proy": None,
                    "estado": "Sin Reporte", "n_forms": 0},
        "por_trimestre": {t: {"pct": None, "alc": None, "proy": None,
                              "estado": "Sin Reporte", "n_forms": 0}
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
    df["_alc"]  = _to_num_opt(df["pct_avance_alcanzado"]).fillna(0)
    df["_aplica"] = df["_proy"].notna() & (df["_proy"] > 0)

    def _metricas_subset(sub):
        if len(sub) == 0:
            return {"pct": None, "alc": None, "proy": None,
                    "estado": "Sin Reporte", "n_forms": 0}
        sub_proy = float(sub["_proy"].sum())
        sub_alc  = float(sub["_alc"].sum())
        # pct = avance del producto = SUMA de los alcanzados
        pct = sub_alc
        # estado se basa en el ratio (cumplimiento del proyectado)
        ratio = (sub_alc / sub_proy * 100.0) if sub_proy > 0 else None
        return {
            "pct":     round(pct, 2),
            "alc":     round(sub_alc, 2),
            "proy":    round(sub_proy, 2),
            "estado":  _estado(ratio),
            "n_forms": int(len(sub)),
        }

    por_trim = {t: _metricas_subset(df[(df["periodo_reporte"] == t) & df["_aplica"]])
                for t in TRIMESTRES}
    anual = _metricas_subset(df[df["_aplica"]])
    return {
        "n_forms": int(len(df)),
        "anual":   anual,
        "por_trimestre": por_trim,
    }


# 1) Procesar cada producto
productos = {}
for codigo in LINEA_BY_TEMPLATE.keys():
    productos[codigo] = _producto_metricas(dfs.get(codigo))


# 2) Promediar por Línea — ignora productos/trimestres SIN proyección reportada
def _linea_metricas(linea_id):
    """Avance de la línea = promedio aritmético de TODOS los velocímetros
    de nivel 2 (productos de la línea). Los productos sin datos cuentan
    como 0 — la línea no se beneficia de tener productos sin reportar.
    """
    codigos = [c for c, l in LINEA_BY_TEMPLATE.items() if l == linea_id]
    plinea = [productos[c] for c in codigos]
    n_total = sum(p["n_forms"] for p in plinea)

    def _avg(values):
        # values puede contener None (Sin Reporte) — se convierten a 0
        # para que cuenten en el divisor (el promedio refleje TODOS los
        # productos de la línea, no solo los que ya tienen datos).
        if not values:
            return None
        # IMPORTANTE: se promedian los avances reales (`pct`) del producto,
        # nunca su ratio de cumplimiento alc/proy. Ejemplo Línea 6:
        # [0, 0, 0, 23.7] / 4 productos = 5.925%, no 87.8%.
        nums = [v if v is not None else 0.0 for v in values]
        return round(sum(nums) / len(nums), 2)

    anual_pct = _avg([p["anual"]["pct"] for p in plinea])
    por_trim = {}
    for t in TRIMESTRES:
        vals = [p["por_trimestre"][t]["pct"] for p in plinea]
        ppct = _avg(vals)
        por_trim[t] = {"pct": ppct, "estado": _estado(ppct)}

    # Estado de la línea anual: se basa en el AVANCE (mismo umbral que
    # los productos). Si todos están en 0, marca "Sin Reporte".
    if anual_pct is None or anual_pct == 0:
        estado_anual = "Sin Reporte"
    else:
        estado_anual = _estado(anual_pct)

    return {
        "id":     linea_id,
        "key":    f"L{linea_id}",
        "label":  LINEA_NOMBRE[linea_id],
        "n_forms": n_total,
        "anual":  {"pct": anual_pct, "estado": estado_anual},
        "por_trimestre": por_trim,
    }


nivel1_list = [_linea_metricas(lid) for lid in sorted(LINEA_NOMBRE)]

nivel2_dict = {}
# template_meta llega como variable global del sandbox (inyectado por
# _load_dataframes). Lo usamos para conseguir el NOMBRE LARGO del template
# (p. ej. "L6-P2-DPE-2026 — SISPLAN - BÚSQUEDA: ...") en lugar de
# mostrar solo el código. Si no está disponible, cae al código.
try:
    _META = template_meta or {}
except NameError:
    _META = {}

def _label_producto(codigo):
    info = _META.get(codigo) or {}
    nombre = (info.get("nombre") or "").strip()
    return nombre if nombre else codigo

for linea_id in LINEA_NOMBRE:
    key = f"L{linea_id}"
    items = []
    for codigo, l in LINEA_BY_TEMPLATE.items():
        if l != linea_id:
            continue
        p = productos[codigo]
        items.append({
            "key":     codigo,
            "label":   _label_producto(codigo),
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

"""
app/services/auto_calc.py — Cálculo automático de campos del template.

Cuando un FieldConfig tiene `auto_calculate`, el valor se recalcula SIEMPRE
al guardar/cargar (sobreescribe cualquier valor enviado por la dependencia o
proveniente del Excel).

Fórmulas soportadas (canónicas para PAI 2026):

  "ratio_alcanzado_proyectado"
      valor = pct_avance_alcanzado / pct_avance_proyectado  (fracción 0..1)
      Si proyectado <= 0 o falta dato → None (se mostrará como "No Aplica")

  "estado_cumplimiento_from_pct_final"
      Toma `pct_avance_final` (fracción 0..1) y devuelve:
          >= 0.90 → "Cumple"
          >= 0.70 → "Cumple Parcialmente"
          >  0    → "No Cumple"
          None    → "No Aplica"
"""
from __future__ import annotations

from typing import Any, Iterable


def _to_float(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None


def recalc_auto_fields(
    datos: dict[str, Any],
    fields: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """
    Recalcula in-place los campos con `auto_calculate` y devuelve el dict.
    Las fórmulas se aplican EN ORDEN: primero ratio (necesario para estado).
    """
    fields_list = list(fields)

    # Paso 1: cualquier ratio_alcanzado_proyectado
    for f in fields_list:
        if f.get("auto_calculate") != "ratio_alcanzado_proyectado":
            continue
        name = f.get("name")
        if not name:
            continue
        proj = _to_float(datos.get("pct_avance_proyectado"))
        alc  = _to_float(datos.get("pct_avance_alcanzado"))
        if proj is None or alc is None or proj <= 0:
            datos[name] = None   # → "No Aplica"
        else:
            datos[name] = round(alc / proj, 4)

    # Paso 2: estados que dependen de pct_avance_final ya calculado
    for f in fields_list:
        if f.get("auto_calculate") != "estado_cumplimiento_from_pct_final":
            continue
        name = f.get("name")
        if not name:
            continue
        v = datos.get("pct_avance_final")
        pct_f = _to_float(v)
        if pct_f is None:
            datos[name] = "No Aplica"
        else:
            pct = pct_f * 100.0
            if   pct >= 90: datos[name] = "Cumple"
            elif pct >= 70: datos[name] = "Cumple Parcialmente"
            elif pct >  0:  datos[name] = "No Cumple"
            else:           datos[name] = "No Aplica"

    return datos

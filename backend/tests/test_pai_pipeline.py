"""Pruebas de la fórmula oficial del Plan de Acción Institucional 2026."""
from pathlib import Path

import pandas as pd
import pytest


def _run_seed(dfs: dict[str, pd.DataFrame]) -> dict:
    seed = Path(__file__).resolve().parents[1] / "app" / "seeds" / "pipeline_pai_default.py"
    namespace = {"pd": pd, "dfs": dfs, "template_meta": {}}
    exec(compile(seed.read_text(encoding="utf-8"), str(seed), "exec"), namespace)
    return namespace["resultado"]


def test_linea_6_promedia_avance_real_de_todos_los_productos() -> None:
    """23.7 de un único producto en una línea de cuatro equivale a ~5.9%."""
    result = _run_seed({
        "L6-P2-DPE-2026": pd.DataFrame([
            {
                "periodo_reporte": "TRIMESTRE 1",
                "pct_avance_proyectado": 27.0,
                "pct_avance_alcanzado": 23.7,
            },
        ]),
    })

    linea_6 = next(item for item in result["nivel1"] if item["key"] == "L6")
    producto = next(item for item in result["nivel2"]["L6"] if item["key"] == "L6-P2-DPE-2026")

    assert producto["valor"] == pytest.approx(23.7)
    assert linea_6["valor"] == pytest.approx(23.7 / 4, abs=0.01)
    assert linea_6["valor"] != pytest.approx(23.7 / 27.0 * 100)

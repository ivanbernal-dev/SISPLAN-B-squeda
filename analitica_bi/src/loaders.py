"""
analitica_bi/src/loaders.py

Utilidades para cargar los datos BI desde dos fuentes diferentes con el MISMO
esquema de retorno:

    {
        "PRB":                   pd.DataFrame,
        "EstructuraIndicadores": pd.DataFrame,
        "Historico":             pd.DataFrame,
    }

Esto permite intercambiar fácilmente la fuente de datos dentro de los notebooks
y comparar que los resultados Excel == Base de datos.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd
import requests


# ══════════════════════════════════════════════════════════════════════════════
# Fuente 1: Excel
# ══════════════════════════════════════════════════════════════════════════════

def load_from_excel(path: str | Path) -> Dict[str, pd.DataFrame]:
    """
    Carga las 3 hojas relevantes del Excel y las devuelve como un dict de
    DataFrames con el mismo esquema que la base de datos.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el Excel: {path}")

    xl = pd.ExcelFile(path)
    required = {"PRB", "EstructuraIndicadores", "Historico"}
    missing = required - set(xl.sheet_names)
    if missing:
        raise ValueError(f"Faltan hojas en el Excel: {missing}. Disponibles: {xl.sheet_names}")

    return {
        "PRB":                   pd.read_excel(xl, sheet_name="PRB"),
        "EstructuraIndicadores": pd.read_excel(xl, sheet_name="EstructuraIndicadores"),
        "Historico":             pd.read_excel(xl, sheet_name="Historico"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Fuente 2: Base de datos (vía API admin)
# ══════════════════════════════════════════════════════════════════════════════

def _login(api_base: str, username: str, password: str) -> str:
    """Obtiene un access_token JWT de la API de UBPD."""
    r = requests.post(
        f"{api_base}/auth/login",
        json={"username": username, "password": password},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def load_from_db(
    api_base: str = "http://localhost/api",
    username: str = "admin",
    password: str = "Admin@UBPD2024!",
) -> Dict[str, pd.DataFrame]:
    """
    Descarga las 3 tablas BI desde la base de datos vía el endpoint
    GET /admin/bi/raw y las retorna como DataFrames con el mismo esquema
    que el Excel original.
    """
    token = _login(api_base, username, password)
    r = requests.get(
        f"{api_base}/admin/bi/raw",
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )
    r.raise_for_status()
    payload = r.json()

    return {
        "PRB":                   pd.DataFrame(payload["PRB"]),
        "EstructuraIndicadores": pd.DataFrame(payload["EstructuraIndicadores"]),
        "Historico":             pd.DataFrame(payload["Historico"]),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Comparación y descripción de DataFrames
# ══════════════════════════════════════════════════════════════════════════════

def describe_dict(data: Dict[str, pd.DataFrame], titulo: str = "Dataset") -> None:
    """Imprime descripción estructurada de cada DataFrame del dict."""
    print("=" * 70)
    print(f"  {titulo}")
    print("=" * 70)
    for key, df in data.items():
        print(f"\n[{key}] — shape={df.shape}")
        print(f"  Columnas ({len(df.columns)}): {list(df.columns)}")
        print(f"  Tipos: {df.dtypes.value_counts().to_dict()}")
        print(f"  Nulls totales: {df.isna().sum().sum()}")


def compare_sources(
    excel_data: Dict[str, pd.DataFrame],
    db_data:    Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Compara las dos fuentes por hoja y retorna un DataFrame con filas/columnas.
    Útil para confirmar que Excel y DB tienen la misma información.
    """
    rows = []
    for key in excel_data:
        x = excel_data[key]
        d = db_data.get(key)
        rows.append({
            "hoja": key,
            "filas_excel": len(x),
            "filas_db":    len(d) if d is not None else None,
            "cols_excel":  x.shape[1],
            "cols_db":     d.shape[1] if d is not None else None,
            "match_filas": (len(x) == len(d)) if d is not None else False,
        })
    return pd.DataFrame(rows)

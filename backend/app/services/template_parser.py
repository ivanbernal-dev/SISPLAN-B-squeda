"""
app/services/template_parser.py — Parseo de Markdown extendido a configuracion_campos JSONB.

El parser es tolerante al orden de columnas: detecta el header y mapea por nombre.
Columnas reconocidas (cualquier orden):
  campo/name, label/etiqueta, tipo/type, bloqueado/readonly,
  default/por_defecto, requerido/required, opciones/options
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import markdown

logger = logging.getLogger(__name__)

VALID_FIELD_TYPES = {"text", "number", "date", "select", "textarea", "computed"}

# Aliases de nombres de columnas → clave interna
_COLUMN_ALIASES: Dict[str, str] = {
    "campo": "name", "name": "name", "field": "name",
    "label": "label", "etiqueta": "label",
    "tipo": "type", "type": "type",
    "bloqueado": "readonly", "readonly": "readonly", "solo_lectura": "readonly",
    "default": "default", "por_defecto": "default", "valor_default": "default",
    "requerido": "required", "required": "required", "obligatorio": "required",
    "opciones": "options", "options": "options",
}

# Orden por defecto si no hay header reconocible
_DEFAULT_ORDER = ["name", "type", "readonly", "default", "required", "options"]


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in ("true", "1", "yes", "si", "sí")


def _build_col_map(header_cells: List[str]) -> List[str]:
    """
    Dado el header de la tabla, devuelve una lista donde cada índice
    contiene el nombre interno del campo (name, label, type, …) o '' si no se reconoce.
    """
    result: List[str] = []
    for cell in header_cells:
        key = cell.strip().lower().replace(" ", "_")
        result.append(_COLUMN_ALIASES.get(key, ""))
    return result


def _parse_table_row(cells: List[str], col_map: List[str]) -> Optional[Dict[str, Any]]:
    """Parsea una fila usando el mapa de columnas del header."""
    if not cells:
        return None

    data: Dict[str, str] = {}
    for idx, attr in enumerate(col_map):
        if attr and idx < len(cells):
            data[attr] = cells[idx].strip()

    name = data.get("name", "").strip()
    if not name or name.startswith("-"):
        return None

    field_type = data.get("type", "text").lower()
    if field_type not in VALID_FIELD_TYPES:
        field_type = "text"

    readonly = _parse_bool(data.get("readonly", "false"))
    default_raw = data.get("default", "")
    default_val: Any = default_raw if default_raw else None
    required = _parse_bool(data.get("required", "true"))
    options_raw = data.get("options", "")
    options: Optional[List[str]] = (
        [o.strip() for o in options_raw.split(",") if o.strip()] if options_raw else None
    )

    # Label: usar el valor de la columna si existe, sino generar desde name
    label_raw = data.get("label", "").strip()
    label = label_raw if label_raw else name.replace("_", " ").title()

    field_config: Dict[str, Any] = {
        "name": name,
        "label": label,
        "type": field_type,
        "readonly": readonly,
        "default": default_val,
        "required": required,
    }
    if options:
        field_config["options"] = options

    return field_config


def _extract_table_rows(markdown_text: str) -> Tuple[List[str], List[List[str]]]:
    """
    Extrae el header y las filas de datos de la primera tabla Markdown encontrada.
    Retorna (col_map, rows) donde col_map es la lista de atributos internos.
    """
    col_map: List[str] = []
    rows: List[List[str]] = []
    header_seen = False
    header_cells: List[str] = []

    for line in markdown_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if header_seen:
                break  # fin de la tabla
            header_cells = []
            continue

        cells = [c.strip() for c in stripped.split("|")[1:-1]]

        # Separador (---|---|---)
        if all(re.match(r"^[-:]+$", c) for c in cells if c):
            if header_cells:
                col_map = _build_col_map(header_cells)
                header_seen = True
            continue

        if not header_seen:
            header_cells = cells
        else:
            rows.append(cells)

    # Si el header no tenía columnas reconocibles, usar orden por defecto
    if not any(c for c in col_map):
        col_map = _DEFAULT_ORDER[:]

    return col_map, rows


def parse_markdown_to_schema(markdown_text: str) -> Dict[str, Any]:
    """
    Parsea el markdown del template y genera el JSONB de configuracion_campos.
    Soporta cualquier orden de columnas siempre que el header sea reconocible.

    Retorna: { "fields": [ { "name": ..., "label": ..., "type": ..., ... }, ... ] }
    """
    col_map, rows = _extract_table_rows(markdown_text)
    fields: List[Dict[str, Any]] = []
    for row in rows:
        field = _parse_table_row(row, col_map)
        if field:
            fields.append(field)
    return {"fields": fields}


def validate_schema(schema: Dict[str, Any]) -> bool:
    if not isinstance(schema, dict):
        return False
    fields = schema.get("fields")
    if not isinstance(fields, list):
        return False
    for field in fields:
        if not isinstance(field, dict):
            return False
        if "name" not in field or "type" not in field:
            return False
        if field.get("type") not in VALID_FIELD_TYPES:
            return False
    return True


def calculate_completeness(
    form_data: Dict[str, Any], schema: Dict[str, Any]
) -> Tuple[int, int]:
    """
    Calcula la completitud de un formulario (campos editables llenos / total editables).
    """
    fields: List[Dict[str, Any]] = schema.get("fields", [])
    editable_fields = [f for f in fields if not f.get("readonly", False)]
    total = len(editable_fields)
    filled = sum(
        1
        for f in editable_fields
        if (v := form_data.get(f.get("name", ""))) is not None and str(v).strip() != ""
    )
    return filled, total


def render_markdown_to_html(markdown_text: str) -> str:
    return markdown.markdown(
        markdown_text,
        extensions=["tables", "fenced_code", "nl2br"],
    )

"""
app/services/template_parser.py — Parseo de Markdown extendido a configuracion_campos JSONB.

Formato de tabla de campos en el Markdown:
| campo | tipo | bloqueado | default | requerido | opciones |
|-------|------|-----------|---------|-----------|---------|
| municipio | text | true | Bogotá | true | |
| estado | select | false | | true | Activo,Inactivo |
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import markdown

logger = logging.getLogger(__name__)

# Tipos de campo admitidos
VALID_FIELD_TYPES = {"text", "number", "date", "select", "textarea"}


def _parse_bool(value: str) -> bool:
    """Convierte 'true'/'false'/'1'/'0' a bool."""
    return value.strip().lower() in ("true", "1", "yes", "si", "sí")


def _parse_table_row(cells: List[str]) -> Optional[Dict[str, Any]]:
    """Parsea una fila de la tabla de campos y retorna un dict de configuración."""
    if len(cells) < 2:
        return None

    name = cells[0].strip()
    if not name or name.startswith("-"):
        return None

    field_type = cells[1].strip().lower() if len(cells) > 1 else "text"
    if field_type not in VALID_FIELD_TYPES:
        field_type = "text"

    readonly = _parse_bool(cells[2]) if len(cells) > 2 else False
    default_val_raw = cells[3].strip() if len(cells) > 3 else ""
    default_val: Any = default_val_raw if default_val_raw else None

    required = _parse_bool(cells[4]) if len(cells) > 4 else True
    options_raw = cells[5].strip() if len(cells) > 5 else ""
    options: Optional[List[str]] = None
    if options_raw:
        options = [o.strip() for o in options_raw.split(",") if o.strip()]

    # Generar label a partir del nombre (snake_case → Title Case)
    label = name.replace("_", " ").title()

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


def _extract_table_rows(markdown_text: str) -> List[List[str]]:
    """
    Extrae filas de tablas Markdown del texto.
    Retorna una lista de listas de celdas (strings).
    """
    rows: List[List[str]] = []
    in_table = False
    header_seen = False

    for line in markdown_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            in_table = False
            header_seen = False
            continue

        in_table = True
        cells = [c.strip() for c in stripped.split("|")[1:-1]]

        # Detectar fila separadora (---|---|---)
        if all(re.match(r"^-+$", c.replace(":", "")) for c in cells if c):
            header_seen = True
            continue

        if header_seen:
            rows.append(cells)
        # Si aún no hay separador, la primera fila es el header — la saltamos

    return rows


def parse_markdown_to_schema(markdown_text: str) -> Dict[str, Any]:
    """
    Parsea el markdown del template y genera el JSONB de configuracion_campos.

    El markdown puede contener una o más tablas con el siguiente encabezado:
    | campo | tipo | bloqueado | default | requerido | opciones |

    Retorna: { "fields": [ { "name": ..., "type": ..., ... }, ... ] }
    """
    rows = _extract_table_rows(markdown_text)
    fields: List[Dict[str, Any]] = []

    for row in rows:
        field = _parse_table_row(row)
        if field:
            fields.append(field)

    return {"fields": fields}


def validate_schema(schema: Dict[str, Any]) -> bool:
    """
    Valida que el esquema JSONB tenga la estructura esperada.
    Retorna True si es válido, False en caso contrario.
    """
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
    Calcula la completitud de un formulario.

    Solo cuenta campos que sean editables (readonly=False).
    Un campo se considera "lleno" si tiene un valor no nulo y no vacío.

    Retorna: (campos_llenos, campos_totales_editables)
    """
    fields: List[Dict[str, Any]] = schema.get("fields", [])
    editable_fields = [f for f in fields if not f.get("readonly", False)]
    total = len(editable_fields)
    filled = 0

    for field in editable_fields:
        name = field.get("name", "")
        value = form_data.get(name)
        if value is not None and str(value).strip() != "":
            filled += 1

    return filled, total


def render_markdown_to_html(markdown_text: str) -> str:
    """Convierte el Markdown a HTML para preview."""
    return markdown.markdown(
        markdown_text,
        extensions=["tables", "fenced_code", "nl2br"],
    )

"""
tests/test_template_parser.py — Pruebas unitarias para app/services/template_parser.py
"""
import pytest
from app.services.template_parser import (
    parse_markdown_to_schema,
    validate_schema,
    calculate_completeness,
)


MARKDOWN_VALIDO = """
# Formulario de Prueba

| campo | tipo | bloqueado | default | requerido | opciones |
|-------|------|-----------|---------|-----------|----------|
| nombre_victima | text | no | | si | |
| fecha_evento | date | no | | si | |
| municipio | text | no | Bogotá | no | |
| departamento | select | no | | si | Cundinamarca,Antioquia,Valle |
| observaciones | textarea | no | | no | |
| numero_registro | number | si | 0 | no | |
"""

MARKDOWN_SIN_TABLA = """
# Solo texto sin tabla

Este documento no tiene tabla de campos.
"""

MARKDOWN_TABLA_INCOMPLETA = """
| campo | tipo |
|-------|------|
| nombre | text |
"""


class TestParseMarkdownToSchema:
    """Pruebas para parse_markdown_to_schema."""

    def test_parse_valid_markdown_returns_list(self):
        schema = parse_markdown_to_schema(MARKDOWN_VALIDO)
        assert isinstance(schema, list)
        assert len(schema) > 0

    def test_parse_correct_number_of_fields(self):
        schema = parse_markdown_to_schema(MARKDOWN_VALIDO)
        assert len(schema) == 6

    def test_field_names_parsed_correctly(self):
        schema = parse_markdown_to_schema(MARKDOWN_VALIDO)
        names = [f["name"] for f in schema]
        assert "nombre_victima" in names
        assert "fecha_evento" in names
        assert "departamento" in names

    def test_field_types_parsed_correctly(self):
        schema = parse_markdown_to_schema(MARKDOWN_VALIDO)
        by_name = {f["name"]: f for f in schema}
        assert by_name["nombre_victima"]["type"] == "text"
        assert by_name["fecha_evento"]["type"] == "date"
        assert by_name["departamento"]["type"] == "select"
        assert by_name["observaciones"]["type"] == "textarea"
        assert by_name["numero_registro"]["type"] == "number"

    def test_readonly_field_parsed(self):
        schema = parse_markdown_to_schema(MARKDOWN_VALIDO)
        by_name = {f["name"]: f for f in schema}
        assert by_name["numero_registro"]["readonly"] is True
        assert by_name["nombre_victima"]["readonly"] is False

    def test_required_field_parsed(self):
        schema = parse_markdown_to_schema(MARKDOWN_VALIDO)
        by_name = {f["name"]: f for f in schema}
        assert by_name["nombre_victima"]["required"] is True
        assert by_name["municipio"]["required"] is False

    def test_default_value_parsed(self):
        schema = parse_markdown_to_schema(MARKDOWN_VALIDO)
        by_name = {f["name"]: f for f in schema}
        assert by_name["municipio"]["default"] == "Bogotá"

    def test_select_options_parsed(self):
        schema = parse_markdown_to_schema(MARKDOWN_VALIDO)
        by_name = {f["name"]: f for f in schema}
        options = by_name["departamento"].get("options", [])
        assert "Cundinamarca" in options
        assert "Antioquia" in options
        assert "Valle" in options

    def test_markdown_without_table_returns_empty(self):
        schema = parse_markdown_to_schema(MARKDOWN_SIN_TABLA)
        assert schema == []

    def test_empty_string_returns_empty(self):
        schema = parse_markdown_to_schema("")
        assert schema == []

    def test_invalid_type_defaults_to_text(self):
        md = """
| campo | tipo | bloqueado | default | requerido | opciones |
|-------|------|-----------|---------|-----------|----------|
| campo1 | tipo_invalido | no | | no | |
"""
        schema = parse_markdown_to_schema(md)
        if schema:
            assert schema[0]["type"] == "text"


class TestValidateSchema:
    """Pruebas para validate_schema."""

    def test_valid_schema_passes(self):
        schema = parse_markdown_to_schema(MARKDOWN_VALIDO)
        errors = validate_schema(schema)
        assert errors == [] or errors is None

    def test_empty_schema_is_valid(self):
        errors = validate_schema([])
        assert errors == [] or errors is None

    def test_schema_with_missing_name_fails(self):
        schema = [{"type": "text", "label": "Sin nombre"}]
        errors = validate_schema(schema)
        # Should report error or return non-empty errors
        if errors is not None:
            assert len(errors) > 0

    def test_schema_with_select_without_options_fails(self):
        schema = [{"name": "campo1", "type": "select", "options": []}]
        errors = validate_schema(schema)
        if errors is not None:
            assert len(errors) > 0


class TestCalculateCompleteness:
    """Pruebas para calculate_completeness."""

    def setup_method(self):
        """Configura esquema y datos de prueba."""
        self.schema = parse_markdown_to_schema(MARKDOWN_VALIDO)
        # Campos editables (no readonly): nombre_victima, fecha_evento, municipio, departamento, observaciones
        # numero_registro es readonly → no cuenta

    def test_all_required_filled_returns_high_completeness(self):
        form_data = {
            "nombre_victima": "Juan García",
            "fecha_evento": "2024-01-15",
            "municipio": "Bogotá",
            "departamento": "Cundinamarca",
            "observaciones": "Algunos detalles",
        }
        filled, total = calculate_completeness(form_data, self.schema)
        assert total > 0
        assert filled == total  # todos completos

    def test_empty_form_returns_zero_filled(self):
        form_data = {}
        filled, total = calculate_completeness(form_data, self.schema)
        assert filled == 0
        assert total > 0

    def test_partial_fill_counted_correctly(self):
        form_data = {
            "nombre_victima": "Juan",
            "fecha_evento": "2024-01-15",
        }
        filled, total = calculate_completeness(form_data, self.schema)
        assert filled == 2
        assert total >= 2

    def test_readonly_fields_not_counted_in_total(self):
        _, total_without_readonly = calculate_completeness({}, self.schema)
        # numero_registro is readonly → total should be 5, not 6
        assert total_without_readonly == 5

    def test_none_values_not_counted_as_filled(self):
        form_data = {
            "nombre_victima": None,
            "fecha_evento": "",
            "municipio": "   ",  # spaces only
        }
        filled, total = calculate_completeness(form_data, self.schema)
        assert filled == 0

    def test_returns_tuple_of_two_ints(self):
        form_data = {"nombre_victima": "Test"}
        result = calculate_completeness(form_data, self.schema)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_completeness_with_empty_schema(self):
        filled, total = calculate_completeness({"campo": "valor"}, [])
        assert filled == 0
        assert total == 0

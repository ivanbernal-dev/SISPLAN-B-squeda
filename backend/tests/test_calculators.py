"""
tests/test_calculators.py — Pruebas unitarias para los calculadores de indicadores.
"""
import pytest
from unittest.mock import MagicMock
from app.services.calculators.base_calculator import BaseCalculator
from app.services.calculators.indicator_calculator import IndicatorCalculator
from app.models.indicator import FormulaTipo


def make_fact_stats(completitudes: list[float]) -> list:
    """Helper: crea lista de FactStats mockeados con los valores dados."""
    result = []
    for c in completitudes:
        fs = MagicMock()
        fs.completitud = c
        result.append(fs)
    return result


class TestBaseCalculator:
    """Pruebas para BaseCalculator.safe_average."""

    def setup_method(self):
        """Crea instancia concreta para testear el método base."""
        class ConcreteCalculator(BaseCalculator):
            def calculate(self, fact_stats_list):
                return self.safe_average([float(fs.completitud) for fs in fact_stats_list])

        self.calc = ConcreteCalculator()

    def test_safe_average_empty_list(self):
        assert self.calc.safe_average([]) == 0.0

    def test_safe_average_single_value(self):
        assert self.calc.safe_average([75.0]) == 75.0

    def test_safe_average_multiple_values(self):
        result = self.calc.safe_average([80.0, 60.0, 100.0])
        assert abs(result - 80.0) < 0.001

    def test_safe_average_with_zero(self):
        result = self.calc.safe_average([0.0, 100.0])
        assert result == 50.0

    def test_safe_average_all_same(self):
        result = self.calc.safe_average([50.0, 50.0, 50.0])
        assert result == 50.0


class TestIndicatorCalculatorPromedioSimple:
    """Pruebas para IndicatorCalculator con promedio_simple."""

    def setup_method(self):
        self.calc = IndicatorCalculator(FormulaTipo.promedio_simple, peso=1.0)

    def test_empty_list_returns_zero(self):
        assert self.calc.calculate([]) == 0.0

    def test_single_record(self):
        stats = make_fact_stats([80.0])
        assert self.calc.calculate(stats) == 80.0

    def test_average_of_multiple(self):
        stats = make_fact_stats([80.0, 60.0, 100.0])
        result = self.calc.calculate(stats)
        assert abs(result - 80.0) < 0.001

    def test_all_zero(self):
        stats = make_fact_stats([0.0, 0.0, 0.0])
        assert self.calc.calculate(stats) == 0.0

    def test_all_hundred(self):
        stats = make_fact_stats([100.0, 100.0, 100.0])
        assert self.calc.calculate(stats) == 100.0

    def test_result_between_0_and_100(self):
        stats = make_fact_stats([45.5, 67.3, 88.2, 12.0])
        result = self.calc.calculate(stats)
        assert 0.0 <= result <= 100.0


class TestIndicatorCalculatorPromedioPonderado:
    """Pruebas para IndicatorCalculator con promedio_ponderado."""

    def test_with_equal_weights_same_as_simple_average(self):
        stats = make_fact_stats([80.0, 60.0, 100.0])
        calc_simple = IndicatorCalculator(FormulaTipo.promedio_simple, peso=1.0)
        calc_pond = IndicatorCalculator(FormulaTipo.promedio_ponderado, peso=1.0)
        assert abs(calc_simple.calculate(stats) - calc_pond.calculate(stats)) < 0.001

    def test_empty_list_returns_zero(self):
        calc = IndicatorCalculator(FormulaTipo.promedio_ponderado, peso=2.0)
        assert calc.calculate([]) == 0.0

    def test_single_record_returns_completeness(self):
        calc = IndicatorCalculator(FormulaTipo.promedio_ponderado, peso=3.0)
        stats = make_fact_stats([75.0])
        assert abs(calc.calculate(stats) - 75.0) < 0.001

    def test_result_is_float(self):
        calc = IndicatorCalculator(FormulaTipo.promedio_ponderado, peso=1.5)
        stats = make_fact_stats([50.0, 75.0])
        result = calc.calculate(stats)
        assert isinstance(result, float)


class TestIndicatorCalculatorConteo:
    """Pruebas para IndicatorCalculator con conteo."""

    def setup_method(self):
        self.calc = IndicatorCalculator(FormulaTipo.conteo, peso=1.0)

    def test_empty_list_returns_zero(self):
        assert self.calc.calculate([]) == 0.0

    def test_conteo_returns_number_of_records(self):
        stats = make_fact_stats([80.0, 60.0, 40.0])
        assert self.calc.calculate(stats) == 3.0

    def test_conteo_single_record(self):
        stats = make_fact_stats([100.0])
        assert self.calc.calculate(stats) == 1.0

    def test_conteo_ignores_completeness_values(self):
        """El conteo no depende del valor de completitud, solo del número de registros."""
        stats_low = make_fact_stats([0.0, 0.0, 0.0, 0.0])
        stats_high = make_fact_stats([100.0, 100.0, 100.0, 100.0])
        assert self.calc.calculate(stats_low) == self.calc.calculate(stats_high) == 4.0


class TestIndicatorCalculatorPersonalizado:
    """Pruebas para IndicatorCalculator con personalizado (fallback a promedio simple)."""

    def setup_method(self):
        self.calc = IndicatorCalculator(FormulaTipo.personalizado, peso=1.0)

    def test_falls_back_to_promedio_simple(self):
        stats = make_fact_stats([80.0, 60.0, 100.0])
        expected = (80.0 + 60.0 + 100.0) / 3
        assert abs(self.calc.calculate(stats) - expected) < 0.001

    def test_empty_list_returns_zero(self):
        assert self.calc.calculate([]) == 0.0


class TestIndicatorCalculatorForIndicator:
    """Pruebas para el factory method for_indicator."""

    def test_creates_calculator_from_indicator(self, mock_indicator):
        calc = IndicatorCalculator.for_indicator(mock_indicator)
        assert isinstance(calc, IndicatorCalculator)
        assert calc.formula_tipo == mock_indicator.formula_tipo

    def test_peso_matches_indicator(self, mock_indicator):
        mock_indicator.peso = 2.5
        calc = IndicatorCalculator.for_indicator(mock_indicator)
        assert calc.peso == 2.5

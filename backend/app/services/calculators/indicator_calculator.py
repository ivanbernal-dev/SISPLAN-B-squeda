"""
app/services/calculators/indicator_calculator.py — Calculadora de indicadores.

Implementa la lógica por tipo de fórmula definida en el Enum FormulaTipo:
- promedio_simple: media aritmética de completitud
- promedio_ponderado: media ponderada usando el peso del template/indicador
- conteo: devuelve el número de formularios (no un porcentaje)
- personalizado: aplica reglas específicas (extensible)
"""
import logging
from decimal import Decimal
from typing import List, TYPE_CHECKING

from app.models.indicator import FormulaTipo
from app.services.calculators.base_calculator import BaseCalculator

if TYPE_CHECKING:
    from app.models.fact_stats import FactStats

logger = logging.getLogger(__name__)


class IndicatorCalculator(BaseCalculator):
    """
    Calculadora que despacha la lógica según el formula_tipo del indicador.
    """

    def __init__(self, formula_tipo: FormulaTipo, peso: float = 1.0) -> None:
        self.formula_tipo = formula_tipo
        self.peso = peso

    def calculate(self, fact_stats_list: List["FactStats"]) -> float:
        """Delega al método correspondiente según el tipo de fórmula."""
        if not fact_stats_list:
            return 0.0

        dispatch = {
            FormulaTipo.promedio_simple: self._promedio_simple,
            FormulaTipo.promedio_ponderado: self._promedio_ponderado,
            FormulaTipo.conteo: self._conteo,
            FormulaTipo.personalizado: self._personalizado,
        }
        func = dispatch.get(self.formula_tipo, self._promedio_simple)
        return func(fact_stats_list)

    # ── Implementaciones ───────────────────────────────────────────────────────
    def _promedio_simple(self, fact_stats_list: List["FactStats"]) -> float:
        """Media aritmética de completitud."""
        values = [float(fs.completitud) for fs in fact_stats_list]
        return self.safe_average(values)

    def _promedio_ponderado(self, fact_stats_list: List["FactStats"]) -> float:
        """
        Media ponderada: Σ(completitud × peso_template) / Σ(peso_template).
        En esta implementación el peso se toma del indicador; se puede extender
        para que cada template tenga su propio peso.
        """
        total_peso = len(fact_stats_list) * self.peso
        if total_peso == 0:
            return 0.0
        suma = sum(float(fs.completitud) * self.peso for fs in fact_stats_list)
        return suma / total_peso

    def _conteo(self, fact_stats_list: List["FactStats"]) -> float:
        """Retorna el número de formularios aprobados como valor del indicador."""
        return float(len(fact_stats_list))

    def _personalizado(self, fact_stats_list: List["FactStats"]) -> float:
        """
        Lógica personalizada: extensible por indicador específico.
        Por defecto aplica promedio simple.
        """
        logger.debug(
            "Usando cálculo 'personalizado' (promedio_simple) para %d registros.",
            len(fact_stats_list),
        )
        return self._promedio_simple(fact_stats_list)

    @classmethod
    def for_indicator(cls, indicator: "Indicator") -> "IndicatorCalculator":  # type: ignore[name-defined]
        """Factory para construir una calculadora a partir de un objeto Indicator."""
        return cls(
            formula_tipo=indicator.formula_tipo,
            peso=float(indicator.peso),
        )

"""
app/services/calculators/base_calculator.py — Clase base abstracta para calculadoras.
"""
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.fact_stats import FactStats


class BaseCalculator(ABC):
    """
    Contrato base para todos los calculadores de indicadores.
    Cada indicador puede tener su propia lógica implementada en una subclase.
    """

    @abstractmethod
    def calculate(self, fact_stats_list: List["FactStats"]) -> float:
        """
        Recibe una lista de registros fact_stats pertenecientes a un indicador
        y retorna el valor calculado (completitud agregada, 0-100).
        """
        ...

    def safe_average(self, values: List[float]) -> float:
        """Calcula el promedio de una lista; retorna 0.0 si está vacía."""
        if not values:
            return 0.0
        return sum(values) / len(values)

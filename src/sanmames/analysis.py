"""Análisis estadístico entre réplicas y escenarios (memoria §5.3).

Responsable: C.

* media ± t_{0,975; n-1} · s / √n de cada KPI;
* intervalo de confianza de la diferencia con X0 (réplicas emparejadas por
  semilla, números aleatorios comunes);
* número de réplicas necesario n = (t · s / h)² con h ≤ 5 % de la espera media;
* gráficas con matplotlib (guardar en ``results/``).
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


def confidence_interval(values: Sequence[float], level: float = 0.95) -> tuple[float, float]:
    """Devuelve ``(media, semianchura)`` del IC t-Student de ``values``."""
    raise NotImplementedError("T5.2-C: confidence_interval")


def required_replications(
    values: Sequence[float], rel_halfwidth: float = 0.05, level: float = 0.95
) -> int:
    """Réplicas necesarias para que la semianchura sea ``rel_halfwidth`` x media."""
    raise NotImplementedError("T5.2-C: required_replications")


def summarize(kpis: pd.DataFrame, level: float = 0.95) -> pd.DataFrame:
    """Media e IC de cada KPI por escenario (una fila por ``scenario``)."""
    raise NotImplementedError("T5.2-C: summarize")


def compare_with_baseline(
    kpis: pd.DataFrame, baseline: str = "X0_base", level: float = 0.95
) -> pd.DataFrame:
    """IC de la diferencia (escenario - baseline) por KPI, emparejando por ``seed``."""
    raise NotImplementedError("T5.2-C: compare_with_baseline")

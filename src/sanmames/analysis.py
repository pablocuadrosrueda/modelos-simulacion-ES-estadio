"""Análisis estadístico entre réplicas y escenarios (memoria §5.3).

Responsable: C.

* media ± t_{0,975; n-1} · s / √n de cada KPI;
* intervalo de confianza de la diferencia con X0 (réplicas emparejadas por
  semilla, números aleatorios comunes);
* número de réplicas necesario n = (t · s / h)² con h ≤ 5 % de la espera media;
* gráficas con matplotlib (guardar en ``results/``).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.stats import t

from .metrics import KPI_COLUMNS

_STAT_COLUMNS = [
    f"{name}_{suffix}" for name in KPI_COLUMNS for suffix in ("mean", "halfwidth", "n")
]


def _sample(values: Sequence[float]) -> np.ndarray:
    """Observaciones de réplica: omite NaN, pero rechaza infinitos y matrices."""
    sample = np.asarray(values, dtype=float)
    if sample.ndim != 1:
        raise ValueError("Se esperaba una secuencia unidimensional de réplicas")
    if np.isinf(sample).any():
        raise ValueError("Las observaciones no pueden contener infinitos")
    return sample[~np.isnan(sample)]


def _validate_level(level: float) -> None:
    if not 0 < level < 1:
        raise ValueError("level debe estar entre 0 y 1, sin incluir los extremos")


def _validate_table(kpis: pd.DataFrame, *, paired: bool = False) -> None:
    required = ["scenario", "seed"] if paired else ["scenario"]
    if any(name not in kpis for name in required):
        raise ValueError(f"Faltan columnas identificativas: {required}")
    if kpis["scenario"].isna().any():
        raise ValueError("scenario no puede contener valores ausentes")
    if "seed" in kpis:
        if kpis["seed"].isna().any():
            raise ValueError("seed no puede contener valores ausentes")
        if kpis.duplicated(["scenario", "seed"]).any():
            raise ValueError("Hay réplicas duplicadas para el mismo escenario y semilla")
    for name in KPI_COLUMNS:
        if name in kpis:
            _sample(kpis[name])


def _summary_row(frame: pd.DataFrame, level: float) -> dict[str, float | int]:
    row: dict[str, float | int] = {}
    for name in KPI_COLUMNS:
        values = _sample(frame[name]) if name in frame else np.array([], dtype=float)
        mean, halfwidth = confidence_interval(values, level)
        row[f"{name}_mean"] = mean
        row[f"{name}_halfwidth"] = halfwidth
        row[f"{name}_n"] = len(values)
    return row


def confidence_interval(values: Sequence[float], level: float = 0.95) -> tuple[float, float]:
    """Devuelve ``(media, semianchura)`` del IC t-Student entre réplicas.

    Usa desviación muestral (n-1) y omite NaN. Sin datos devuelve (NaN, NaN);
    con uno solo, (media, NaN): no se puede estimar la incertidumbre.
    """
    _validate_level(level)
    sample = _sample(values)
    if len(sample) == 0:
        return math.nan, math.nan
    mean = float(sample.mean())
    if len(sample) == 1:
        return mean, math.nan
    critical = float(t.ppf((1 + level) / 2, df=len(sample) - 1))
    halfwidth = critical * float(sample.std(ddof=1)) / math.sqrt(len(sample))
    return mean, halfwidth


def required_replications(
    values: Sequence[float], rel_halfwidth: float = 0.05, level: float = 0.95
) -> int:
    """Estima el total necesario con n = ceil((t_piloto * s / h)^2).

    h = rel_halfwidth * abs(media); usa los grados de libertad del piloto y
    devuelve al menos las réplicas válidas ya disponibles. No garantiza que
    la precisión final se alcance: debe comprobarse al ampliar la muestra.
    Media cero con variabilidad no permite un objetivo relativo finito.
    """
    _validate_level(level)
    if not math.isfinite(rel_halfwidth) or rel_halfwidth <= 0:
        raise ValueError("rel_halfwidth debe ser positivo y finito")
    sample = _sample(values)
    if len(sample) < 2:
        raise ValueError("Se necesitan al menos dos réplicas piloto válidas")
    mean, halfwidth = confidence_interval(sample, level)
    if halfwidth == 0:
        return len(sample)
    if mean == 0:
        raise ValueError("Media cero con variabilidad: no se puede usar precisión relativa")
    # halfwidth = t*s/sqrt(n_piloto); esta expresión aplica la fórmula de §5.3.
    required = math.ceil(len(sample) * (halfwidth / (rel_halfwidth * abs(mean))) ** 2)
    return max(len(sample), required)


def summarize(kpis: pd.DataFrame, level: float = 0.95) -> pd.DataFrame:
    """Media e IC de cada KPI por escenario (una fila por ``scenario``)."""
    _validate_level(level)
    _validate_table(kpis)
    rows = [
        {"scenario": scenario, **_summary_row(group, level)}
        for scenario, group in kpis.groupby("scenario", sort=False)
    ]
    return pd.DataFrame(rows, columns=["scenario", *_STAT_COLUMNS])


def compare_with_baseline(
    kpis: pd.DataFrame, baseline: str = "X0_base", level: float = 0.95
) -> pd.DataFrame:
    """IC de escenario - baseline, emparejando exclusivamente por ``seed``.

    Una fila por escenario alternativo. Usa solo semillas comunes y, para cada
    KPI, parejas con ambos valores observados. Informa el número de parejas
    válido; sin parejas, la media y la semianchura son NaN.
    """
    _validate_level(level)
    _validate_table(kpis, paired=True)
    if baseline not in set(kpis["scenario"]):
        raise ValueError(f"Escenario base no encontrado: {baseline}")
    base = kpis.loc[kpis["scenario"] == baseline].set_index("seed").reindex(columns=KPI_COLUMNS)
    rows = []
    for scenario, group in kpis.groupby("scenario", sort=False):
        if scenario == baseline:
            continue
        variant = group.set_index("seed").reindex(columns=KPI_COLUMNS)
        common = variant.index.intersection(base.index, sort=False)
        differences = variant.loc[common] - base.loc[common]
        rows.append(
            {"scenario": scenario, "baseline": baseline, **_summary_row(differences, level)}
        )
    return pd.DataFrame(rows, columns=["scenario", "baseline", *_STAT_COLUMNS])

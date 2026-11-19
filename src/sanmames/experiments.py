"""Ejecución de experimentos: varias réplicas por escenario (RF06).

Responsable: C.

Un *experimento* es un fichero de ``configs/experiments`` (``X1_2tornos``,
``S1_sensibilidad``...). Puede contener uno o varios escenarios (``variants``).
Todas las réplicas ``j`` de todos los escenarios usan la misma semilla
``replica_seed(base_seed, j)`` (números aleatorios comunes, memoria §5.3).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import EXPERIMENTS_DIR

DEFAULT_BASE_SEED = 20261105
"""Semilla base común a todos los escenarios."""

RESULTS_DIR = EXPERIMENTS_DIR.parents[1] / "results"


def list_experiments(directory: Path = EXPERIMENTS_DIR) -> list[str]:
    """Nombres (stem) de los ficheros de experimento disponibles, ordenados."""
    return sorted(p.stem for p in directory.glob("*.json"))


def find_experiment_file(name: str, directory: Path = EXPERIMENTS_DIR) -> Path:
    """Resuelve ``name`` a un fichero de experimento.

    Acepta el stem exacto (``"X1_2tornos"``) o un prefijo que identifique un
    único fichero (``"X0"`` -> ``X0_base.json``).

    Raises:
        FileNotFoundError: si no hay coincidencia.
        ValueError: si el prefijo es ambiguo (p. ej. ``"X1"``).
    """
    exact = directory / f"{name}.json"
    if exact.is_file():
        return exact
    matches = [s for s in list_experiments(directory) if s.startswith(f"{name}_")]
    if not matches:
        raise FileNotFoundError(
            f"Experimento {name!r} no encontrado. Disponibles: {list_experiments(directory)}"
        )
    if len(matches) > 1:
        raise ValueError(f"Experimento {name!r} ambiguo: {matches}")
    return directory / f"{matches[0]}.json"


def replica_seed(base_seed: int, replica: int) -> int:
    """Semilla de la réplica ``replica`` (0-indexada). Igual en todos los escenarios."""
    return base_seed + replica


def run_experiment(name: str, n_reps: int, base_seed: int = DEFAULT_BASE_SEED) -> pd.DataFrame:
    """Ejecuta ``n_reps`` réplicas de cada escenario del experimento ``name``.

    Returns:
        Tabla de KPIs por réplica: una fila por (escenario, réplica) con columnas
        ``metrics.ID_COLUMNS + metrics.KPI_COLUMNS``.
    """
    raise NotImplementedError("T1.6-C: run_experiment")

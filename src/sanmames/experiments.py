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

from .config import EXPERIMENTS_DIR, load_experiment
from .metrics import ID_COLUMNS, KPI_COLUMNS, compute_kpis
from .runner import run_replica

DEFAULT_BASE_SEED = 20261105
"""Semilla base común a todos los escenarios."""

RESULTS_DIR = EXPERIMENTS_DIR.parents[1] / "results"


def list_experiments(directory: Path = EXPERIMENTS_DIR) -> list[str]:
    """Nombres (stem) de los ficheros de experimento disponibles, ordenados."""
    return sorted(p.stem for p in directory.glob("*.json"))


def find_experiment_file(name: str, directory: Path = EXPERIMENTS_DIR) -> Path:
    """Resuelve ``name`` a un fichero de experimento.

    Acepta una ruta a un JSON, también fuera de ``configs/experiments``, el
    stem exacto (``"X1_2tornos"``) o un prefijo que identifique un único fichero
    (``"X0"`` -> ``X0_base.json``).

    Raises:
        FileNotFoundError: si no hay coincidencia.
        ValueError: si el prefijo es ambiguo (p. ej. ``"X1"``).
    """
    candidate = Path(name).expanduser()
    if candidate.is_file():
        return candidate
    if candidate.parent != Path("."):
        raise FileNotFoundError(f"No existe el fichero de experimento: {candidate}")
    exact = directory / (candidate.name if candidate.suffix == ".json" else f"{name}.json")
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

    Acepta los mismos nombres y rutas que ``find_experiment_file``. No escribe
    archivos: la CLI guarda la tabla devuelta en ``results/<fichero>_kpis.csv``.

    Returns:
        Tabla de KPIs por réplica: una fila por (escenario, réplica) con columnas
        ``metrics.ID_COLUMNS + metrics.KPI_COLUMNS``.
    """
    if isinstance(n_reps, bool) or not isinstance(n_reps, int) or n_reps < 1:
        raise ValueError("n_reps debe ser un entero >= 1")
    if isinstance(base_seed, bool) or not isinstance(base_seed, int) or base_seed < 0:
        raise ValueError("base_seed debe ser un entero >= 0")

    experiment = load_experiment(find_experiment_file(name))
    rows = []
    for config in experiment.configs:
        for replica in range(n_reps):
            seed = replica_seed(base_seed, replica)
            df = run_replica(config, seed)
            rows.append(
                {
                    "experiment": experiment.experiment,
                    "scenario": config.name,
                    "replica": replica,
                    "seed": seed,
                    **compute_kpis(df, config),
                }
            )
    return pd.DataFrame(rows, columns=ID_COLUMNS + KPI_COLUMNS)

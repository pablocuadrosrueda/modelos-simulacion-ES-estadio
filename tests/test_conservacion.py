"""Verificación: conservación de espectadores (memoria §3.3 y §5.3).

En todo instante N = pendientes + en cola + en control + en tránsito +
en conflicto + sentados + saliendo + fuera. Se reconstruye el estado de cada
espectador a partir de sus instantes en el DataFrame de resultados.

Conservación de entrada activa con T1.4; salida pendiente de T3.3 / T3.4.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from sanmames.config import Config
from sanmames.entities import SPECTATOR_COLUMNS
from sanmames.runner import run_replica


def _state_counts(df: pd.DataFrame, t: float) -> dict[str, int]:
    """Número de espectadores en cada estado en el instante ``t`` (min)."""
    seated_end = df["t_exit_queue"].fillna(np.inf)
    states = {
        "pending": df["t_arrival"] > t,
        "queue": (df["t_arrival"] <= t) & ~(df["t_start_control"] <= t),
        "control": (df["t_start_control"] <= t) & ~(df["t_end_control"] <= t),
        "transit": (df["t_end_control"] <= t) & ~(df["t_seated"] <= t),
        "seated": (df["t_seated"] <= t) & (seated_end > t),
        "leaving": (df["t_exit_queue"] <= t) & ~(df["t_exit"] <= t),
        "out": df["t_exit"] <= t,
    }
    return {k: int(v.sum()) for k, v in states.items()}


def test_conservation_over_time(mini_config: Config) -> None:
    df = run_replica(mini_config, seed=1)
    assert list(df.columns) == SPECTATOR_COLUMNS
    assert len(df) == mini_config.n_spectators
    for t in np.linspace(mini_config.t_open_min, mini_config.t_end_min + 30, 50):
        assert sum(_state_counts(df, t).values()) == mini_config.n_spectators, t


@pytest.mark.xfail(raises=AssertionError, strict=True, reason="salida pendiente de T3.3 / T3.4")
def test_everybody_ends_out(mini_config: Config) -> None:
    df = run_replica(mini_config, seed=2)
    assert df["t_exit"].notna().all()

"""Verificación: orden temporal (memoria §5.3).

t_llegada <= t_inicio_control <= t_fin_control <= t_sentado <= t_salida.

Entrada y reproducibilidad activas con T1.4; salida pendiente de T3.3.
"""

from __future__ import annotations

import pytest

from sanmames.config import Config
from sanmames.runner import run_replica

ORDER = ["t_arrival", "t_start_control", "t_end_control", "t_vomitory", "t_seated"]


def test_entry_times_are_ordered(mini_config: Config) -> None:
    df = run_replica(mini_config, seed=3)
    assert df[ORDER].notna().all().all()
    for earlier, later in zip(ORDER, ORDER[1:], strict=False):
        # Aviso de B: redondeo s <-> min; tolerancia numérica, no parámetro del modelo.
        assert (df[earlier] <= df[later] + 1e-9).all(), (earlier, later)


@pytest.mark.xfail(raises=AssertionError, strict=True, reason="salida pendiente de T3.3")
def test_exit_after_seated(mini_config: Config) -> None:
    df = run_replica(mini_config, seed=3)
    assert df["t_exit"].notna().all()
    both = df[["t_seated", "t_exit"]].dropna()
    assert (both["t_seated"] <= both["t_exit"]).all()


def test_same_seed_same_result(mini_config: Config) -> None:
    a = run_replica(mini_config, seed=4)
    b = run_replica(mini_config, seed=4)
    assert a.equals(b)

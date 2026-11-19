"""Verificación: orden temporal (memoria §5.3).

t_llegada <= t_inicio_control <= t_fin_control <= t_sentado <= t_salida.

Esqueleto: se activa al implementar runner.run_replica (T1.7).
"""

from __future__ import annotations

import pytest

from sanmames.config import Config
from sanmames.runner import run_replica

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError, strict=True, reason="pendiente de run_replica (T1.4)"
)

ORDER = ["t_arrival", "t_start_control", "t_end_control", "t_vomitory", "t_seated"]


def test_entry_times_are_ordered(mini_config: Config) -> None:
    df = run_replica(mini_config, seed=3)
    for earlier, later in zip(ORDER, ORDER[1:], strict=False):
        both = df[[earlier, later]].dropna()
        assert (both[earlier] <= both[later]).all(), (earlier, later)


def test_exit_after_seated(mini_config: Config) -> None:
    df = run_replica(mini_config, seed=3)
    both = df[["t_seated", "t_exit"]].dropna()
    assert (both["t_seated"] <= both["t_exit"]).all()


def test_same_seed_same_result(mini_config: Config) -> None:
    a = run_replica(mini_config, seed=4)
    b = run_replica(mini_config, seed=4)
    assert a.equals(b)

"""Verificación de Inc1: conservación en cada cambio y caso límite de tornos (T1.7)."""

from __future__ import annotations

import numpy as np
import pytest

from conftest import MINI_OVERRIDES
from sanmames.config import load_config
from sanmames.runner import run_replica


@pytest.mark.parametrize("seed", [1, 7, 42])
def test_one_state_per_spectator_at_every_transition(seed: int) -> None:
    cfg = load_config(overrides={**MINI_OVERRIDES, "n_spectators": 80})
    df = run_replica(cfg, seed)
    assert len(df) == df["id"].nunique() == cfg.n_spectators

    # Precisión de 1e-9 min para no distinguir el mismo instante por el
    # redondeo s <-> min señalado por B. No es un paso del reloj de simulación.
    columns = ["t_arrival", "t_start_control", "t_end_control", "t_seated"]
    times = df[columns].round(9).to_numpy()
    instants = np.unique(
        np.concatenate([times.ravel(), [cfg.t_open_min, df["t_seated"].max() + 1]])
    )
    arrived, started, controlled, seated = [
        times[:, i][None, :] <= instants[:, None] for i in range(len(columns))
    ]
    states = np.stack(
        [~arrived, arrived & ~started, started & ~controlled, controlled & ~seated, seated]
    )
    # Cada persona está en exactamente un estado en cada transición; comprobar
    # solo la suma global podría ocultar una duplicación compensada por una pérdida.
    assert (states.sum(axis=0) == 1).all()
    assert (states.sum(axis=(0, 2)) == cfg.n_spectators).all()
    assert df["t_seated"].notna().all()
    assert df["t_exit"].isna().all()  # Inc1 termina en el asiento.


@pytest.mark.parametrize("seed", [1, 7, 42])
def test_many_turnstiles_remove_entry_wait(seed: int) -> None:
    overrides = {
        **MINI_OVERRIDES,
        "n_spectators": 60,
        "gates_per_zone": 1,
        "arrival_profile": "burst",
        "arrival_profiles": {"burst": [[-1, 0, 1.0]]},
    }
    few = run_replica(load_config(overrides={**overrides, "turnstiles_per_gate": 1}), seed)
    many = run_replica(load_config(overrides={**overrides, "turnstiles_per_gate": 60}), seed)
    # Misma demanda y servicio por espectador; cambia únicamente la capacidad.
    np.testing.assert_array_equal(few["t_arrival"], many["t_arrival"])
    np.testing.assert_array_equal(few["service_s"], many["service_s"])
    wait_few = few["t_start_control"] - few["t_arrival"]
    wait_many = many["t_start_control"] - many["t_arrival"]
    assert wait_few.mean() > 0
    np.testing.assert_allclose(wait_many, 0, atol=1e-9, rtol=0)
    assert many["t_seated"].notna().all()


def test_conservation_when_time_limit_leaves_an_unfinished_queue() -> None:
    cfg = load_config(
        overrides={
            **MINI_OVERRIDES,
            "n_spectators": 40,
            "gates_per_zone": 1,
            "turnstiles_per_gate": 1,
            "arrival_profile": "burst",
            "arrival_profiles": {"burst": [[-90, -89.9, 1.0]]},
            "service_time_s": {"low": 60, "mode": 60, "high": 60},
            "max_sim_hours": 30 / 3600,
        }
    )
    df = run_replica(cfg, seed=1)
    assert len(df) == df["id"].nunique() == 40
    assert df["t_arrival"].max() < cfg.t_open_min + cfg.max_sim_hours * 60
    queued = df["t_start_control"].isna()
    in_control = df["t_start_control"].notna() & df["t_end_control"].isna()
    assert queued.sum() == 39
    assert in_control.sum() == 1
    assert (queued.astype(int) + in_control.astype(int) == 1).all()
    assert df["t_seated"].isna().all()

"""T3.4: conservación individual en todas las transiciones del partido.

Pendientes + cola + control + tránsito + conflicto + sentados + saliendo + fuera
suman N, sin pérdidas ni duplicaciones compensadas. Incluye réplicas truncadas.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from conftest import MINI_OVERRIDES
from sanmames import runner
from sanmames.config import Config, deep_merge, load_config
from sanmames.entities import SPECTATOR_COLUMNS, Spectator


def _assert_conservation(df: pd.DataFrame, cfg: Config) -> dict[str, int]:
    """Reconstruye estados en sucesos y puntos intermedios, hasta el fin real."""
    assert list(df.columns) == SPECTATOR_COLUMNS
    assert len(df) == df["id"].nunique() == cfg.n_spectators
    columns = [
        "t_arrival",
        "t_start_control",
        "t_end_control",
        "t_seated",
        "t_exit_queue",
        "t_exit",
    ]
    # Tolerancia de conversión s/min ya usada en T1.7, no paso del reloj SimPy.
    times = df[columns].round(9).to_numpy(dtype=float)
    delay = np.where(
        df["tier"].eq("upper") & (cfg.exit_policy == "staggered"), cfg.exit_stagger_min, 0
    )
    release = np.maximum(df["t_seated"].to_numpy(), cfg.t_end_min + delay).round(9)
    limit = cfg.t_open_min + cfg.max_sim_hours * 60
    stop = round(df["t_exit"].max() if df["t_exit"].notna().all() else limit, 9)
    conflicts = df.attrs["incidents"].query('kind == "I1"')
    instants = np.concatenate(
        [
            times.ravel(),
            release,
            conflicts[["t_start", "t_end"]].to_numpy().ravel(),
            [cfg.t_open_min, stop],
        ]
    ).astype(float)
    instants = np.unique(instants[np.isfinite(instants) & (instants <= stop)])
    instants = np.unique(np.concatenate([instants, (instants[:-1] + instants[1:]) / 2]))
    t = instants[:, None]
    arrived, started, controlled, seated, at_exit, out = [
        times[:, i][None, :] <= t for i in range(len(columns))
    ]
    conflict = np.zeros_like(arrived)
    for event in conflicts.itertuples():
        end = np.inf if pd.isna(event.t_end) else round(event.t_end, 9)
        conflict |= (
            (df["id"].to_numpy()[None, :] == event.spectator_id)
            & (t >= round(event.t_start, 9))
            & (t < end)
        )
    released = release[None, :] <= t
    states = {
        "pending": ~arrived,
        "queue": arrived & ~started,
        "control": started & ~controlled,
        "transit": controlled & ~seated & ~conflict,
        "conflict": conflict,
        "seated": seated & ~released,
        "leaving": released & ~out,
        "out": out,
    }
    # Llegar a una salida exige haberse liberado del asiento.
    assert (~at_exit | released).all()
    assert (~out | at_exit).all()
    membership = np.stack(list(states.values()))
    assert (membership.sum(axis=0) == 1).all()
    assert (membership.sum(axis=(0, 2)) == cfg.n_spectators).all()
    return {name: int(mask[-1].sum()) for name, mask in states.items()}


@pytest.mark.parametrize("seed", [1, 7, 42])
@pytest.mark.parametrize("policy", ["simultaneous", "staggered"])
@pytest.mark.parametrize("incidents", [False, True])
def test_conservation_at_every_transition(seed: int, policy: str, incidents: bool) -> None:
    cfg = load_config(
        overrides=deep_merge(
            MINI_OVERRIDES,
            {
                "n_spectators": 80,
                "zones": ["A", "B"],
                "zone_share": [0.5, 0.5],
                "exit_policy": policy,
                "queue_discipline": "priority",
                "arrival_profile": "burst",
                "arrival_profiles": {"burst": [[-2, -1, 1.0]]},
                "vomitory_capacity": 2,
                "stewards_per_zone": 1,
                "incidents": {
                    "seat_conflict": {
                        "enabled": incidents,
                        "prob": 0.5,
                        "resolution_min": {"low": 0.1, "mode": 0.1, "high": 0.1},
                    },
                    "turnstile_failure": {"enabled": incidents, "mtbf_min": 10},
                    "gate_closure": {"enabled": incidents, "start_min": -2, "duration_min": 0.5},
                },
            },
        )
    )
    df = runner.run_replica(cfg, seed)
    final = _assert_conservation(df, cfg)
    assert final["out"] == cfg.n_spectators
    assert sum(value for name, value in final.items() if name != "out") == 0
    if incidents:
        assert df.attrs["incidents"]["kind"].eq("I1").any()


@pytest.mark.parametrize(
    ("duration_min", "arrival", "service_s", "expected"),
    [
        (0.5, -90, 60, {"queue": 3, "control": 1}),
        (100, -80, 0, {"seated": 4}),
        (195.3, -80, 0, {"leaving": 3, "out": 1}),
        (0.5, -80, 0, {"pending": 4}),
    ],
)
def test_conservation_with_time_limit(
    duration_min, arrival, service_s, expected, monkeypatch
) -> None:
    cfg = load_config(
        overrides={
            **MINI_OVERRIDES,
            "n_spectators": 4,
            "turnstiles_per_gate": 1,
            "exits_per_zone": 1,
            "exit_rate_per_m_min": 1,
            "max_sim_hours": duration_min / 60,
        }
    )
    spectators = [
        Spectator(i, "A", 1, 1, "lower", "standard", 1, 0, arrival, service_s) for i in range(4)
    ]
    monkeypatch.setattr(runner, "generate_spectators", lambda config, rngs: spectators)
    df = runner.run_replica(cfg, 1)
    final = _assert_conservation(df, cfg)
    assert {name: count for name, count in final.items() if count} == expected


def test_everybody_ends_out(mini_config: Config) -> None:
    df = runner.run_replica(mini_config, seed=2)
    assert _assert_conservation(df, mini_config)["out"] == mini_config.n_spectators

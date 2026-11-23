"""T3.3: salida real desde el runner y KPIs con soluciones conocidas."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from conftest import MINI_OVERRIDES
from sanmames import runner
from sanmames.config import Config, load_config, load_experiment
from sanmames.entities import SPECTATOR_COLUMNS, Spectator
from sanmames.metrics import compute_kpis


@pytest.mark.parametrize("policy", ["simultaneous", "staggered"])
def test_release_walk_and_pass_end_to_end(policy: str, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = load_config(overrides={**MINI_OVERRIDES, "n_spectators": 2, "exit_policy": policy})
    spectators = [
        Spectator(0, "A", 1, 1, "lower", "standard", 1, 60, -20, 4),
        Spectator(1, "A", 1, 6, "upper", "standard", 1, 60, -20, 4),
    ]
    monkeypatch.setattr(runner, "generate_spectators", lambda config, rngs: spectators)
    df = runner.run_replica(cfg, 1)
    delay = cfg.exit_stagger_min if policy == "staggered" else 0
    assert df.loc[0, "t_exit_queue"] == pytest.approx(cfg.t_end_min + 1)
    assert df.loc[1, "t_exit_queue"] == pytest.approx(cfg.t_end_min + 1 + delay)
    passage = 1 / (cfg.exit_width_m * cfg.exit_rate_per_m_min)
    assert (df["t_exit"] - df["t_exit_queue"]).to_numpy() == pytest.approx([passage] * 2)
    kpis = compute_kpis(df, cfg)
    assert kpis["exit_time_min"] == pytest.approx(1 + delay + passage)
    assert kpis["exit_queue_max"] == 1  # Incluye a quien está atravesando la salida.


def test_late_seating_starts_exit_immediately(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = load_config(overrides={**MINI_OVERRIDES, "n_spectators": 1})
    spectator = Spectator(0, "A", 1, 1, "lower", "standard", 1, 60, cfg.t_end_min + 1, 4)
    monkeypatch.setattr(runner, "generate_spectators", lambda config, rngs: [spectator])
    row = runner.run_replica(cfg, 1).iloc[0]
    assert row.t_exit_queue == pytest.approx(row.t_seated + 1)
    assert row.t_exit > row.t_exit_queue > row.t_seated > cfg.t_end_min


def test_full_journey_matches_analytical_exit_capacity(monkeypatch: pytest.MonkeyPatch) -> None:
    # Apartado 4.3: una zona, 12.195 personas y seis salidas de 4 m a 66 pers/m/min.
    # Marcha nula para aislar exactamente la capacidad teórica de las salidas.
    cfg = load_config(
        overrides={
            **MINI_OVERRIDES,
            "n_spectators": 12195,
            "vomitory_pass_s": {"low": 0, "mode": 0, "high": 0},
        }
    )
    spectators = [
        Spectator(i, "A", 1, 1, "lower", "standard", 1, 0, -80, 0) for i in range(cfg.n_spectators)
    ]
    monkeypatch.setattr(runner, "generate_spectators", lambda config, rngs: spectators)
    df = runner.run_replica(cfg, 1)
    assert df["t_exit"].notna().all()
    expected = math.ceil(cfg.n_spectators / cfg.exits_per_zone) / (
        cfg.exit_width_m * cfg.exit_rate_per_m_min
    )
    assert compute_kpis(df, cfg)["exit_time_min"] == pytest.approx(expected)
    assert expected == pytest.approx(7.7, abs=0.01)


def test_exit_kpis_separate_zones_and_exits(mini_config: Config) -> None:
    df = pd.DataFrame(
        {
            "zone": ["A", "A", "A", "B"],
            "exit_id": [1, 1, 2, 1],
            "t_exit_queue": [105, 105, 105, 105],
            "t_exit": [106, 107, 106, 106],
        }
    ).reindex(columns=SPECTATOR_COLUMNS)
    kpis = compute_kpis(df, mini_config)
    assert kpis["exit_time_min"] == 2
    assert kpis["exit_queue_max"] == 2
    df.loc[1, "t_exit"] = math.nan
    kpis = compute_kpis(df, mini_config)
    assert math.isnan(kpis["exit_time_min"])
    assert kpis["exit_queue_max"] == 2


def test_limit_during_exit_preserves_unfinished_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = load_config(
        overrides={
            **MINI_OVERRIDES,
            "n_spectators": 3,
            "exits_per_zone": 1,
            "exit_rate_per_m_min": 1,
            "max_sim_hours": (195 + 0.3) / 60,
        }
    )
    spectators = [Spectator(i, "A", 1, 1, "lower", "standard", 1, 0, -80, 0) for i in range(3)]
    monkeypatch.setattr(runner, "generate_spectators", lambda config, rngs: spectators)
    df = runner.run_replica(cfg, 1)
    assert len(df) == df["id"].nunique() == 3
    assert df["t_exit_queue"].notna().all()
    assert df["t_exit"].notna().sum() == 1
    assert math.isnan(compute_kpis(df, cfg)["exit_time_min"])
    assert compute_kpis(df, cfg)["exit_queue_max"] == 3


def test_development_policies_keep_common_random_numbers() -> None:
    experiment = load_experiment("configs/dev/i3_mini.json")
    a, b = [runner.run_replica(cfg, 7) for cfg in experiment.configs]
    pd.testing.assert_frame_equal(a.loc[:, :"t_seated"], b.loc[:, :"t_seated"])
    assert a["t_exit"].notna().all() and b["t_exit"].notna().all()
    upper = a["tier"].eq("upper")
    assert (b.loc[upper, "t_exit_queue"] - a.loc[upper, "t_exit_queue"]).to_numpy() == (
        pytest.approx([experiment.configs[1].exit_stagger_min] * upper.sum())
    )

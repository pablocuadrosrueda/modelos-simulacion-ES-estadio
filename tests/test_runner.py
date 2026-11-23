"""Integración real de llegadas, tornos y asientos (T1.4)."""

from __future__ import annotations

from dataclasses import asdict

import numpy as np
import pytest

from conftest import MINI_OVERRIDES
from sanmames import runner
from sanmames.config import Config, deep_merge, load_config, load_experiment
from sanmames.entities import INCIDENT_COLUMNS, SPECTATOR_COLUMNS, Spectator, min_to_s


def test_replica_schema_and_completed_entry(mini_config: Config) -> None:
    df = runner.run_replica(mini_config, seed=7)
    assert list(df.columns) == SPECTATOR_COLUMNS
    assert len(df) == mini_config.n_spectators
    assert df["id"].tolist() == list(range(mini_config.n_spectators))
    assert df["t_arrival"].is_monotonic_increasing
    assert df[["t_start_control", "t_end_control", "t_vomitory", "t_seated"]].notna().all().all()
    assert (df["gate_used"] == df["gate"]).all()
    assert (df["zone"] == "A").all()
    assert df["gate"].dtype.kind in "iu"
    assert df["late"].dtype.kind == "b"
    np.testing.assert_array_equal(
        df["late"],
        (df["t_arrival"] < mini_config.t_start_min) & (df["t_seated"] > mini_config.t_start_min),
    )


def test_replica_metadata(mini_config: Config) -> None:
    df = runner.run_replica(mini_config, seed=19)
    assert df.attrs["seed"] == 19
    assert df.attrs["scenario"] == mini_config.name
    assert list(df.attrs["incidents"].columns) == INCIDENT_COLUMNS
    assert df.attrs["incidents"].empty


def test_future_phases_have_no_events(mini_config: Config) -> None:
    df = runner.run_replica(mini_config, seed=7)
    assert df[["t_exit_queue", "t_exit", "t_safe"]].isna().all().all()
    assert (df["exit_id"] == -1).all()
    assert not df[["read_failure", "conflict", "abandoned"]].any().any()


def test_different_seeds_change_arrivals(mini_config: Config) -> None:
    a = runner.run_replica(mini_config, seed=1)
    b = runner.run_replica(mini_config, seed=2)
    assert not a["t_arrival"].equals(b["t_arrival"])


def test_single_spectator_timing() -> None:
    cfg = load_config(
        overrides={
            **MINI_OVERRIDES,
            "n_spectators": 1,
            "service_time_s": {"low": 4, "mode": 4, "high": 4},
            "vomitory_pass_s": {"low": 10, "mode": 10, "high": 10},
        }
    )
    sp = runner.run_replica(cfg, seed=3).iloc[0]
    assert sp.t_start_control == pytest.approx(sp.t_arrival)
    assert sp.t_end_control == pytest.approx(sp.t_arrival + 4 / 60)
    assert sp.t_vomitory == pytest.approx(sp.t_end_control + sp.distance_m / sp.speed_mps / 60)
    assert sp.t_seated == pytest.approx(sp.t_vomitory + 10 / 60)


def test_simultaneous_arrivals_keep_fifo(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = load_config(overrides={**MINI_OVERRIDES, "n_spectators": 3, "turnstiles_per_gate": 1})
    spectators = [
        Spectator(i, "A", 1, 1, "lower", "standard", 1.0, 60.0, -20.0, 4.0) for i in range(3)
    ]
    monkeypatch.setattr(runner, "generate_spectators", lambda config, rngs: spectators)
    df = runner.run_replica(cfg, seed=1)
    np.testing.assert_allclose(df["t_start_control"], [-20, -20 + 4 / 60, -20 + 8 / 60])


def test_stops_when_last_spectator_sits(
    mini_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    contexts = []
    original = runner.build_entry_resources

    def capture_context(ctx):
        contexts.append(ctx)
        return original(ctx)

    monkeypatch.setattr(runner, "build_entry_resources", capture_context)
    df = runner.run_replica(mini_config, seed=7)
    assert contexts[0].env.now == pytest.approx(min_to_s(df["t_seated"].max()))
    assert contexts[0].env.now < min_to_s(mini_config.t_open_min + mini_config.max_sim_hours * 60)


def test_time_limit_preserves_pending_spectators(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = load_config(overrides={**MINI_OVERRIDES, "n_spectators": 2, "max_sim_hours": 30 / 3600})
    spectators = [
        Spectator(i, "A", 1, 1, "lower", "standard", 1.0, 60.0, -90.0 + i, 4.0) for i in range(2)
    ]
    monkeypatch.setattr(runner, "generate_spectators", lambda config, rngs: spectators)
    df = runner.run_replica(cfg, seed=1)
    assert len(df) == 2
    assert df.loc[0, "t_end_control"] == pytest.approx(-90 + 4 / 60)
    assert df.loc[0, ["t_vomitory", "t_seated"]].isna().all()
    assert df.loc[1, ["t_start_control", "t_end_control", "t_seated"]].isna().all()
    assert df.loc[1, "gate_used"] == -1


def test_multiple_zones() -> None:
    cfg = load_config(overrides={**MINI_OVERRIDES, "zones": ["A", "B"], "zone_share": [0.5, 0.5]})
    df = runner.run_replica(cfg, seed=1)
    assert set(df["zone"]) == {"A", "B"}
    assert df["t_seated"].notna().all()


def test_rejects_unimplemented_read_failure() -> None:
    cfg = load_config(
        overrides=deep_merge(MINI_OVERRIDES, {"incidents": {"read_failure": {"enabled": True}}})
    )
    with pytest.raises(NotImplementedError, match="T2.2"):
        runner.run_replica(cfg, seed=1)


def test_rejects_emergency(mini_config: Config) -> None:
    cfg = load_config(overrides={**MINI_OVERRIDES, "emergency": {"enabled": True}})
    with pytest.raises(NotImplementedError, match="Inc4"):
        runner.run_replica(cfg, seed=1)


def test_accepts_priority_queue() -> None:
    cfg = load_config(overrides={**MINI_OVERRIDES, "queue_discipline": "priority"})
    assert runner.run_replica(cfg, seed=1)["t_seated"].notna().all()


def test_development_config() -> None:
    experiment = load_experiment("configs/dev/i1_mini.json")
    cfg = experiment.configs[0]
    df = runner.run_replica(cfg, seed=20261105)
    assert cfg.zones == ("A",)
    assert len(df) == cfg.n_spectators == 600
    assert df["t_seated"].notna().all()


def test_config_unchanged(mini_config: Config) -> None:
    before = asdict(mini_config)
    runner.run_replica(mini_config, seed=1)
    assert asdict(mini_config) == before

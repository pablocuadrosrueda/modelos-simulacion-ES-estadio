"""T4.3: alarma desde el runner, interrupciones, conservación y KPIs de evacuación."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from conftest import MINI_OVERRIDES
from sanmames import runner
from sanmames.config import deep_merge, load_config
from sanmames.entities import SPECTATOR_COLUMNS, Spectator
from sanmames.metrics import compute_kpis


def config(extra=None):
    overrides = deep_merge(
        MINI_OVERRIDES,
        {
            "n_spectators": 4,
            "gates_per_zone": 1,
            "turnstiles_per_gate": 1,
            "emergency": {
                "enabled": True,
                "alarm_min": 40,
                "reaction_s": {"low": 0, "mode": 0, "high": 0},
            },
        },
    )
    return load_config(overrides=deep_merge(overrides, extra or {}))


def capture_context(monkeypatch):
    contexts = []
    original = runner.build_entry_resources

    def capture(ctx):
        contexts.append(ctx)
        return original(ctx)

    monkeypatch.setattr(runner, "build_entry_resources", capture)
    return contexts


def test_alarm_handles_seated_control_queue_and_future_arrival(monkeypatch) -> None:
    cfg = config()
    spectators = [
        Spectator(0, "A", 1, 1, "lower", "standard", 1, 0, -80, 0),
        Spectator(1, "A", 1, 1, "lower", "standard", 1, 0, 39.9, 60),
        Spectator(2, "A", 1, 1, "lower", "standard", 1, 0, 39.9, 4),
        Spectator(3, "A", 1, 1, "lower", "standard", 1, 0, 41, 4),
    ]
    monkeypatch.setattr(runner, "generate_spectators", lambda config, rngs: spectators)
    contexts = capture_context(monkeypatch)
    df = runner.run_replica(cfg, 1)
    assert df["t_exit"].isna().all()
    assert df["abandoned"].tolist() == [False, True, True, False]
    assert df["t_safe"].notna().tolist() == [True, False, False, False]
    assert math.isnan(df.loc[3, "t_start_control"])
    # Cada id termina exactamente en una población: seguro, abandona, no llegó.
    states = pd.DataFrame(
        {
            "safe": df.t_safe.notna(),
            "abandoned": df.abandoned,
            "not_arrived": df.t_arrival > cfg.emergency.alarm_min,
        }
    )
    assert states.sum(axis=1).eq(1).all()
    assert states.to_numpy().sum() == cfg.n_spectators
    ctx = contexts[0]
    assert not any(ctx.entry.gate_open.values())
    for resources in [
        ctx.entry.turnstiles,
        ctx.stadium.vomitories,
        ctx.stadium.stewards,
        ctx.exits.exits,
    ]:
        assert all(resource.count == 0 and not resource.queue for resource in resources.values())
    assert df.attrs["alarm_triggered"] is True
    assert df.attrs["stop_time_min"] == pytest.approx(df.t_safe.max())
    kpis = compute_kpis(df, cfg)
    assert kpis["n_abandoned"] == 2
    assert kpis["evac_pct_ref"] == 100
    assert math.isnan(kpis["exit_time_min"]) and math.isnan(kpis["exit_queue_max"])


def test_interruption_releases_active_conflicts(monkeypatch) -> None:
    cfg = config(
        {
            "n_spectators": 3,
            "vomitory_capacity": 1,
            "stewards_per_zone": 1,
            "vomitory_pass_s": {"low": 0, "mode": 0, "high": 0},
            "incidents": {
                "seat_conflict": {
                    "enabled": True,
                    "prob": 1,
                    "resolution_min": {"low": 10, "mode": 10, "high": 10},
                }
            },
        }
    )
    spectators = [Spectator(i, "A", 1, 1, "lower", "standard", 1, 0, 39, 0) for i in range(3)]
    monkeypatch.setattr(runner, "generate_spectators", lambda config, rngs: spectators)
    contexts = capture_context(monkeypatch)
    df = runner.run_replica(cfg, 1)
    assert df.t_safe.notna().all()
    assert df.t_seated.isna().all()
    conflicts = df.attrs["incidents"].query('kind == "I1"')
    assert len(conflicts) == 1
    assert conflicts.t_end.tolist() == [40]
    ctx = contexts[0]
    assert all(resource.count == 0 for resource in ctx.stadium.vomitories.values())
    assert all(resource.count == 0 for resource in ctx.stadium.stewards.values())


@pytest.mark.parametrize(("blocked", "expected"), [(False, 5.9), (True, 7.1)])
def test_full_runner_evacuation_capacity_reference(blocked, expected, monkeypatch) -> None:
    cfg = config(
        {
            "n_spectators": 12195,
            "vomitory_pass_s": {"low": 0, "mode": 0, "high": 0},
            "emergency": {"blocked_exit": blocked},
        }
    )
    spectators = [
        Spectator(i, "A", 1, 1, "lower", "standard", 1, 0, -80, 0) for i in range(cfg.n_spectators)
    ]
    monkeypatch.setattr(runner, "generate_spectators", lambda config, rngs: spectators)
    df = runner.run_replica(cfg, 1)
    assert df.t_safe.notna().all() and df.t_exit.isna().all()
    assert not df.abandoned.any()
    kpis = compute_kpis(df, cfg)
    assert kpis["evac_time_min"] == pytest.approx(expected, abs=0.05)
    assert kpis["evac_pct_ref"] == 100
    if blocked:
        assert 1 not in set(df.exit_id)


def test_evacuation_kpis_include_unfinished_and_exclude_outside() -> None:
    cfg = config({"n_spectators": 5, "emergency": {"reference_min": 8}})
    df = pd.DataFrame(
        {
            "t_end_control": [0, 0, 0, math.nan, math.nan],
            "t_exit": [math.nan] * 5,
            "t_safe": [47, 48, math.nan, math.nan, math.nan],
            "abandoned": [False, False, False, True, False],
        }
    ).reindex(columns=SPECTATOR_COLUMNS)
    df.attrs.update(alarm_triggered=True, stop_time_min=49)
    kpis = compute_kpis(df, cfg)
    assert kpis["evac_pct_ref"] == pytest.approx(200 / 3)
    assert math.isnan(kpis["evac_time_min"])
    assert kpis["n_abandoned"] == 1
    df.attrs["stop_time_min"] = 47.5
    assert math.isnan(compute_kpis(df, cfg)["evac_pct_ref"])
    df.loc[2, "t_safe"] = 49
    df.attrs["stop_time_min"] = 49
    assert compute_kpis(df, cfg)["evac_time_min"] == 9
    assert compute_kpis(df, cfg)["evac_pct_ref"] == pytest.approx(200 / 3)


@pytest.mark.parametrize("duration", [100, 130.2])
def test_limit_before_alarm_or_during_reaction(duration, monkeypatch) -> None:
    cfg = config(
        {
            "n_spectators": 1,
            "max_sim_hours": duration / 60,
            "emergency": {"reaction_s": {"low": 60, "mode": 60, "high": 60}},
        }
    )
    spectators = [Spectator(0, "A", 1, 1, "lower", "standard", 1, 0, -80, 0)]
    monkeypatch.setattr(runner, "generate_spectators", lambda config, rngs: spectators)
    df = runner.run_replica(cfg, 1)
    assert df.t_safe.isna().all()
    assert df.attrs["alarm_triggered"] == (duration > 130)
    kpis = compute_kpis(df, cfg)
    assert math.isnan(kpis["evac_time_min"]) and math.isnan(kpis["evac_pct_ref"])


def test_all_future_arrivals_finish_without_fictitious_evacuees(monkeypatch) -> None:
    cfg = config({"n_spectators": 1})
    monkeypatch.setattr(
        runner,
        "generate_spectators",
        lambda config, rngs: [Spectator(0, "A", 1, 1, "lower", "standard", 1, 0, 41, 4)],
    )
    df = runner.run_replica(cfg, 1)
    kpis = compute_kpis(df, cfg)
    assert df.attrs["stop_time_min"] == 40
    assert kpis["n_abandoned"] == 0
    assert math.isnan(kpis["evac_time_min"]) and math.isnan(kpis["evac_pct_ref"])


def test_read_failures_integrated_with_real_metrics(monkeypatch) -> None:
    cfg = config(
        {
            "n_spectators": 3,
            "emergency": {"enabled": False},
            "incidents": {
                "read_failure": {"enabled": True, "prob": 1, "extra_s": {"low": 10, "high": 10}}
            },
        }
    )
    monkeypatch.setattr(
        runner,
        "generate_spectators",
        lambda config, rngs: [
            Spectator(i, "A", 1, 1, "lower", "standard", 1, 0, -80, 4) for i in range(3)
        ],
    )
    df = runner.run_replica(cfg, 1)
    assert df.read_failure.all() and df.t_exit.notna().all()
    assert ((df.t_end_control - df.t_start_control) * 60).to_numpy() == pytest.approx([14] * 3)
    assert compute_kpis(df, cfg)["n_read_failures"] == 3

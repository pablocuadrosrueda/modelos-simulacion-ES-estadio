"""I2 · fallo de lectura en el torno (entry.py, T2.2)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
import simpy

from conftest import MINI_OVERRIDES
from sanmames.arrivals import generate_spectators
from sanmames.config import Config, deep_merge, load_config
from sanmames.entities import Spectator, min_to_s
from sanmames.entry import build_entry_resources, entry_process, has_read_failure
from sanmames.rng import RngStreams
from sanmames.runner import SimContext

EXTRA = 10.0  # s, extra fijo (low == high) para comprobar duraciones exactas


def rf_config(
    *,
    enabled: bool = True,
    prob: float = 0.03,
    extra: tuple[float, float] = (5.0, 15.0),
    **other: Any,
) -> Config:
    overrides = deep_merge(
        MINI_OVERRIDES,
        {
            "incidents": {
                "read_failure": {
                    "enabled": enabled,
                    "prob": prob,
                    "extra_s": {"low": extra[0], "high": extra[1]},
                }
            }
        },
    )
    return load_config(overrides=deep_merge(overrides, other))


def make_ctx(config: Config, seed: int = 1) -> SimContext:
    env = simpy.Environment(initial_time=min_to_s(config.t_open_min))
    ctx = SimContext(env=env, config=config, rngs=RngStreams(seed))
    ctx.entry = build_entry_resources(ctx)
    return ctx


def run_mini(config: Config, seed: int = 1) -> tuple[SimContext, list[Spectator]]:
    ctx = make_ctx(config, seed)
    sps = generate_spectators(config, ctx.rngs)
    ctx.spectators = sps
    for sp in sps:
        ctx.env.process(entry_process(sp, ctx))
    ctx.env.run()
    return ctx, sps


def failures(config: Config, seed: int = 1) -> set[int]:
    ctx = make_ctx(config, seed)
    return {
        i
        for i in range(config.n_spectators)
        if has_read_failure(_stub(i), ctx)  # solo depende de id
    }


def _stub(i: int) -> Spectator:
    return Spectator(i, "A", 1, 1, "lower", "standard", 1.4, 100.0, -30.0, 4.0)


def extras(config: Config, seed: int = 1) -> np.ndarray:
    ctx = make_ctx(config, seed)
    assert ctx.entry is not None
    return ctx.entry.read_failure_extra_s


def outcome(sps: list[Spectator]) -> list[tuple[int, float, float, bool]]:
    return [(s.gate_used, s.t_start_control, s.t_end_control, s.read_failure) for s in sps]


# -- activación ---------------------------------------------------------------


def test_disabled_no_failures_and_same_times_as_without_incident() -> None:
    off = rf_config(enabled=False, prob=1.0)
    ctx, sps = run_mini(off)
    assert not any(s.read_failure for s in sps)
    assert ctx.incidents == []
    _, plain = run_mini(load_config(overrides=MINI_OVERRIDES))
    assert outcome(sps) == outcome(plain)


def test_prob_zero_no_failures() -> None:
    ctx, sps = run_mini(rf_config(prob=0.0))
    assert not any(s.read_failure for s in sps)
    assert ctx.incidents == []


def test_prob_one_everybody_rereads_with_fixed_extra() -> None:
    ctx, sps = run_mini(rf_config(prob=1.0, extra=(EXTRA, EXTRA)))
    assert all(s.read_failure for s in sps)
    for s in sps:
        assert s.t_end_control - s.t_start_control == pytest.approx(
            (s.service_s + EXTRA) / 60, abs=1e-9
        )
    assert len(ctx.incidents) == len(sps)


# -- registro -------------------------------------------------------------------


def test_incidents_logged_with_spectator_gate_and_times() -> None:
    ctx, sps = run_mini(rf_config(prob=0.2))
    by_id = {s.id: s for s in sps}
    incs = [i for i in ctx.incidents if i.kind == "I2"]
    assert {i.spectator_id for i in incs} == {s.id for s in sps if s.read_failure}
    assert len(incs) == sum(s.read_failure for s in sps) > 0
    for inc in incs:
        s = by_id[inc.spectator_id]
        assert inc.zone == s.zone
        assert inc.resource == f"{s.zone}-G{s.gate_used}"
        assert inc.t_start < inc.t_end
        assert inc.t_start == pytest.approx(s.t_start_control + s.service_s / 60, abs=1e-9)
        assert inc.t_end == pytest.approx(s.t_end_control, abs=1e-9)


# -- el torno queda ocupado ---------------------------------------------------


def test_reread_keeps_turnstile_busy() -> None:
    cfg = rf_config(prob=1.0, extra=(EXTRA, EXTRA), turnstiles_per_gate=1)
    ctx = make_ctx(cfg)
    first = Spectator(0, "A", 1, 1, "lower", "standard", 1.4, 100.0, -30.0, 4.0)
    second = Spectator(1, "A", 1, 1, "lower", "standard", 1.4, 100.0, -30.0, 4.0)
    ctx.spectators = [first, second]
    for s in ctx.spectators:
        ctx.env.process(entry_process(s, ctx))
    ctx.env.run()
    assert second.t_start_control == pytest.approx(first.t_end_control, abs=1e-9)
    assert second.t_start_control - first.t_start_control == pytest.approx(
        (4.0 + EXTRA) / 60, abs=1e-9
    )


# -- estadística ----------------------------------------------------------------


def test_frequency_and_extra_distribution() -> None:
    cfg = rf_config(n_spectators=48775)
    n_fail = len(failures(cfg))
    p = cfg.incidents.read_failure.prob
    sd = (cfg.n_spectators * p * (1 - p)) ** 0.5
    assert abs(n_fail - cfg.n_spectators * p) < 4 * sd
    ex = extras(cfg)
    assert ex.min() >= 5.0 and ex.max() <= 15.0
    assert ex.mean() == pytest.approx(10.0, abs=0.1)


# -- números aleatorios comunes (D26) -------------------------------------------


def test_set_grows_with_prob_and_extra_is_common() -> None:
    low, high = rf_config(prob=0.03), rf_config(prob=0.06)
    f_low, f_high = failures(low), failures(high)
    assert f_low and f_low < f_high
    np.testing.assert_array_equal(extras(low), extras(high))


@pytest.mark.parametrize(
    "other",
    [{"turnstiles_per_gate": 2}, {"turnstiles_per_gate": 4}, {"arrival_profile": "anticipated"}],
)
def test_same_failures_across_scenarios(other: dict[str, Any]) -> None:
    base = rf_config(prob=0.1)
    variant = rf_config(prob=0.1, **other)
    assert failures(base) == failures(variant)
    np.testing.assert_array_equal(extras(base), extras(variant))
    _, sps = run_mini(variant)
    assert {s.id for s in sps if s.read_failure} == failures(base)


def test_reproducible_and_seed_dependent() -> None:
    cfg = rf_config(prob=0.1)
    assert outcome(run_mini(cfg, 3)[1]) == outcome(run_mini(cfg, 3)[1])
    assert failures(cfg, 3) != failures(cfg, 4)

"""Salida ordinaria (exit.py, T3.1) y política de liberación (T3.2)."""

from __future__ import annotations

import math

import numpy as np
import pytest
import simpy

from conftest import MINI_OVERRIDES
from sanmames.arrivals import generate_spectators
from sanmames.config import Config, load_config
from sanmames.entities import Spectator, min_to_s
from sanmames.entry import build_entry_resources, entry_process
from sanmames.exit import (
    build_exit_resources,
    choose_exit,
    exit_pass_time_s,
    exit_process,
    release_time_min,
)
from sanmames.rng import RngStreams
from sanmames.runner import SimContext
from sanmames.stadium import build_stadium_resources, seating_process


def make_ctx(config: Config, seed: int = 1) -> SimContext:
    env = simpy.Environment(initial_time=min_to_s(config.t_open_min))
    ctx = SimContext(env=env, config=config, rngs=RngStreams(seed))
    ctx.entry = build_entry_resources(ctx)
    ctx.stadium = build_stadium_resources(ctx)
    ctx.exits = build_exit_resources(ctx)
    return ctx


def make_spectator(
    i: int,
    zone: str = "A",
    block: int = 1,
    speed_mps: float = 1.0,
    distance_m: float = 60.0,
    t_seated: float = -5.0,
) -> Spectator:
    tier = "lower" if block <= 5 else "upper"
    sp = Spectator(i, zone, 1, block, tier, "standard", speed_mps, distance_m, -30.0, 4.0)
    sp.t_seated = t_seated
    return sp


def run_exit(ctx: SimContext, sps: list[Spectator]) -> None:
    ctx.spectators = sps
    for sp in sps:
        ctx.env.process(exit_process(sp, ctx))
    ctx.env.run()


# -- recursos y paso -------------------------------------------------------------


def test_exit_pass_time() -> None:
    assert exit_pass_time_s(4.0, 66) == pytest.approx(60 / 264)
    assert exit_pass_time_s(4.0 * 1.3, 66) == pytest.approx(0.1748, abs=1e-4)
    with pytest.raises(ValueError):
        exit_pass_time_s(0.0, 66)


def test_build_exit_resources(base_config: Config) -> None:
    ctx = make_ctx(base_config)
    res = ctx.exits
    keys = {(z, e) for z in base_config.zones for e in range(1, base_config.exits_per_zone + 1)}
    assert set(res.exits) == set(res.pass_time_s) == keys
    for k in keys:
        assert res.exits[k].capacity == 1
        assert res.pass_time_s[k] == pytest.approx(60 / base_config.exit_rate_per_exit_min)
    assert res.blocked == set()
    assert res.tie_u.shape == (base_config.n_spectators,)
    assert 0 <= res.tie_u.min() and res.tie_u.max() < 1


def test_tie_numbers_common_across_scenarios() -> None:
    a = make_ctx(load_config(overrides={**MINI_OVERRIDES, "exit_policy": "simultaneous"}), seed=3)
    b = make_ctx(load_config(overrides={**MINI_OVERRIDES, "exit_policy": "staggered"}), seed=3)
    np.testing.assert_array_equal(a.exits.tie_u, b.exits.tie_u)


# -- liberación (E5) -------------------------------------------------------------


def test_release_simultaneous(mini_config: Config) -> None:
    ctx = make_ctx(mini_config)
    assert release_time_min(make_spectator(0, block=1), ctx) == mini_config.t_end_min
    assert release_time_min(make_spectator(1, block=8), ctx) == mini_config.t_end_min


def test_release_staggered() -> None:
    cfg = load_config(overrides={**MINI_OVERRIDES, "exit_policy": "staggered"})
    ctx = make_ctx(cfg)
    assert release_time_min(make_spectator(0, block=2), ctx) == cfg.t_end_min
    assert release_time_min(make_spectator(1, block=7), ctx) == cfg.t_end_min + cfg.exit_stagger_min


# -- elección de salida ----------------------------------------------------------


def test_choose_exit_shortest_queue(mini_config: Config) -> None:
    ctx = make_ctx(mini_config)
    ctx.exits.tie_u[:] = 0.0  # empate -> la de menor id
    # Ocupa la salida 1 y pone a dos en cola en la 2; las demás vacías salvo la 3 (1 persona).
    reqs = [ctx.exits.exits[("A", 1)].request()]
    reqs += [ctx.exits.exits[("A", 2)].request() for _ in range(3)]
    reqs += [ctx.exits.exits[("A", 3)].request()]
    ctx.env.run(until=ctx.env.now + 0.001)
    assert choose_exit(make_spectator(0), ctx) == 4
    for e in range(4, mini_config.exits_per_zone + 1):
        reqs.append(ctx.exits.exits[("A", e)].request())
    ctx.env.run(until=ctx.env.now + 0.001)
    # Ahora 1, 3, 4, 5, 6 tienen una persona y la 2 tiene tres: empate entre 1, 3-6.
    assert choose_exit(make_spectator(0), ctx) == 1


def test_choose_exit_tie_break_uses_spectator_number(mini_config: Config) -> None:
    ctx = make_ctx(mini_config)
    k = mini_config.exits_per_zone
    for j in range(k):
        ctx.exits.tie_u[j] = (j + 0.5) / k
    assert [choose_exit(make_spectator(j), ctx) for j in range(k)] == list(range(1, k + 1))
    ctx.exits.tie_u[0] = np.nextafter(1.0, 0.0)
    assert choose_exit(make_spectator(0), ctx) == k


def test_choose_exit_skips_blocked(mini_config: Config) -> None:
    ctx = make_ctx(mini_config)
    ctx.exits.blocked = {("A", e) for e in range(1, mini_config.exits_per_zone)}
    assert choose_exit(make_spectator(0), ctx) == mini_config.exits_per_zone
    ctx.exits.blocked.add(("A", mini_config.exits_per_zone))
    with pytest.raises(RuntimeError):
        choose_exit(make_spectator(0), ctx)


# -- proceso de salida -----------------------------------------------------------


def test_single_spectator_exit_times(mini_config: Config) -> None:
    ctx = make_ctx(mini_config)
    sp = make_spectator(0, speed_mps=1.2, distance_m=90.0)
    run_exit(ctx, [sp])
    walk_min = 90.0 / 1.2 / 60
    assert sp.t_exit_queue == pytest.approx(mini_config.t_end_min + walk_min)
    assert sp.t_exit == pytest.approx(sp.t_exit_queue + exit_pass_time_s(4.0, 66) / 60)
    assert 1 <= sp.exit_id <= mini_config.exits_per_zone


def test_late_seated_leaves_on_arrival(mini_config: Config) -> None:
    """Quien se sienta después de E5 sale en cuanto se lanza el proceso."""
    ctx = make_ctx(mini_config)
    sp = make_spectator(0, distance_m=60.0, speed_mps=1.0, t_seated=110.0)
    ctx.spectators = [sp]

    def later():
        yield ctx.env.timeout(min_to_s(110.0) - ctx.env.now)
        yield from exit_process(sp, ctx)

    ctx.env.process(later())
    ctx.env.run()
    assert sp.t_exit_queue == pytest.approx(111.0)


def test_requires_seated(mini_config: Config) -> None:
    ctx = make_ctx(mini_config)
    sp = make_spectator(0, t_seated=math.nan)
    ctx.env.process(exit_process(sp, ctx))
    with pytest.raises(AssertionError):
        ctx.env.run()


def test_exit_capacity_one_per_pass_time(mini_config: Config) -> None:
    """Cada salida deja pasar a una persona cada ``pass_time_s``, sin solaparse."""
    ctx = make_ctx(mini_config)
    sps = [make_spectator(i) for i in range(120)]  # llegan todos a la vez
    run_exit(ctx, sps)
    pass_s = exit_pass_time_s(4.0, 66)
    for e in range(1, mini_config.exits_per_zone + 1):
        t = np.sort([min_to_s(sp.t_exit) for sp in sps if sp.exit_id == e])
        assert len(t) == 120 // mini_config.exits_per_zone  # el reparto es uniforme
        np.testing.assert_allclose(np.diff(t), pass_s, rtol=1e-6)


def test_zone_exit_time_matches_memoria() -> None:
    """Validación (apartado 4.3 de la memoria): una macrozona sale por sus 6 salidas en 7,7 min."""
    cfg = load_config(overrides={**MINI_OVERRIDES, "n_spectators": 12_195})
    ctx = make_ctx(cfg)
    sps = [make_spectator(i, distance_m=1.0, speed_mps=1.0) for i in range(cfg.n_spectators)]
    run_exit(ctx, sps)
    crossing_min = max(sp.t_exit for sp in sps) - min(sp.t_exit_queue for sp in sps)
    assert crossing_min == pytest.approx(7.7, abs=0.05)
    counts = np.bincount([sp.exit_id for sp in sps])[1:]
    assert counts.max() - counts.min() <= 1


def test_staggered_upper_tier_waits() -> None:
    cfg = load_config(overrides={**MINI_OVERRIDES, "exit_policy": "staggered"})
    ctx = make_ctx(cfg)
    lower, upper = make_spectator(0, block=1), make_spectator(1, block=9)
    run_exit(ctx, [lower, upper])
    assert upper.t_exit_queue - lower.t_exit_queue == pytest.approx(cfg.exit_stagger_min)


def test_full_journey_order(mini_config: Config) -> None:
    ctx = make_ctx(mini_config, seed=9)
    sps = generate_spectators(mini_config, ctx.rngs)
    ctx.spectators = sps

    def journey(sp: Spectator):
        yield from entry_process(sp, ctx)
        yield from seating_process(sp, ctx)
        yield from exit_process(sp, ctx)

    for sp in sps:
        ctx.env.process(journey(sp))
    ctx.env.run()

    for sp in sps:
        assert sp.t_seated <= sp.t_exit_queue <= sp.t_exit
        assert sp.t_exit_queue >= mini_config.t_end_min
        assert sp.t_exit_queue == pytest.approx(
            max(mini_config.t_end_min, sp.t_seated) + sp.distance_m / sp.speed_mps / 60
        )
        assert 1 <= sp.exit_id <= mini_config.exits_per_zone

"""I1 · Conflicto por asiento con acomodadores (incidents.py + stadium.py, T2.5)."""

from __future__ import annotations

import numpy as np
import pytest
import simpy

from conftest import MINI_OVERRIDES
from sanmames.arrivals import generate_spectators
from sanmames.config import Config, deep_merge, load_config
from sanmames.entities import Spectator, min_to_s
from sanmames.entry import build_entry_resources, entry_process
from sanmames.incidents import has_seat_conflict, sample_seat_conflicts
from sanmames.rng import RngStreams
from sanmames.runner import SimContext
from sanmames.stadium import build_stadium_resources, seating_process


def conflict_config(prob: float = 0.005, **extra) -> Config:
    over = deep_merge(
        MINI_OVERRIDES, {"incidents": {"seat_conflict": {"enabled": True, "prob": prob}}}
    )
    return load_config(overrides=deep_merge(over, extra))


def make_ctx(config: Config, seed: int = 1) -> SimContext:
    env = simpy.Environment(initial_time=min_to_s(config.t_open_min))
    ctx = SimContext(env=env, config=config, rngs=RngStreams(seed))
    ctx.entry = build_entry_resources(ctx)
    ctx.stadium = build_stadium_resources(ctx)
    return ctx


def make_spectator(i: int, block: int = 1, zone: str = "A", t_end_control: float = -10.0):
    sp = Spectator(i, zone, 1, block, "lower", "standard", 1.0, 60.0, t_end_control - 1, 4.0)
    sp.t_start_control = t_end_control - 4.0 / 60
    sp.t_end_control = t_end_control
    return sp


def force(ctx: SimContext, ids, *, conflict: bool, pass_s=None, resolution_s=None) -> None:
    """Fija a mano los números de E0 de unos espectadores (conflicto sí/no y duraciones)."""
    st = ctx.stadium
    for i in ids:
        st.seat_conflict_u[i] = 0.0 if conflict else 1.0
        if pass_s is not None:
            st.vomitory_pass_s[i] = pass_s
        if resolution_s is not None:
            st.seat_conflict_resolution_s[i] = resolution_s


def run_seating(ctx: SimContext, sps: list[Spectator]) -> None:
    ctx.spectators = sps
    for sp in sps:
        ctx.env.process(seating_process(sp, ctx))
    ctx.env.run()


def seated_s(sp: Spectator) -> float:
    return min_to_s(sp.t_seated)


# -- sorteo con números comunes (D21) -------------------------------------------


def test_sample_seat_conflicts_distribution(base_config: Config) -> None:
    params = base_config.incidents.seat_conflict
    n = 200_000
    u, res_s = sample_seat_conflicts(params, n, np.random.default_rng(0))
    assert u.shape == res_s.shape == (n,)
    assert 0 <= u.min() and u.max() < 1
    tri = params.resolution_min
    assert res_s.min() >= tri.low * 60 and res_s.max() <= tri.high * 60
    assert res_s.mean() == pytest.approx(tri.mean * 60, rel=0.01)
    # Proporción de conflictos ~ Binomial(n, 0,005): ±4 desviaciones típicas.
    p = params.prob
    assert abs((u < p).mean() - p) < 4 * np.sqrt(p * (1 - p) / n)


def test_draws_stored_per_spectator_and_common_across_scenarios() -> None:
    a = make_ctx(conflict_config(prob=0.005, stewards_per_zone=3), seed=4)
    b = make_ctx(conflict_config(prob=0.01, stewards_per_zone=6), seed=4)
    n = a.config.n_spectators
    assert a.stadium.seat_conflict_u.shape == (n,)
    np.testing.assert_array_equal(a.stadium.seat_conflict_u, b.stadium.seat_conflict_u)
    np.testing.assert_array_equal(
        a.stadium.seat_conflict_resolution_s, b.stadium.seat_conflict_resolution_s
    )


def test_higher_prob_keeps_previous_conflicts() -> None:
    lo = make_ctx(conflict_config(prob=0.005, n_spectators=20_000), seed=2)
    hi = make_ctx(conflict_config(prob=0.01, n_spectators=20_000), seed=2)
    sps = [make_spectator(i) for i in range(20_000)]
    in_lo = {sp.id for sp in sps if has_seat_conflict(sp, lo)}
    in_hi = {sp.id for sp in sps if has_seat_conflict(sp, hi)}
    assert in_lo and in_lo < in_hi


def test_has_seat_conflict_disabled_or_extreme(mini_config: Config) -> None:
    sps = [make_spectator(i) for i in range(mini_config.n_spectators)]
    off = make_ctx(mini_config)
    force(off, range(len(sps)), conflict=True)  # aunque u = 0, desactivada => no
    assert not any(has_seat_conflict(sp, off) for sp in sps)
    assert all(has_seat_conflict(sp, make_ctx(conflict_config(prob=1.0))) for sp in sps)
    assert not any(has_seat_conflict(sp, make_ctx(conflict_config(prob=0.0))) for sp in sps)


# -- proceso de conflicto ---------------------------------------------------------


def test_single_conflict_times_and_incident() -> None:
    ctx = make_ctx(conflict_config())
    sp = make_spectator(5, block=3)
    force(ctx, [5], conflict=True, pass_s=10.0, resolution_s=120.0)
    run_seating(ctx, [sp])

    assert sp.conflict is True
    assert seated_s(sp) - min_to_s(sp.t_vomitory) == pytest.approx(10.0 + 120.0)
    assert len(ctx.incidents) == 1
    inc = ctx.incidents[0]
    assert (inc.kind, inc.zone, inc.resource, inc.spectator_id) == ("I1", "A", "A-B3", 5)
    assert min_to_s(inc.t_start) == pytest.approx(min_to_s(sp.t_vomitory) + 10.0)
    assert inc.t_end == pytest.approx(sp.t_seated)


def test_no_conflict_unchanged() -> None:
    ctx = make_ctx(conflict_config())
    sp = make_spectator(0)
    force(ctx, [0], conflict=False, pass_s=10.0)
    run_seating(ctx, [sp])
    assert sp.conflict is False
    assert ctx.incidents == []
    assert seated_s(sp) - min_to_s(sp.t_vomitory) == pytest.approx(10.0)


def test_conflict_holds_vomitory_place() -> None:
    """Los 8 primeros tienen conflicto y llenan el vomitorio; el 9.º espera a que se libere."""
    ctx = make_ctx(conflict_config(stewards_per_zone=8))
    cap = ctx.config.vomitory_capacity
    sps = [make_spectator(i) for i in range(cap + 1)]
    force(ctx, range(cap), conflict=True, pass_s=10.0, resolution_s=60.0)
    force(ctx, [cap], conflict=False, pass_s=10.0)
    run_seating(ctx, sps)

    t0 = min_to_s(sps[0].t_vomitory)
    for sp in sps[:cap]:
        assert seated_s(sp) == pytest.approx(t0 + 70.0)
    # Sin conflicto habría pasado en t0 + 20; espera a que se libere una plaza.
    assert seated_s(sps[cap]) == pytest.approx(t0 + 70.0 + 10.0)


def test_stewards_limit_conflicts_in_parallel() -> None:
    """Con 2 acomodadores, el 3.er conflicto (otro bloque) espera a que quede uno libre."""
    ctx = make_ctx(conflict_config(stewards_per_zone=2))
    sps = [make_spectator(i, block=i + 1) for i in range(3)]
    force(ctx, range(3), conflict=True, pass_s=10.0, resolution_s=60.0)
    run_seating(ctx, sps)

    t0 = min_to_s(sps[0].t_vomitory)
    assert [seated_s(sp) for sp in sps] == pytest.approx([t0 + 70, t0 + 70, t0 + 130])
    durations = sorted(min_to_s(i.t_end) - min_to_s(i.t_start) for i in ctx.incidents)
    assert durations == pytest.approx([60.0, 60.0, 120.0])  # incluye la espera al acomodador


def test_stewards_are_per_zone() -> None:
    ctx = make_ctx(conflict_config(stewards_per_zone=1, zones=["A", "B"], zone_share=[0.5, 0.5]))
    sps = [make_spectator(0, zone="A"), make_spectator(1, zone="B")]
    force(ctx, [0, 1], conflict=True, pass_s=10.0, resolution_s=60.0)
    run_seating(ctx, sps)
    assert seated_s(sps[0]) == pytest.approx(seated_s(sps[1]))


def test_entry_and_seating_with_conflicts() -> None:
    cfg = conflict_config(prob=0.05)
    ctx = make_ctx(cfg, seed=11)
    sps = generate_spectators(cfg, ctx.rngs)
    ctx.spectators = sps

    def journey(sp: Spectator):
        yield from entry_process(sp, ctx)
        yield from seating_process(sp, ctx)

    for sp in sps:
        ctx.env.process(journey(sp))
    ctx.env.run()

    with_conflict = [sp for sp in sps if sp.conflict]
    assert with_conflict  # con p = 5 % y N = 600 hay casi seguro alguno
    assert {sp.id for sp in with_conflict} == {sp.id for sp in sps if has_seat_conflict(sp, ctx)}
    assert len(ctx.incidents) == len(with_conflict)
    assert all(i.kind == "I1" and i.t_end >= i.t_start for i in ctx.incidents)
    st = ctx.stadium
    for sp in sps:
        assert sp.t_end_control <= sp.t_vomitory + 1e-9 and sp.t_vomitory <= sp.t_seated
        floor_s = st.vomitory_pass_s[sp.id] + (
            st.seat_conflict_resolution_s[sp.id] if sp.conflict else 0.0
        )
        assert seated_s(sp) - min_to_s(sp.t_vomitory) >= floor_s - 1e-6

"""Ubicación sin conflictos: vomitorios y asiento (stadium.py, T1.3)."""

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
from sanmames.rng import RngStreams
from sanmames.runner import SimContext
from sanmames.stadium import build_stadium_resources, is_late, seating_process


def make_ctx(config: Config, seed: int = 1) -> SimContext:
    env = simpy.Environment(initial_time=min_to_s(config.t_open_min))
    ctx = SimContext(env=env, config=config, rngs=RngStreams(seed))
    ctx.entry = build_entry_resources(ctx)
    ctx.stadium = build_stadium_resources(ctx)
    return ctx


def make_spectator(
    i: int,
    t_end_control: float,
    block: int = 1,
    zone: str = "A",
    speed_mps: float = 1.0,
    distance_m: float = 60.0,
    t_arrival: float | None = None,
) -> Spectator:
    t_arr = t_end_control - 1.0 if t_arrival is None else t_arrival
    sp = Spectator(i, zone, 1, block, "lower", "standard", speed_mps, distance_m, t_arr, 4.0)
    sp.t_start_control = t_end_control - 4.0 / 60
    sp.t_end_control = t_end_control
    return sp


def run_seating(ctx: SimContext, sps: list[Spectator]) -> None:
    ctx.spectators = sps
    for sp in sps:
        ctx.env.process(seating_process(sp, ctx))
    ctx.env.run()


def max_overlap(starts: np.ndarray, ends: np.ndarray) -> int:
    """Máximo de intervalos [start, end) abiertos a la vez (salida antes que entrada).

    Redondea a µs: la conversión s <-> min deja errores de coma flotante.
    """
    events = sorted([(round(e, 6), -1) for e in ends] + [(round(s, 6), +1) for s in starts])
    level = peak = 0
    for _, delta in events:
        level += delta
        peak = max(peak, level)
    return peak


# -- recursos -----------------------------------------------------------------


def test_build_stadium_resources(base_config: Config) -> None:
    ctx = make_ctx(base_config)
    res = ctx.stadium
    assert res is not None
    keys = {(z, b) for z in base_config.zones for b in range(1, base_config.blocks_per_zone + 1)}
    assert set(res.vomitories) == keys
    for k in keys:
        assert isinstance(res.vomitories[k], simpy.Resource)
        assert res.vomitories[k].capacity == base_config.vomitory_capacity
    assert set(res.stewards) == set(base_config.zones)
    for z in base_config.zones:
        assert res.stewards[z].capacity == base_config.stewards_per_zone

    tri = base_config.vomitory_pass_s
    assert res.vomitory_pass_s.shape == (base_config.n_spectators,)
    assert res.vomitory_pass_s.min() >= tri.low
    assert res.vomitory_pass_s.max() <= tri.high
    assert res.vomitory_pass_s.mean() == pytest.approx(tri.mean, rel=0.01)


def test_vomitory_times_common_random_numbers() -> None:
    """D18: el tiempo de paso de cada espectador no depende del escenario."""
    a = make_ctx(load_config(overrides={**MINI_OVERRIDES, "turnstiles_per_gate": 2}), seed=7)
    b = make_ctx(load_config(overrides={**MINI_OVERRIDES, "turnstiles_per_gate": 4}), seed=7)
    np.testing.assert_array_equal(a.stadium.vomitory_pass_s, b.stadium.vomitory_pass_s)
    c = make_ctx(load_config(overrides=MINI_OVERRIDES), seed=8)
    assert not np.array_equal(a.stadium.vomitory_pass_s, c.stadium.vomitory_pass_s)


# -- proceso de ubicación -------------------------------------------------------


def test_single_spectator_times(mini_config: Config) -> None:
    ctx = make_ctx(mini_config)
    sp = make_spectator(3, -20.0, speed_mps=1.2, distance_m=90.0)
    run_seating(ctx, [sp])
    walk_min = 90.0 / 1.2 / 60
    pass_min = ctx.stadium.vomitory_pass_s[3] / 60
    assert sp.t_vomitory == pytest.approx(-20.0 + walk_min)
    assert sp.t_seated == pytest.approx(sp.t_vomitory + pass_min)
    assert sp.conflict is False
    assert sp.late is False


def test_vomitory_capacity_respected(mini_config: Config) -> None:
    ctx = make_ctx(mini_config)
    cap = mini_config.vomitory_capacity
    n = 3 * cap + 2
    ctx.stadium.vomitory_pass_s[:n] = 10.0
    sps = [make_spectator(i, -10.0) for i in range(n)]  # llegan todos a la vez
    run_seating(ctx, sps)

    seated = np.array([min_to_s(sp.t_seated) for sp in sps])
    starts = seated - 10.0
    assert max_overlap(starts, seated) == cap
    t0 = min_to_s(sps[0].t_vomitory)
    # Oleadas de `cap` personas cada 10 s, en orden FIFO.
    expected = [t0 + 10.0 * (i // cap + 1) for i in range(n)]
    np.testing.assert_allclose(seated, expected)


def test_vomitories_independent(mini_config: Config) -> None:
    ctx = make_ctx(mini_config)
    cap = mini_config.vomitory_capacity
    sps = [make_spectator(i, -10.0, block=1 + i // cap) for i in range(3 * cap)]
    run_seating(ctx, sps)
    for sp in sps:
        wait_s = min_to_s(sp.t_seated) - min_to_s(sp.t_vomitory)
        assert wait_s == pytest.approx(ctx.stadium.vomitory_pass_s[sp.id])


def test_waits_until_end_of_control(mini_config: Config) -> None:
    """Si se lanza en E0, espera a su ``t_end_control`` antes de caminar."""
    ctx = make_ctx(mini_config)
    sp = make_spectator(0, -30.0, distance_m=60.0, speed_mps=1.0)
    run_seating(ctx, [sp])
    assert sp.t_vomitory == pytest.approx(-29.0)


def test_requires_end_of_control(mini_config: Config) -> None:
    ctx = make_ctx(mini_config)
    sp = make_spectator(0, -30.0)
    sp.t_end_control = math.nan
    ctx.env.process(seating_process(sp, ctx))
    with pytest.raises(AssertionError):
        ctx.env.run()


def test_entry_then_seating_invariants(mini_config: Config) -> None:
    ctx = make_ctx(mini_config, seed=3)
    sps = generate_spectators(mini_config, ctx.rngs)
    ctx.spectators = sps

    def journey(sp: Spectator):
        yield from entry_process(sp, ctx)
        yield from seating_process(sp, ctx)

    for sp in sps:
        ctx.env.process(journey(sp))
    ctx.env.run()

    eps = 1e-9  # min; la conversión s <-> min deja errores de coma flotante
    for sp in sps:
        assert sp.t_arrival - eps <= sp.t_start_control <= sp.t_end_control + eps
        assert sp.t_end_control - eps <= sp.t_vomitory <= sp.t_seated + eps
        walk_min = sp.distance_m / sp.speed_mps / 60
        assert sp.t_vomitory == pytest.approx(sp.t_end_control + walk_min)
        assert sp.late == is_late(sp, ctx)
        assert sp.conflict is False

    seated = np.array([min_to_s(sp.t_seated) for sp in sps])
    starts = seated - ctx.stadium.vomitory_pass_s[[sp.id for sp in sps]]
    for block in range(1, mini_config.blocks_per_zone + 1):
        mask = np.array([sp.block == block for sp in sps])
        if mask.any():
            assert max_overlap(starts[mask], seated[mask]) <= mini_config.vomitory_capacity


def test_seating_deterministic(mini_config: Config) -> None:
    def run(seed: int) -> list[float]:
        ctx = make_ctx(mini_config, seed=seed)
        sps = generate_spectators(mini_config, ctx.rngs)

        def journey(sp: Spectator):
            yield from entry_process(sp, ctx)
            yield from seating_process(sp, ctx)

        for sp in sps:
            ctx.env.process(journey(sp))
        ctx.env.run()
        return [sp.t_seated for sp in sps]

    assert run(5) == run(5)


# -- entrada tardía -------------------------------------------------------------


@pytest.mark.parametrize(
    ("t_arrival", "t_seated", "expected"),
    [
        (-5.0, 2.0, True),  # llega antes, se sienta después del inicio
        (-5.0, -1.0, False),  # llega y se sienta antes
        (-5.0, 0.0, False),  # se sienta justo en el inicio
        (3.0, 5.0, False),  # llega ya empezado: no es «tardío por colas»
        (0.0, 1.0, False),  # llega justo en el inicio
        (-5.0, math.nan, False),  # no se ha sentado
    ],
)
def test_is_late(mini_config: Config, t_arrival: float, t_seated: float, expected: bool) -> None:
    ctx = make_ctx(mini_config)
    sp = make_spectator(0, t_arrival + 1.0, t_arrival=t_arrival)
    sp.t_seated = t_seated
    assert is_late(sp, ctx) is expected

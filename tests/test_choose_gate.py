"""I4 · elección de puerta y redirección ante el cierre (entry.choose_gate, T2.7)."""

from __future__ import annotations

from typing import Any

import pytest
import simpy

from conftest import MINI_OVERRIDES
from sanmames.arrivals import generate_spectators
from sanmames.config import Config, deep_merge, load_config
from sanmames.entities import Spectator, min_to_s
from sanmames.entry import build_entry_resources, choose_gate, entry_process
from sanmames.incidents import gate_closure_process
from sanmames.rng import RngStreams
from sanmames.runner import SimContext

# Cierre dentro de la hora punta (base.json lo pone en +20, fuera de ella).
CLOSE, DURATION = -25.0, 10.0
REOPEN = CLOSE + DURATION


def closure_config(*, redirect: bool, enabled: bool = True, gates: int = 3, **extra: Any) -> Config:
    overrides = deep_merge(
        MINI_OVERRIDES,
        {
            "gates_per_zone": gates,
            "redirect_on_gate_closure": redirect,
            "incidents": {
                "gate_closure": {
                    "enabled": enabled,
                    "zone": "A",
                    "gate": 1,
                    "start_min": CLOSE,
                    "duration_min": DURATION,
                }
            },
        },
    )
    return load_config(overrides=deep_merge(overrides, extra))


def make_ctx(config: Config, seed: int = 1) -> SimContext:
    env = simpy.Environment(initial_time=min_to_s(config.t_open_min))
    ctx = SimContext(env=env, config=config, rngs=RngStreams(seed))
    ctx.entry = build_entry_resources(ctx)
    return ctx


def sp(i: int, t_arrival: float, gate: int = 1, service_s: float = 4.0) -> Spectator:
    return Spectator(i, "A", gate, 1, "lower", "standard", 1.4, 100.0, t_arrival, service_s)


def run(ctx: SimContext, sps: list[Spectator], until_min: float | None = None) -> None:
    ctx.spectators = sps
    ctx.env.process(gate_closure_process(ctx))
    for s in sps:
        ctx.env.process(entry_process(s, ctx))
    ctx.env.run(until=None if until_min is None else min_to_s(until_min))


def occupy(ctx: SimContext, gate: int, n: int) -> None:
    """Pide ``n`` plazas en la puerta ``gate`` (las que no caben quedan en cola)."""
    assert ctx.entry is not None
    res = ctx.entry.turnstiles[("A", gate)]
    for _ in range(n):
        res.request()
    ctx.env.run(until=ctx.env.now + 1)


# -- choose_gate (estado instantáneo) -----------------------------------------


def test_open_gate_is_kept() -> None:
    ctx = make_ctx(closure_config(redirect=True))
    assert choose_gate(sp(0, -30.0, gate=2), ctx) == 2


def test_closed_without_redirect_returns_assigned() -> None:
    ctx = make_ctx(closure_config(redirect=False))
    assert ctx.entry is not None
    ctx.entry.gate_open[("A", 1)] = False
    assert choose_gate(sp(0, -30.0), ctx) == 1


def test_redirect_tie_breaks_by_gate_number() -> None:
    ctx = make_ctx(closure_config(redirect=True))
    assert ctx.entry is not None
    ctx.entry.gate_open[("A", 1)] = False
    assert choose_gate(sp(0, -30.0), ctx) == 2


def test_redirect_prefers_fewer_in_service_when_queues_tie() -> None:
    ctx = make_ctx(closure_config(redirect=True))
    assert ctx.entry is not None
    ctx.entry.gate_open[("A", 1)] = False
    occupy(ctx, gate=2, n=1)  # cola 0, 1 en control
    assert choose_gate(sp(0, -30.0), ctx) == 3


def test_redirect_prefers_shorter_queue_first() -> None:
    c = closure_config(redirect=True).turnstiles_per_gate
    ctx = make_ctx(closure_config(redirect=True))
    assert ctx.entry is not None
    ctx.entry.gate_open[("A", 1)] = False
    occupy(ctx, gate=2, n=c + 1)  # cola 1
    occupy(ctx, gate=3, n=c + 2)  # cola 2
    assert choose_gate(sp(0, -30.0), ctx) == 2


def test_redirect_ignores_other_closed_gates_and_zones() -> None:
    cfg = closure_config(redirect=True, zones=["A", "B"], zone_share=[0.5, 0.5])
    ctx = make_ctx(cfg)
    assert ctx.entry is not None
    ctx.entry.gate_open[("A", 1)] = False
    ctx.entry.gate_open[("A", 2)] = False
    assert choose_gate(sp(0, -30.0), ctx) == 3  # ni la cerrada A-G2 ni la zona B


# -- entry_process con cierre -------------------------------------------------


def test_redirect_during_closure_and_nobody_new_uses_closed_gate() -> None:
    ctx = make_ctx(closure_config(redirect=True))
    sps = [sp(i, CLOSE - 2.25 + 0.5 * i) for i in range(30)]  # G1; ninguno justo en el límite
    run(ctx, sps)
    for s in sps:
        if CLOSE <= s.t_arrival < REOPEN:
            assert s.gate_used in (2, 3)
        else:
            assert s.gate_used == 1


def test_without_redirect_wait_and_keep_arrival_order() -> None:
    ctx = make_ctx(closure_config(redirect=False))
    t = CLOSE + 3.0
    sps = [sp(i, t) for i in range(5)] + [sp(5, t + 1.0), sp(6, t + 2.0)]
    run(ctx, sps)
    starts = [s.t_start_control for s in sps]
    assert all(s.gate_used == 1 for s in sps)
    assert min(starts) == pytest.approx(REOPEN)
    assert starts == sorted(starts)
    c = ctx.config.turnstiles_per_gate
    assert starts[:c] == pytest.approx([REOPEN] * c)


def test_before_closure_unaffected_and_after_reopen_use_own_gate() -> None:
    def times(enabled: bool) -> list[Spectator]:
        ctx = make_ctx(closure_config(redirect=True, enabled=enabled))
        cfg = ctx.config
        sps = generate_spectators(cfg, ctx.rngs)
        run(ctx, sps)
        return sps

    with_closure, without = times(True), times(False)
    for a, b in zip(with_closure, without, strict=True):
        if a.t_arrival < CLOSE:
            assert (a.gate_used, a.t_start_control, a.t_end_control) == (
                b.gate_used,
                b.t_start_control,
                b.t_end_control,
            )
        if a.t_arrival >= REOPEN:
            assert a.gate_used == a.gate


def test_single_gate_zone_with_redirect_waits() -> None:
    ctx = make_ctx(closure_config(redirect=True, gates=1))
    s = sp(0, CLOSE + 1.0)
    run(ctx, [s])
    assert s.gate_used == 1
    assert s.t_start_control == pytest.approx(REOPEN)


def test_wait_reads_reopen_event_each_time() -> None:
    """Un disparo con la puerta aún cerrada no deja pasar; se espera al evento nuevo."""
    ctx = make_ctx(closure_config(redirect=False, enabled=False))
    assert ctx.entry is not None
    entry, env, key = ctx.entry, ctx.env, ("A", 1)
    entry.gate_open[key] = False
    s = sp(0, -60.0)
    ctx.spectators = [s]
    env.process(entry_process(s, ctx))

    def reopen(at_min: float, really: bool) -> Any:
        yield env.timeout(min_to_s(at_min) - env.now)
        if really:
            entry.gate_open[key] = True
        old = entry.reopen_event[key]
        entry.reopen_event[key] = env.event()
        old.succeed()

    def driver() -> Any:
        yield env.process(reopen(-50.0, really=False))  # disparo espurio
        yield env.process(reopen(-40.0, really=True))

    env.process(driver())
    env.run()
    assert s.t_start_control == pytest.approx(-40.0)


@pytest.mark.parametrize("redirect", [False, True])
def test_disabled_closure_is_regression_free(redirect: bool) -> None:
    def outcome(cfg: Config) -> list[tuple[int, float, float]]:
        ctx = make_ctx(cfg)
        sps = generate_spectators(cfg, ctx.rngs)
        run(ctx, sps)
        return [(s.gate_used, s.t_start_control, s.t_end_control) for s in sps]

    cfg = closure_config(redirect=redirect, enabled=False)
    plain = load_config(overrides=deep_merge(MINI_OVERRIDES, {"gates_per_zone": 3}))
    got = outcome(cfg)
    assert got == outcome(plain)
    assigned = [s.gate for s in generate_spectators(cfg, RngStreams(1))]
    assert [g for g, _, _ in got] == assigned


def test_x6_redirect_lowers_max_wait_at_closed_gate() -> None:
    """Macrozona realista saturada en punta (6 puertas, 2 tornos, N/4), misma semilla.

    Con 2 tornos una puerta atiende ~30 pers/min y en punta le llegan ~38. La
    redirección reparte la cola de la puerta cerrada y empeora algo las demás.
    """

    def waits(redirect: bool) -> tuple[float, float]:
        cfg = closure_config(redirect=redirect, gates=6, turnstiles_per_gate=2, n_spectators=12194)
        ctx = make_ctx(cfg, seed=11)
        sps = generate_spectators(cfg, ctx.rngs)
        run(ctx, sps)
        closed = max(s.t_start_control - s.t_arrival for s in sps if s.gate == 1)
        others = max(s.t_start_control - s.t_arrival for s in sps if s.gate != 1)
        return closed, others

    (sin_g1, sin_rest), (con_g1, con_rest) = waits(False), waits(True)
    assert sin_g1 > DURATION
    assert con_g1 < sin_g1
    assert con_rest >= sin_rest

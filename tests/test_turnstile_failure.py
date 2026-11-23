"""I3 · avería de torno (entry.py, T2.3)."""

from __future__ import annotations

import math
from typing import Any

import pytest
import simpy

from conftest import MINI_OVERRIDES
from sanmames.config import Config, deep_merge, load_config
from sanmames.entities import Incident, Spectator, min_to_s
from sanmames.entry import (
    PRIORITY_FAILURE,
    PRIORITY_HIGH,
    build_entry_resources,
    entry_process,
    start_turnstile_failure_processes,
    turnstile_failure_process,
)
from sanmames.rng import RngStreams
from sanmames.runner import SimContext

SEED = 7
REPAIR = 5.0  # min, reparación fija (low == high) para comprobar duraciones exactas


def failure_config(
    *,
    enabled: bool = True,
    mtbf: float = 30.0,
    repair: tuple[float, float] = (REPAIR, REPAIR),
    **extra: Any,
) -> Config:
    overrides = deep_merge(
        MINI_OVERRIDES,
        {
            "gates_per_zone": 1,
            "turnstiles_per_gate": 1,
            "incidents": {
                "turnstile_failure": {
                    "enabled": enabled,
                    "mtbf_min": mtbf,
                    "repair_min": {"low": repair[0], "high": repair[1]},
                }
            },
        },
    )
    return load_config(overrides=deep_merge(overrides, extra))


def make_ctx(config: Config, seed: int = SEED) -> SimContext:
    env = simpy.Environment(initial_time=min_to_s(config.t_open_min))
    ctx = SimContext(env=env, config=config, rngs=RngStreams(seed))
    ctx.entry = build_entry_resources(ctx)
    return ctx


def spectator(i: int, t_arrival: float, service_s: float, group: str = "standard") -> Spectator:
    return Spectator(i, "A", 1, 1, "lower", group, 1.4, 100.0, t_arrival, service_s)


def first_failure_min(config: Config, zone: str = "A", gate: int = 1, k: int = 1) -> float:
    """Instante (min) en que se avería el torno si está libre: apertura + 1.er Exp."""
    rng = RngStreams(SEED).substream("turnstile_failure", zone, gate, k)
    return config.t_open_min + rng.exponential(config.incidents.turnstile_failure.mtbf_min)


def run_until_min(ctx: SimContext, t_min: float) -> None:
    ctx.env.run(until=min_to_s(t_min))


def i3(ctx: SimContext) -> list[Incident]:
    return [inc for inc in ctx.incidents if inc.kind == "I3"]


def calendar(ctx: SimContext, resource: str) -> list[tuple[float, float]]:
    return [(inc.t_start, inc.t_end) for inc in i3(ctx) if inc.resource == resource]


# -- activación ---------------------------------------------------------------


def test_disabled_creates_nothing() -> None:
    cfg = failure_config(enabled=False, mtbf=0.5)
    ctx = make_ctx(cfg)
    assert start_turnstile_failure_processes(ctx) == []
    proc = ctx.env.process(turnstile_failure_process("A", 1, ctx))
    run_until_min(ctx, cfg.t_open_min + 60)
    assert not proc.is_alive
    assert ctx.incidents == []
    assert ctx.entry is not None and ctx.entry.failed_turnstiles[("A", 1)] == 0


def test_one_process_per_gate_in_fixed_order() -> None:
    cfg = failure_config(zones=["A", "B"], zone_share=[0.5, 0.5], gates_per_zone=3)
    ctx = make_ctx(cfg)
    procs = start_turnstile_failure_processes(ctx)
    assert len(procs) == cfg.n_gates
    assert all(p.is_alive for p in procs)


# -- duración, estado y registro ----------------------------------------------


def test_failure_lasts_exactly_repair_and_restores_state() -> None:
    cfg = failure_config(mtbf=30.0)
    ctx = make_ctx(cfg)
    assert ctx.entry is not None
    start_turnstile_failure_processes(ctx)
    t_fail = first_failure_min(cfg)

    run_until_min(ctx, t_fail + REPAIR / 2)
    assert ctx.entry.failed_turnstiles[("A", 1)] == 1
    assert ctx.entry.turnstiles[("A", 1)].count == 1
    (inc,) = i3(ctx)
    assert inc.t_start == pytest.approx(t_fail, abs=1e-9)
    assert math.isnan(inc.t_end)

    run_until_min(ctx, t_fail + REPAIR + 1e-3)
    assert ctx.entry.failed_turnstiles[("A", 1)] == 0
    assert ctx.entry.turnstiles[("A", 1)].count == 0
    assert inc.t_end - inc.t_start == pytest.approx(REPAIR, abs=1e-9)


def test_incidents_are_logged_complete() -> None:
    cfg = failure_config(mtbf=5.0, gates_per_zone=2, turnstiles_per_gate=2)
    ctx = make_ctx(cfg)
    start_turnstile_failure_processes(ctx)
    run_until_min(ctx, cfg.t_open_min + 300)
    incs = i3(ctx)
    assert len(incs) > 10
    labels = {f"A-G{g}-T{k}" for g in (1, 2) for k in (1, 2)}
    assert {inc.resource for inc in incs} == labels
    for inc in incs:
        assert inc.zone == "A"
        assert inc.spectator_id == -1
        if not math.isnan(inc.t_end):  # la última de cada torno puede seguir abierta
            assert inc.t_start < inc.t_end


# -- interacción con la cola --------------------------------------------------


def test_failure_does_not_interrupt_service_in_progress() -> None:
    cfg = failure_config(mtbf=30.0)
    ctx = make_ctx(cfg)
    t_fail = first_failure_min(cfg)
    sp = spectator(0, t_arrival=t_fail - 1.0, service_s=300.0)  # sigue en servicio en t_fail
    ctx.spectators = [sp]
    ctx.env.process(entry_process(sp, ctx))
    start_turnstile_failure_processes(ctx)
    run_until_min(ctx, t_fail + 30)

    assert sp.t_end_control - sp.t_start_control == pytest.approx(5.0)
    inc = i3(ctx)[0]
    assert inc.t_start == pytest.approx(sp.t_end_control, abs=1e-9)
    assert inc.t_end - inc.t_start == pytest.approx(REPAIR, abs=1e-9)


def test_failure_jumps_queue_including_priority_groups() -> None:
    cfg = failure_config(mtbf=30.0, queue_discipline="priority", priority_groups=["elderly"])
    assert "elderly" in cfg.priority_groups
    ctx = make_ctx(cfg)
    t_fail = first_failure_min(cfg)
    busy = spectator(0, t_arrival=t_fail - 1.0, service_s=300.0)
    normal = spectator(1, t_arrival=t_fail - 0.9, service_s=4.0)
    high = spectator(2, t_arrival=t_fail - 0.8, service_s=4.0, group="elderly")
    ctx.spectators = [busy, normal, high]
    for sp in ctx.spectators:
        ctx.env.process(entry_process(sp, ctx))
    start_turnstile_failure_processes(ctx)
    run_until_min(ctx, t_fail + 30)

    assert PRIORITY_FAILURE < PRIORITY_HIGH
    inc = i3(ctx)[0]
    # La avería se pide en t_fail, después que los dos que esperan, y entra antes.
    assert inc.t_start == pytest.approx(busy.t_end_control, abs=1e-9)
    assert high.t_start_control == pytest.approx(inc.t_end, abs=1e-9)
    assert normal.t_start_control == pytest.approx(high.t_end_control, abs=1e-9)


def test_capacity_and_gate_keeps_serving_with_failures() -> None:
    c = 3
    cfg = failure_config(mtbf=3.0, turnstiles_per_gate=c)
    ctx = make_ctx(cfg)
    assert ctx.entry is not None
    res = ctx.entry.turnstiles[("A", 1)]
    sps = [spectator(i, t_arrival=cfg.t_open_min + i * 0.05, service_s=4.0) for i in range(600)]
    ctx.spectators = sps
    for sp in sps:
        ctx.env.process(entry_process(sp, ctx))
    start_turnstile_failure_processes(ctx)

    samples: list[tuple[int, int]] = []

    def probe() -> Any:
        while True:
            samples.append((ctx.entry.failed_turnstiles[("A", 1)], res.count))
            yield ctx.env.timeout(1.0)

    ctx.env.process(probe())
    run_until_min(ctx, cfg.t_open_min + 120)

    assert all(0 <= failed <= busy <= c for failed, busy in samples)
    # Con c - 1 tornos averiados, el que queda sigue atendiendo.
    assert any(failed == c - 1 and busy == c for failed, busy in samples)
    assert all(not math.isnan(sp.t_end_control) for sp in sps)


def test_failure_count_matches_rate() -> None:
    """Sin público: cada torno alterna Exp(mtbf) en marcha y la reparación."""
    mtbf, repair = 10.0, (0.5, 1.5)
    gates, c, horizon = 2, 3, 6000.0
    cfg = failure_config(mtbf=mtbf, repair=repair, gates_per_zone=gates, turnstiles_per_gate=c)
    ctx = make_ctx(cfg)
    start_turnstile_failure_processes(ctx)
    run_until_min(ctx, cfg.t_open_min + horizon)
    expected = gates * c * horizon / (mtbf + sum(repair) / 2)
    assert len(i3(ctx)) == pytest.approx(expected, rel=0.05)


# -- números aleatorios comunes (D22) -------------------------------------------


def test_reproducible_and_seed_dependent() -> None:
    cfg = failure_config(mtbf=5.0, repair=(3.0, 10.0), turnstiles_per_gate=3)

    def run(seed: int) -> list[tuple[str, float, float]]:
        ctx = make_ctx(cfg, seed)
        start_turnstile_failure_processes(ctx)
        run_until_min(ctx, cfg.t_open_min + 600)
        return [(i.resource, i.t_start, i.t_end) for i in i3(ctx)]

    assert run(1) == run(1)
    assert run(1) != run(2)


@pytest.mark.parametrize("other", [{"turnstiles_per_gate": 4}, {"gates_per_zone": 3}])
def test_calendar_same_regardless_of_number_of_turnstiles(other: dict[str, int]) -> None:
    """El calendario de A-G1-T1 y A-G1-T2 no cambia al añadir tornos o puertas."""
    base = failure_config(mtbf=5.0, repair=(3.0, 10.0), turnstiles_per_gate=2)
    more = failure_config(mtbf=5.0, repair=(3.0, 10.0), **{"turnstiles_per_gate": 2, **other})

    def run(cfg: Config) -> SimContext:
        ctx = make_ctx(cfg)
        start_turnstile_failure_processes(ctx)
        run_until_min(ctx, cfg.t_open_min + 600)
        return ctx

    ctx_base, ctx_more = run(base), run(more)
    for label in ("A-G1-T1", "A-G1-T2"):
        assert calendar(ctx_base, label)
        assert calendar(ctx_base, label) == calendar(ctx_more, label)


def test_calendar_independent_of_other_zones() -> None:
    one = failure_config(mtbf=5.0)
    two = failure_config(mtbf=5.0, zones=["B", "A"], zone_share=[0.5, 0.5])

    def run(cfg: Config) -> SimContext:
        ctx = make_ctx(cfg)
        start_turnstile_failure_processes(ctx)
        run_until_min(ctx, cfg.t_open_min + 600)
        return ctx

    assert calendar(run(one), "A-G1-T1") == calendar(run(two), "A-G1-T1")

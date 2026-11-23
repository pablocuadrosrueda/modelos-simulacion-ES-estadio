"""Fase de entrada sin incidencias (entry.py, T1.2)."""

from __future__ import annotations

import math

import numpy as np
import pytest
import simpy

from conftest import MINI_OVERRIDES
from sanmames.arrivals import generate_spectators
from sanmames.config import Config, load_config
from sanmames.entities import Spectator, min_to_s
from sanmames.entry import (
    PRIORITY_HIGH,
    PRIORITY_NORMAL,
    build_entry_resources,
    entry_process,
    priority_of,
)
from sanmames.rng import RngStreams
from sanmames.runner import SimContext


def make_ctx(config: Config, seed: int = 1) -> SimContext:
    env = simpy.Environment(initial_time=min_to_s(config.t_open_min))
    ctx = SimContext(env=env, config=config, rngs=RngStreams(seed))
    ctx.entry = build_entry_resources(ctx)
    return ctx


def make_spectator(
    i: int,
    t_arrival: float,
    zone: str = "A",
    gate: int = 1,
    service_s: float = 4.0,
    group: str = "standard",
) -> Spectator:
    return Spectator(i, zone, gate, 1, "lower", group, 1.4, 100.0, t_arrival, service_s)


def run_entry(ctx: SimContext, sps: list[Spectator]) -> None:
    ctx.spectators = sps
    for sp in sps:
        ctx.env.process(entry_process(sp, ctx))
    ctx.env.run()


# -- recursos y prioridad ---------------------------------------------------


def test_build_entry_resources(base_config: Config) -> None:
    ctx = make_ctx(base_config)
    res = ctx.entry
    assert res is not None
    keys = {(z, g) for z in base_config.zones for g in range(1, base_config.gates_per_zone + 1)}
    assert set(res.turnstiles) == keys
    assert set(res.gate_open) == set(res.reopen_event) == set(res.failed_turnstiles) == keys
    assert len(keys) == base_config.n_gates
    for k in keys:
        assert isinstance(res.turnstiles[k], simpy.PriorityResource)
        assert res.turnstiles[k].capacity == base_config.turnstiles_per_gate
        assert res.gate_open[k] is True
        assert not res.reopen_event[k].triggered
        assert res.failed_turnstiles[k] == 0


def test_priority_fifo(mini_config: Config) -> None:
    ctx = make_ctx(mini_config)
    for group in mini_config.groups:
        sp = make_spectator(0, -10.0)
        sp.group = group
        assert priority_of(sp, ctx) == PRIORITY_NORMAL


# -- proceso de entrada -----------------------------------------------------


def test_single_spectator_no_wait(mini_config: Config) -> None:
    ctx = make_ctx(mini_config)
    sp = make_spectator(0, -30.0, gate=2)
    run_entry(ctx, [sp])
    assert sp.gate_used == 2
    assert sp.t_start_control == pytest.approx(-30.0)
    assert sp.t_end_control - sp.t_start_control == pytest.approx(sp.service_s / 60)
    assert sp.read_failure is False


@pytest.mark.parametrize("t_arrival", [-89.8356, -89.6164, -89.3972])
def test_no_wait_start_equals_arrival_exactly(mini_config: Config, t_arrival: float) -> None:
    """Sin cola, t_start_control == t_arrival exacto (redondeo s <-> min, aviso de B)."""
    ctx = make_ctx(mini_config)
    sp = make_spectator(0, t_arrival)
    run_entry(ctx, [sp])
    assert sp.t_start_control == sp.t_arrival
    assert sp.t_start_control - sp.t_arrival == 0.0


def test_late_launch_starts_at_launch_time(mini_config: Config) -> None:
    """Lanzado después de su llegada, empieza al lanzarse (no se reescribe a t_arrival)."""
    ctx = make_ctx(mini_config)
    sp = make_spectator(0, -80.0)
    ctx.spectators = [sp]
    ctx.env.run(until=min_to_s(-70.0))
    ctx.env.process(entry_process(sp, ctx))
    ctx.env.run()
    assert sp.t_start_control == pytest.approx(-70.0)


def test_fifo_order_one_gate(mini_config: Config) -> None:
    """Llegadas escalonadas a una puerta saturada: se atienden por orden de llegada."""
    ctx = make_ctx(mini_config)
    c = mini_config.turnstiles_per_gate
    # 60 personas en 1 min (1/s) frente a c tornos de ~4 s: se forma cola.
    sps = [make_spectator(i, -20.0 + i / 60, service_s=3.0 + i % 3) for i in range(60)]
    run_entry(ctx, list(reversed(sps)))  # el orden de lanzamiento no importa
    starts = [sp.t_start_control for sp in sps]
    assert starts == sorted(starts)
    assert max(sp.t_start_control - sp.t_arrival for sp in sps) > 0  # hubo espera
    # Con c tornos, el i-ésimo empieza en cuanto acaba alguno de los c anteriores.
    for i in range(c, len(sps)):
        prev_ends = sorted(s.t_end_control for s in sps[:i])
        assert sps[i].t_start_control == pytest.approx(
            max(sps[i].t_arrival, prev_ends[i - c]), abs=1e-9
        )


def test_fifo_simultaneous_arrivals_keep_launch_order() -> None:
    cfg = load_config(overrides=MINI_OVERRIDES)
    ctx = make_ctx(cfg)
    sps = [make_spectator(i, -10.0) for i in range(10)]
    run_entry(ctx, sps)
    c = cfg.turnstiles_per_gate
    for i, sp in enumerate(sps):
        assert sp.t_start_control == pytest.approx(-10.0 + (i // c) * 4 / 60)


def test_turnstile_capacity_respected(mini_config: Config) -> None:
    ctx = make_ctx(mini_config)
    sps = generate_spectators(mini_config, ctx.rngs)
    run_entry(ctx, sps)
    c = mini_config.turnstiles_per_gate
    for gate in range(1, mini_config.gates_per_zone + 1):
        at_gate = [s for s in sps if s.gate_used == gate]
        events = sorted(
            [(s.t_start_control, 1) for s in at_gate] + [(s.t_end_control, -1) for s in at_gate],
            key=lambda e: (e[0], e[1]),  # a igual instante, primero las salidas
        )
        busy = peak = 0
        for _, d in events:
            busy += d
            peak = max(peak, busy)
        assert peak <= c
        assert ctx.entry is not None and ctx.entry.turnstiles[("A", gate)].count == 0


def test_capacity_exact_c_start_immediately() -> None:
    cfg = load_config(overrides=MINI_OVERRIDES)
    ctx = make_ctx(cfg)
    c = cfg.turnstiles_per_gate
    sps = [make_spectator(i, -5.0) for i in range(c + 1)]
    run_entry(ctx, sps)
    assert all(sp.t_start_control == pytest.approx(-5.0) for sp in sps[:c])
    assert sps[c].t_start_control == pytest.approx(-5.0 + 4 / 60)


def test_gates_are_independent() -> None:
    cfg = load_config(overrides=MINI_OVERRIDES)
    ctx = make_ctx(cfg)
    c = cfg.turnstiles_per_gate
    g1 = [make_spectator(i, -5.0, gate=1) for i in range(c)]
    g2 = [make_spectator(c + i, -5.0, gate=2) for i in range(c)]
    run_entry(ctx, g1 + g2)
    assert all(sp.t_start_control == pytest.approx(-5.0) for sp in g1 + g2)


def test_full_mini_entry_times_ordered(mini_config: Config) -> None:
    ctx = make_ctx(mini_config, seed=7)
    sps = generate_spectators(mini_config, ctx.rngs)
    run_entry(ctx, sps)
    for sp in sps:
        assert sp.gate_used == sp.gate
        assert not math.isnan(sp.t_end_control)
        assert sp.t_arrival <= sp.t_start_control + 1e-9 <= sp.t_end_control + 2e-9


def test_entry_deterministic(mini_config: Config) -> None:
    def run(seed: int) -> list[float]:
        ctx = make_ctx(mini_config, seed=seed)
        sps = generate_spectators(mini_config, ctx.rngs)
        run_entry(ctx, sps)
        return [sp.t_end_control for sp in sps]

    assert run(5) == run(5)
    assert run(5) != run(6)


# -- prioridad no expulsiva (X3, T2.4) -------------------------------------

PRIORITY_OVERRIDES = {
    **MINI_OVERRIDES,
    "queue_discipline": "priority",
    "priority_groups": ["elderly", "reduced_mobility"],
}


def priority_config(**extra: object) -> Config:
    return load_config(overrides={**PRIORITY_OVERRIDES, **extra})


def test_priority_of_by_group() -> None:
    ctx = make_ctx(priority_config())
    for group, expected in [
        ("standard", PRIORITY_NORMAL),
        ("elderly", PRIORITY_HIGH),
        ("reduced_mobility", PRIORITY_HIGH),
    ]:
        assert priority_of(make_spectator(0, -1.0, group=group), ctx) == expected


def test_priority_groups_ignored_under_fifo() -> None:
    cfg = load_config(overrides={**MINI_OVERRIDES, "priority_groups": ["elderly"]})
    ctx = make_ctx(cfg)  # queue_discipline sigue siendo "fifo"
    assert priority_of(make_spectator(0, -1.0, group="elderly"), ctx) == PRIORITY_NORMAL


def test_priority_with_no_groups_is_fifo() -> None:
    ctx = make_ctx(priority_config(priority_groups=[]))
    assert priority_of(make_spectator(0, -1.0, group="elderly"), ctx) == PRIORITY_NORMAL


def _queue_scenario(cfg: Config) -> dict[str, Spectator]:
    """3 tornos ocupados (4 s) y cola: 4 normales a 1 s, 2 mayores a 2 s y 3 s."""
    ctx = make_ctx(cfg)
    t0 = -10.0
    s = 1 / 60  # 1 s en minutos
    sps = {
        **{f"busy{i}": make_spectator(i, t0) for i in range(3)},
        **{f"n{i}": make_spectator(3 + i, t0 + s) for i in range(4)},
        "e1": make_spectator(7, t0 + 2 * s, group="elderly"),
        "e2": make_spectator(8, t0 + 3 * s, group="elderly"),
    }
    run_entry(ctx, list(sps.values()))
    return sps


def test_priority_jumps_the_queue_but_never_preempts() -> None:
    sps = _queue_scenario(priority_config())
    t0, s = -10.0, 1 / 60
    # No expulsiva: los 3 controles en curso terminan a los 4 s, sin interrumpirse.
    for k in ("busy0", "busy1", "busy2"):
        assert sps[k].t_start_control == pytest.approx(t0)
        assert sps[k].t_end_control == pytest.approx(t0 + 4 * s)
    # A los 4 s quedan 3 tornos libres: los dos mayores (en su orden de llegada) y
    # el primer normal de la cola. Los otros 3 normales esperan al siguiente hueco.
    assert sps["e1"].t_start_control == pytest.approx(t0 + 4 * s)
    assert sps["e2"].t_start_control == pytest.approx(t0 + 4 * s)
    assert sps["n0"].t_start_control == pytest.approx(t0 + 4 * s)
    for k in ("n1", "n2", "n3"):
        assert sps[k].t_start_control == pytest.approx(t0 + 8 * s)


def test_priority_keeps_fifo_within_each_level() -> None:
    sps = _queue_scenario(priority_config(turnstiles_per_gate=1))
    # Un solo torno: tras el control en curso (busy0), los mayores adelantan a todos los
    # normales que esperan, y dentro de cada nivel se respeta el orden de llegada.
    order = sorted(sps, key=lambda k: sps[k].t_start_control)
    assert order == ["busy0", "e1", "e2", "busy1", "busy2", "n0", "n1", "n2", "n3"]


def test_same_scenario_under_fifo_serves_elderly_last() -> None:
    sps = _queue_scenario(load_config(overrides=MINI_OVERRIDES))
    t0, s = -10.0, 1 / 60
    # FIFO: a los 4 s entran n0, n1, n2; a los 8 s, n3, e1 y e2.
    assert sps["e1"].t_start_control == pytest.approx(t0 + 8 * s)
    assert sps["e2"].t_start_control == pytest.approx(t0 + 8 * s)


def test_priority_helps_priority_groups_and_hurts_the_rest() -> None:
    """Misma semilla (números aleatorios comunes), 1 torno por puerta para saturar."""

    def mean_waits(cfg: Config) -> tuple[float, float]:
        ctx = make_ctx(cfg, seed=3)
        sps = generate_spectators(cfg, ctx.rngs)
        run_entry(ctx, sps)
        pri = [sp.t_start_control - sp.t_arrival for sp in sps if sp.group != "standard"]
        rest = [sp.t_start_control - sp.t_arrival for sp in sps if sp.group == "standard"]
        assert pri and rest
        return float(np.mean(pri)), float(np.mean(rest))

    base = {**MINI_OVERRIDES, "turnstiles_per_gate": 1, "n_spectators": 1200}
    fifo_pri, fifo_rest = mean_waits(load_config(overrides=base))
    prio_pri, prio_rest = mean_waits(
        load_config(
            overrides={
                **base,
                "queue_discipline": "priority",
                "priority_groups": ["elderly", "reduced_mobility"],
            }
        )
    )
    assert fifo_rest > 0  # había cola
    assert prio_pri < fifo_pri
    assert prio_rest >= fifo_rest

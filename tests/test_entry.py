"""Fase de entrada sin incidencias (entry.py, T1.2)."""

from __future__ import annotations

import math

import pytest
import simpy

from conftest import MINI_OVERRIDES
from sanmames.arrivals import generate_spectators
from sanmames.config import Config, load_config
from sanmames.entities import Spectator, min_to_s
from sanmames.entry import (
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
    i: int, t_arrival: float, zone: str = "A", gate: int = 1, service_s: float = 4.0
) -> Spectator:
    return Spectator(i, zone, gate, 1, "lower", "standard", 1.4, 100.0, t_arrival, service_s)


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


def test_priority_discipline_pending() -> None:
    cfg = load_config(
        overrides={**MINI_OVERRIDES, "queue_discipline": "priority", "priority_groups": ["elderly"]}
    )
    with pytest.raises(NotImplementedError, match="T2.4"):
        priority_of(make_spectator(0, -1.0), make_ctx(cfg))


def test_service_time_belongs_to_spectator() -> None:
    """D17: el servicio lo fija el espectador, no el orden en que lo atienden los tornos."""

    def run(turnstiles: int) -> list[Spectator]:
        cfg = load_config(overrides={**MINI_OVERRIDES, "turnstiles_per_gate": turnstiles})
        ctx = make_ctx(cfg, seed=11)
        sps = generate_spectators(cfg, ctx.rngs)
        run_entry(ctx, sps)
        return sps

    few, many = run(2), run(4)
    assert [s.service_s for s in few] == [s.service_s for s in many]
    for s in few + many:
        assert s.t_end_control - s.t_start_control == pytest.approx(s.service_s / 60)
    # con menos tornos la espera total es mayor: los escenarios sí difieren
    assert sum(s.t_start_control - s.t_arrival for s in few) > sum(
        s.t_start_control - s.t_arrival for s in many
    )

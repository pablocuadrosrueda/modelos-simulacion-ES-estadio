"""Incidencias de B: registro (log_incident) e I4 cierre de puerta (incidents.py, T2.6)."""

from __future__ import annotations

import math

import pytest
import simpy

from conftest import MINI_OVERRIDES
from sanmames.config import Config, deep_merge, load_config
from sanmames.entities import Incident, min_to_s, s_to_min
from sanmames.entry import build_entry_resources
from sanmames.incidents import gate_closure_process, log_incident
from sanmames.rng import RngStreams
from sanmames.runner import SimContext


def closure_config(**gate_closure) -> Config:
    params = {"enabled": True, "zone": "A", "gate": 1, "start_min": 20, "duration_min": 10}
    params.update(gate_closure)
    return load_config(
        overrides=deep_merge(MINI_OVERRIDES, {"incidents": {"gate_closure": params}})
    )


def make_ctx(config: Config) -> SimContext:
    env = simpy.Environment(initial_time=min_to_s(config.t_open_min))
    ctx = SimContext(env=env, config=config, rngs=RngStreams(1))
    ctx.entry = build_entry_resources(ctx)
    return ctx


def watch_gate(ctx: SimContext, key: tuple[str, int], times_min: list[float]):
    """Proceso auxiliar: anota (t, gate_open) en los instantes dados."""
    log = []

    def proc():
        for t in times_min:
            yield ctx.env.timeout(min_to_s(t) - ctx.env.now)
            log.append((t, ctx.entry.gate_open[key]))

    ctx.env.process(proc())
    return log


# -- log_incident ---------------------------------------------------------------


def test_log_incident_appends_and_returns(mini_config: Config) -> None:
    ctx = make_ctx(mini_config)
    inc = Incident("I1", "A", "A-B3", -10.0, spectator_id=7)
    assert log_incident(ctx, inc) is inc
    assert ctx.incidents == [inc]
    inc.t_end = -7.0  # se puede cerrar después
    assert ctx.incidents[0].t_end == -7.0


# -- I4 cierre de puerta -------------------------------------------------------


def test_disabled_does_nothing(mini_config: Config) -> None:
    assert mini_config.incidents.gate_closure.enabled is False
    ctx = make_ctx(mini_config)
    ctx.env.process(gate_closure_process(ctx))
    ctx.env.run()
    assert ctx.env.now == min_to_s(mini_config.t_open_min)
    assert all(ctx.entry.gate_open.values())
    assert ctx.incidents == []


def test_closes_and_reopens_on_time() -> None:
    cfg = closure_config(zone="A", gate=2, start_min=20, duration_min=10)
    ctx = make_ctx(cfg)
    key = ("A", 2)
    log = watch_gate(ctx, key, [19.9, 20.1, 29.9, 30.1])
    ctx.env.process(gate_closure_process(ctx))
    ctx.env.run()

    assert log == [(19.9, True), (20.1, False), (29.9, False), (30.1, True)]
    assert ctx.entry.gate_open[("A", 1)] is True  # las demás puertas no cambian

    assert len(ctx.incidents) == 1
    inc = ctx.incidents[0]
    assert (inc.kind, inc.zone, inc.resource, inc.spectator_id) == ("I4", "A", "A-G2", -1)
    assert inc.t_start == pytest.approx(20.0)
    assert inc.t_end == pytest.approx(30.0)


def test_incident_open_while_closed() -> None:
    ctx = make_ctx(closure_config(start_min=20, duration_min=10))
    ctx.env.process(gate_closure_process(ctx))
    ctx.env.run(until=min_to_s(25))
    assert len(ctx.incidents) == 1
    assert math.isnan(ctx.incidents[0].t_end)
    assert ctx.entry.gate_open[("A", 1)] is False


def test_reopen_event_fires_and_is_replaced() -> None:
    ctx = make_ctx(closure_config(start_min=20, duration_min=10))
    key = ("A", 1)
    old = ctx.entry.reopen_event[key]
    ctx.env.process(gate_closure_process(ctx))
    ctx.env.run()
    assert old.triggered
    new = ctx.entry.reopen_event[key]
    assert new is not old
    assert not new.triggered


def test_waiters_resume_at_reopening_in_order() -> None:
    """D13: quien espera la reapertura se reanuda al reabrir y en orden de llegada."""
    ctx = make_ctx(closure_config(start_min=20, duration_min=10))
    key = ("A", 1)
    resumed: list[tuple[int, float]] = []

    def waiter(i: int, t_min: float):
        yield ctx.env.timeout(min_to_s(t_min) - ctx.env.now)
        if not ctx.entry.gate_open[key]:
            yield ctx.entry.reopen_event[key]
        resumed.append((i, s_to_min(ctx.env.now)))

    ctx.env.process(gate_closure_process(ctx))
    for i, t in enumerate([21.0, 22.5, 22.5, 29.0]):
        ctx.env.process(waiter(i, t))
    ctx.env.run()

    assert [i for i, _ in resumed] == [0, 1, 2, 3]
    assert all(t == pytest.approx(30.0) for _, t in resumed)


def test_zero_duration_closure() -> None:
    ctx = make_ctx(closure_config(start_min=0, duration_min=0))
    ctx.env.process(gate_closure_process(ctx))
    ctx.env.run()
    assert ctx.entry.gate_open[("A", 1)] is True
    inc = ctx.incidents[0]
    assert inc.t_start == inc.t_end == pytest.approx(0.0)


def test_start_in_the_past_raises() -> None:
    ctx = make_ctx(closure_config(start_min=20))
    ctx.env.run(until=min_to_s(25))
    ctx.env.process(gate_closure_process(ctx))
    with pytest.raises(ValueError, match="start_min"):
        ctx.env.run()

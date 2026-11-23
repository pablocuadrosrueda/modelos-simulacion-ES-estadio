"""Evacuación de emergencia (emergency.py, T4.1) y salida bloqueada (T4.2)."""

from __future__ import annotations

import math

import numpy as np
import pytest
import simpy

from conftest import MINI_OVERRIDES
from sanmames.arrivals import generate_spectators
from sanmames.config import Config, deep_merge, load_config
from sanmames.emergency import (
    ALREADY_OUT,
    BLOCKED_EXIT_ID,
    INSIDE,
    NOT_ARRIVED,
    OUTSIDE_QUEUE,
    alarm_process,
    evacuation_process,
    status_at_alarm,
)
from sanmames.entities import Incident, Spectator, min_to_s
from sanmames.entry import build_entry_resources, entry_process
from sanmames.exit import build_exit_resources, exit_pass_time_s, exit_process
from sanmames.incidents import log_incident
from sanmames.rng import RngStreams
from sanmames.runner import SimContext
from sanmames.stadium import build_stadium_resources, seating_process


def emergency_config(top: dict | None = None, **emergency) -> Config:
    """Mini escenario con emergencia; ``top`` son claves de primer nivel."""
    params = {"enabled": True, "alarm_min": 40}
    params.update(emergency)
    over = deep_merge(MINI_OVERRIDES, {"emergency": params})
    return load_config(overrides=deep_merge(over, top or {}))


def make_ctx(config: Config, seed: int = 1) -> SimContext:
    env = simpy.Environment(initial_time=min_to_s(config.t_open_min))
    ctx = SimContext(env=env, config=config, rngs=RngStreams(seed))
    ctx.entry = build_entry_resources(ctx)
    ctx.stadium = build_stadium_resources(ctx)
    ctx.exits = build_exit_resources(ctx)
    return ctx


def seated(i: int, distance_m: float = 60.0, speed_mps: float = 1.0, zone: str = "A"):
    sp = Spectator(i, zone, 1, 1, "lower", "standard", speed_mps, distance_m, -40.0, 4.0)
    sp.t_start_control, sp.t_end_control = -40.0, -39.9
    sp.t_vomitory, sp.t_seated = -38.0, -37.9
    return sp


def journey(sp: Spectator, ctx: SimContext):
    """Lo que hará el runner en T4.3: recorrido normal y, si suena la alarma, evacuación."""
    try:
        yield from entry_process(sp, ctx)
        yield from seating_process(sp, ctx)
        yield from exit_process(sp, ctx)
    except simpy.Interrupt:
        yield from evacuation_process(sp, ctx)


def waiting_seated(sp: Spectator, ctx: SimContext):
    """Espectador ya sentado que espera al final del partido."""
    try:
        yield from exit_process(sp, ctx)
    except simpy.Interrupt:
        yield from evacuation_process(sp, ctx)


def in_transit(sp: Spectator, ctx: SimContext):
    """Espectador entre el torno y el asiento cuando suena la alarma."""
    try:
        yield ctx.env.timeout(min_to_s(1000))
    except simpy.Interrupt:
        yield from evacuation_process(sp, ctx)


def run_alarm(ctx: SimContext, sps: list[Spectator], body=waiting_seated) -> None:
    ctx.spectators = sps
    procs = [ctx.env.process(body(sp, ctx)) for sp in sps]
    ctx.env.process(alarm_process(ctx, procs))
    ctx.env.run(until=ctx.env.all_of(procs))


# -- clasificación al sonar la alarma -------------------------------------------


def test_status_at_alarm() -> None:
    sp = seated(0)
    assert status_at_alarm(sp, 40.0) == INSIDE
    sp.t_seated = sp.t_vomitory = math.nan  # en tránsito tras el torno
    assert status_at_alarm(sp, 40.0) == INSIDE
    sp.t_end_control = math.nan  # en cola o pasando el torno
    assert status_at_alarm(sp, 40.0) == OUTSIDE_QUEUE
    sp.t_arrival = 45.0
    assert status_at_alarm(sp, 40.0) == NOT_ARRIVED
    out = seated(1)
    out.t_exit = 110.0
    assert status_at_alarm(out, 40.0) == ALREADY_OUT


# -- proceso de alarma -------------------------------------------------------------


def test_disabled_does_nothing(mini_config: Config) -> None:
    ctx = make_ctx(mini_config)
    before = dict(ctx.exits.pass_time_s)
    ctx.env.process(alarm_process(ctx))
    ctx.env.run()
    assert ctx.phase == "entry"
    assert ctx.exits.pass_time_s == before
    assert len(ctx.exits.reaction_s) == 0


def test_alarm_changes_state() -> None:
    cfg = emergency_config(alarm_min=40)
    ctx = make_ctx(cfg)
    ctx.env.process(alarm_process(ctx))
    ctx.env.run(until=min_to_s(39.9))
    assert ctx.phase == "entry" and all(ctx.entry.gate_open.values())
    ctx.env.run()

    assert ctx.phase == "evacuation"
    assert not any(ctx.entry.gate_open.values())
    evac = exit_pass_time_s(cfg.exit_width_m * cfg.emergency.exit_width_factor, 66)
    assert evac == pytest.approx(0.1748, abs=1e-4)
    assert all(v == pytest.approx(evac) for v in ctx.exits.pass_time_s.values())
    assert ctx.exits.blocked == set()
    tri = cfg.emergency.reaction_s
    r = ctx.exits.reaction_s
    assert r.shape == (cfg.n_spectators,)
    assert r.min() >= tri.low and r.max() <= tri.high


def test_reaction_times_distribution_and_common_numbers() -> None:
    a = make_ctx(emergency_config({"n_spectators": 50_000}), seed=5)
    b = make_ctx(emergency_config({"n_spectators": 50_000}, blocked_exit=True), seed=5)
    for ctx in (a, b):
        ctx.env.process(alarm_process(ctx))
        ctx.env.run()
    np.testing.assert_array_equal(a.exits.reaction_s, b.exits.reaction_s)
    tri = a.config.emergency.reaction_s
    assert a.exits.reaction_s.mean() == pytest.approx(tri.mean, rel=0.01)


def test_blocked_exit() -> None:
    cfg = emergency_config(blocked_exit=True, blocked_exit_zone="A")
    ctx = make_ctx(cfg)
    ctx.env.process(alarm_process(ctx))
    ctx.env.run()
    assert ctx.exits.blocked == {("A", BLOCKED_EXIT_ID)}


def test_alarm_in_the_past_raises() -> None:
    ctx = make_ctx(emergency_config(alarm_min=-60))
    ctx.env.run(until=min_to_s(-50))
    ctx.env.process(alarm_process(ctx))
    with pytest.raises(ValueError, match="alarm_min"):
        ctx.env.run()


# -- evacuación de un espectador ---------------------------------------------------


def test_seated_spectator_evacuates() -> None:
    cfg = emergency_config(alarm_min=40)
    ctx = make_ctx(cfg)
    sp = seated(3, distance_m=72.0, speed_mps=1.0)
    run_alarm(ctx, [sp])

    reaction = ctx.exits.reaction_s[3]
    walk = 72.0 / (1.0 * cfg.emergency.speed_factor)
    assert min_to_s(sp.t_exit_queue) == pytest.approx(min_to_s(40.0) + reaction + walk)
    assert min_to_s(sp.t_safe) - min_to_s(sp.t_exit_queue) == pytest.approx(
        exit_pass_time_s(4.0 * 1.3, 66)
    )
    assert math.isnan(sp.t_exit) and sp.abandoned is False
    assert 1 <= sp.exit_id <= cfg.exits_per_zone


def test_blocked_exit_not_used() -> None:
    ctx = make_ctx(emergency_config(blocked_exit=True))
    sps = [seated(i) for i in range(60)]
    run_alarm(ctx, sps)
    assert BLOCKED_EXIT_ID not in {sp.exit_id for sp in sps}
    assert all(not math.isnan(sp.t_safe) for sp in sps)


def test_open_conflict_closed_at_alarm() -> None:
    ctx = make_ctx(emergency_config(alarm_min=40))
    sp = seated(0)
    sp.t_seated = math.nan
    sp.conflict = True
    log_incident(ctx, Incident("I1", "A", "A-B1", 39.0, spectator_id=0))
    run_alarm(ctx, [sp], body=in_transit)
    assert ctx.incidents[0].t_end == pytest.approx(40.0)
    assert not math.isnan(sp.t_safe)


def test_full_journey_with_early_alarm() -> None:
    """Alarma en hora punta (t = -10): unos no han llegado, otros están en cola y otros dentro."""
    cfg = emergency_config({"turnstiles_per_gate": 1, "n_spectators": 3000}, alarm_min=-10)
    ctx = make_ctx(cfg, seed=7)
    sps = generate_spectators(cfg, ctx.rngs)
    run_alarm(ctx, sps, body=journey)

    statuses = {s: [] for s in (NOT_ARRIVED, OUTSIDE_QUEUE, INSIDE)}
    for sp in sps:
        assert math.isnan(sp.t_exit)  # nadie sale por la salida ordinaria
        if sp.t_arrival > -10:
            statuses[NOT_ARRIVED].append(sp)
            assert math.isnan(sp.t_start_control) and not sp.abandoned
            assert math.isnan(sp.t_safe)
        elif sp.abandoned:
            statuses[OUTSIDE_QUEUE].append(sp)
            assert math.isnan(sp.t_end_control) and math.isnan(sp.t_safe)
        else:
            statuses[INSIDE].append(sp)
            assert sp.t_end_control <= -10
            assert sp.t_safe >= sp.t_exit_queue >= -10
    assert all(statuses.values()), {k: len(v) for k, v in statuses.items()}
    # Nadie retiene recursos al terminar.
    assert all(r.count == 0 for r in ctx.entry.turnstiles.values())
    assert all(r.count == 0 for r in ctx.stadium.vomitories.values())
    assert all(r.count == 0 for r in ctx.exits.exits.values())


# -- validación con el apartado 4.3 de la memoria ---------------------------------


@pytest.mark.parametrize(("blocked", "expected_min"), [(False, 5.9), (True, 7.1)])
def test_zone_evacuation_time_matches_memoria(blocked: bool, expected_min: float) -> None:
    """12.195 personas de una macrozona: 5,9 min con 6 salidas y 7,1 min con una bloqueada."""
    cfg = emergency_config(
        {"n_spectators": 12_195},
        blocked_exit=blocked,
        reaction_s={"low": 1, "mode": 1, "high": 1},
    )
    ctx = make_ctx(cfg)
    sps = [seated(i, distance_m=1.0) for i in range(cfg.n_spectators)]
    run_alarm(ctx, sps)
    crossing_min = max(sp.t_safe for sp in sps) - min(sp.t_exit_queue for sp in sps)
    assert crossing_min == pytest.approx(expected_min, abs=0.05)

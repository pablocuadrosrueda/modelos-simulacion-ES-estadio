"""Incidencias I1 (conflicto por asiento) e I4 (cierre de puerta).

Responsable: B. (I2 e I3 viven en ``entry.py``, responsable A; ver
``docs/DECISIONES.md``.)

Memoria §3.2:

* I1: al llegar al asiento, con prob. ``seat_conflict.prob`` (0,5 %; 1 % en
  X5) hay conflicto. El espectador retiene su plaza de vomitorio, pide un
  acomodador de su macrozona (FIFO) y la resolución dura Triangular(1, 3, 10)
  min (flujo ``"seat_conflict"``).
* I4: la puerta ``gate`` de ``zone`` se cierra en ``start_min`` durante
  ``duration_min``. Cambia ``EntryResources.gate_open`` y dispara
  ``reopen_event`` al reabrir. Quien espera ese evento se reanuda en orden de
  registro (D13). Tras dispararlo se pone un evento nuevo sin disparar, por si
  la puerta vuelve a cerrarse.

Números aleatorios comunes en I1 (D17, D21): la ocurrencia y la duración del
conflicto son de cada espectador. :func:`sample_seat_conflicts` las sortea de una
vez para los ``n_spectators`` (lo llama ``stadium.build_stadium_resources`` en
E0) y el espectador ``id`` usa su posición. Al subir ``prob`` (0,5 % -> 1 %), el
conjunto de quien tiene conflicto crece y conserva a los anteriores.

Todas las incidencias se registran con :func:`log_incident`.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Any

import numpy as np

from .arrivals import sample_service_times
from .config import SeatConflictParams
from .entities import Incident, Spectator, block_label, gate_label, min_to_s, s_to_min

if TYPE_CHECKING:
    from .runner import SimContext


def log_incident(ctx: SimContext, incident: Incident) -> Incident:
    """Añade ``incident`` a ``ctx.incidents`` y lo devuelve (para fijar ``t_end`` luego)."""
    ctx.incidents.append(incident)
    return incident


def sample_seat_conflicts(
    params: SeatConflictParams, n: int, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """Sorteo de I1 para ``n`` espectadores (D21), del flujo ``"seat_conflict"``.

    Devuelve ``(u, resolution_s)``: ``u`` ~ Uniforme(0, 1), de modo que hay
    conflicto si ``u < prob``, y la duración de la resolución en segundos ~
    Triangular(``resolution_min``) × 60. Siempre consume ``2n`` números, esté o
    no activa la incidencia.
    """
    u = rng.random(n)
    resolution_s = sample_service_times(params.resolution_min, n, rng) * 60.0
    return u, resolution_s


def has_seat_conflict(spectator: Spectator, ctx: SimContext) -> bool:
    """¿Encuentra el espectador su asiento ocupado (I1)?

    No sortea: compara su número ``u`` de E0 con ``seat_conflict.prob`` (D21).
    Con la incidencia desactivada, siempre ``False``.
    """
    params = ctx.config.incidents.seat_conflict
    if not params.enabled:
        return False
    assert ctx.stadium is not None, "build_stadium_resources debe ejecutarse antes (E0)"
    return bool(ctx.stadium.seat_conflict_u[spectator.id] < params.prob)


def seat_conflict(spectator: Spectator, ctx: SimContext) -> Generator[Any, Any, None]:
    """Sub-proceso SimPy de resolución de un conflicto (I1).

    Se invoca con ``yield from`` desde ``stadium.seating_process`` mientras el
    espectador retiene la plaza del vomitorio. Marca ``conflict = True``,
    registra una incidencia ``I1`` (``resource`` = bloque, p. ej. ``"A-B3"``,
    con ``spectator_id``), pide un acomodador de su macrozona (FIFO), lo retiene
    durante su tiempo de resolución y fija ``t_end`` al soltarlo. ``t_end -
    t_start`` incluye la espera al acomodador.
    """
    env = ctx.env
    assert ctx.stadium is not None, "build_stadium_resources debe ejecutarse antes (E0)"
    spectator.conflict = True
    incident = log_incident(
        ctx,
        Incident(
            "I1",
            spectator.zone,
            block_label(spectator.zone, spectator.block),
            s_to_min(env.now),
            spectator_id=spectator.id,
        ),
    )
    with ctx.stadium.stewards[spectator.zone].request() as req:
        yield req
        yield env.timeout(float(ctx.stadium.seat_conflict_resolution_s[spectator.id]))
    incident.t_end = s_to_min(env.now)


def gate_closure_process(ctx: SimContext) -> Generator[Any, Any, None]:
    """Proceso SimPy que cierra y reabre la puerta configurada (I4).

    Si ``incidents.gate_closure.enabled`` es falso no hace nada. Si no, espera
    hasta ``start_min``, cierra la puerta (``gate_open = False``) y registra una
    incidencia ``I4`` con ``resource = "A-G1"``; tras ``duration_min`` la reabre,
    fija ``t_end`` y dispara ``reopen_event`` de esa puerta, que sustituye por
    uno nuevo sin disparar. ``run_replica`` lo lanza en E0.

    Raises:
        ValueError: si ``start_min`` ya ha pasado al lanzar el proceso.
    """
    gc = ctx.config.incidents.gate_closure
    if not gc.enabled:
        return
    env = ctx.env
    assert ctx.entry is not None, "build_entry_resources debe ejecutarse antes (E0)"

    t_close_s = min_to_s(gc.start_min)
    if env.now > t_close_s:
        raise ValueError(
            f"gate_closure.start_min = {gc.start_min} ya ha pasado (t = {s_to_min(env.now)} min)"
        )
    yield env.timeout(t_close_s - env.now)

    key = (gc.zone, gc.gate)
    ctx.entry.gate_open[key] = False
    incident = log_incident(
        ctx, Incident("I4", gc.zone, gate_label(gc.zone, gc.gate), s_to_min(env.now))
    )

    yield env.timeout(min_to_s(gc.duration_min))

    ctx.entry.gate_open[key] = True
    incident.t_end = s_to_min(env.now)
    reopen = ctx.entry.reopen_event[key]
    ctx.entry.reopen_event[key] = env.event()
    reopen.succeed()

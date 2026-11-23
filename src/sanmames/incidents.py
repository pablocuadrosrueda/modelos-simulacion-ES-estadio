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

Todas las incidencias se registran con :func:`log_incident`.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from .entities import Incident, Spectator, gate_label, min_to_s, s_to_min

if TYPE_CHECKING:
    from .runner import SimContext


def log_incident(ctx: SimContext, incident: Incident) -> Incident:
    """Añade ``incident`` a ``ctx.incidents`` y lo devuelve (para fijar ``t_end`` luego)."""
    ctx.incidents.append(incident)
    return incident


def has_seat_conflict(spectator: Spectator, ctx: SimContext) -> bool:
    """Sortea si el espectador encuentra su asiento ocupado (I1)."""
    raise NotImplementedError("T2.5-B: has_seat_conflict")


def seat_conflict(spectator: Spectator, ctx: SimContext) -> Generator[Any, Any, None]:
    """Sub-proceso SimPy de resolución de un conflicto (I1).

    Se invoca con ``yield from`` desde ``stadium.seating_process`` mientras el
    espectador retiene la plaza del vomitorio.
    """
    raise NotImplementedError("T2.5-B: seat_conflict")


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

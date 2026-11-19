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
  ``reopen_event`` al reabrir.

Todas las incidencias se registran con :func:`log_incident`.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from .entities import Incident, Spectator

if TYPE_CHECKING:
    from .runner import SimContext


def log_incident(ctx: SimContext, incident: Incident) -> Incident:
    """Añade ``incident`` a ``ctx.incidents`` y lo devuelve (para fijar ``t_end`` luego)."""
    raise NotImplementedError("T2.5-B: log_incident")


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
    """Proceso SimPy que cierra y reabre la puerta configurada (I4)."""
    raise NotImplementedError("T2.6-B: gate_closure_process")

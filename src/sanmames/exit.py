"""Fase C · Salida ordinaria (E5, E6).

Responsable: B.

Memoria §3.1 Fase C, §4.3 y §4.5:

* en ``t_end_min`` se libera la salida (E5): todos a la vez
  (``exit_policy == "simultaneous"``) o la grada inferior primero y la
  superior ``exit_stagger_min`` después (``"staggered"``);
* cada espectador recorre de nuevo ``distance_m`` a su velocidad y elige la
  salida de su macrozona con menos cola (desempate: flujo ``"exit_choice"``);
* cada salida es un ``simpy.Resource`` de capacidad 1 con paso determinista
  ``60 / (exit_width_m * exit_rate_per_m_min)`` s por persona (≈ 0,23 s);
* al pasar registra ``t_exit`` (E6).
"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .entities import Spectator

if TYPE_CHECKING:
    import simpy

    from .runner import SimContext


@dataclass
class ExitResources:
    """Salidas por ``(zone, exit_id)`` y su tiempo de paso actual (s/persona)."""

    exits: dict[tuple[str, int], simpy.Resource] = field(default_factory=dict)
    pass_time_s: dict[tuple[str, int], float] = field(default_factory=dict)
    blocked: set[tuple[str, int]] = field(default_factory=set)
    """Salidas inutilizadas (variante X7 con bloqueo)."""


def exit_pass_time_s(width_m: float, rate_per_m_min: float) -> float:
    """Segundos por persona en una salida de anchura ``width_m``."""
    raise NotImplementedError("T3.1-B: exit_pass_time_s")


def build_exit_resources(ctx: SimContext) -> ExitResources:
    """Crea las ``exits_per_zone`` salidas de cada macrozona."""
    raise NotImplementedError("T3.1-B: build_exit_resources")


def release_time_min(spectator: Spectator, ctx: SimContext) -> float:
    """Instante (min) en que se libera la salida del espectador según la política."""
    raise NotImplementedError("T3.2-B: release_time_min")


def choose_exit(spectator: Spectator, ctx: SimContext) -> int:
    """Salida no bloqueada de su macrozona con menos cola."""
    raise NotImplementedError("T3.1-B: choose_exit")


def exit_process(spectator: Spectator, ctx: SimContext) -> Generator[Any, Any, None]:
    """Proceso SimPy: liberación -> desplazamiento -> cola -> paso por salida.

    Rellena ``exit_id``, ``t_exit_queue`` y ``t_exit``.
    """
    raise NotImplementedError("T3.1-B: exit_process")

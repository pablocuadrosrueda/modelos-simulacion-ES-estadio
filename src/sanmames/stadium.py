"""Ubicación y permanencia: vomitorios, acomodadores y fase de partido (E4).

Responsable: B.

Memoria §3.1 paso 5-6 y Fase B, §4.5:

* tras el torno, el espectador camina ``distance_m / speed_mps`` hasta su
  vomitorio (10 por macrozona, ``vomitory_capacity`` = 8 plazas, FIFO);
* el paso por el vomitorio dura Triangular(5, 10, 20) s (flujo ``"vomitory"``);
* si hay conflicto por asiento (I1, ver ``incidents.seat_conflict``) retiene
  la plaza del vomitorio hasta que un acomodador lo resuelve;
* al sentarse registra ``t_seated`` y ``late`` (E4);
* entre ``t_start_min`` y ``t_end_min`` permanece sentado; si hay emergencia,
  el proceso puede ser interrumpido (``Process.interrupt``) por la alarma.
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
class StadiumResources:
    """Vomitorios por ``(zone, block)`` y acomodadores por ``zone``."""

    vomitories: dict[tuple[str, int], simpy.Resource] = field(default_factory=dict)
    stewards: dict[str, simpy.Resource] = field(default_factory=dict)


def build_stadium_resources(ctx: SimContext) -> StadiumResources:
    """Crea los vomitorios y los acomodadores de todas las macrozonas."""
    raise NotImplementedError("T1.3-B: build_stadium_resources")


def seating_process(spectator: Spectator, ctx: SimContext) -> Generator[Any, Any, None]:
    """Proceso SimPy: desplazamiento -> vomitorio -> asiento (E3 -> E4).

    Rellena ``t_vomitory``, ``t_seated``, ``conflict`` y ``late``.
    """
    raise NotImplementedError("T1.3-B: seating_process")


def is_late(spectator: Spectator, ctx: SimContext) -> bool:
    """Entrada tardía: llegó antes de ``t_start_min`` y se sentó después."""
    raise NotImplementedError("T1.3-B: is_late")

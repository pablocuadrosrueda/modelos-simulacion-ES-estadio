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

Números aleatorios comunes (D17, D18): el paso por el vomitorio es una variable
por espectador, así que no se sortea dentro del proceso. ``build_stadium_resources``
sortea de una vez ``n_spectators`` tiempos del flujo ``"vomitory"`` y el
espectador ``id`` usa el de su posición. Así cada espectador recibe el mismo
número en todos los escenarios, sea cual sea el orden en que llega al vomitorio.
"""

from __future__ import annotations

import math
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
import simpy

from .arrivals import sample_service_times
from .entities import Spectator, min_to_s, s_to_min

if TYPE_CHECKING:
    from .runner import SimContext


@dataclass
class StadiumResources:
    """Vomitorios por ``(zone, block)`` y acomodadores por ``zone``."""

    vomitories: dict[tuple[str, int], simpy.Resource] = field(default_factory=dict)
    stewards: dict[str, simpy.Resource] = field(default_factory=dict)
    vomitory_pass_s: np.ndarray = field(default_factory=lambda: np.empty(0))
    """Tiempo de paso por el vomitorio (s) del espectador ``id`` (D18)."""


def build_stadium_resources(ctx: SimContext) -> StadiumResources:
    """Crea los vomitorios y los acomodadores de todas las macrozonas.

    Por cada bloque ``(zone, block)`` (``block`` 1-indexado) un ``Resource``
    FIFO con ``vomitory_capacity`` plazas; por cada macrozona un ``Resource``
    con ``stewards_per_zone`` acomodadores. Sortea además los
    ``n_spectators`` tiempos de paso por el vomitorio (D18).
    """
    cfg = ctx.config
    res = StadiumResources()
    for zone in cfg.zones:
        res.stewards[zone] = simpy.Resource(ctx.env, capacity=cfg.stewards_per_zone)
        for block in range(1, cfg.blocks_per_zone + 1):
            res.vomitories[(zone, block)] = simpy.Resource(ctx.env, capacity=cfg.vomitory_capacity)
    res.vomitory_pass_s = sample_service_times(
        cfg.vomitory_pass_s, cfg.n_spectators, ctx.rngs["vomitory"]
    )
    return res


def seating_process(spectator: Spectator, ctx: SimContext) -> Generator[Any, Any, None]:
    """Proceso SimPy: desplazamiento -> vomitorio -> asiento (E3 -> E4).

    Parte de ``t_end_control`` (si se lanza antes, espera hasta entonces):
    camina ``distance_m / speed_mps`` s, se une a la cola del vomitorio de su
    bloque (``t_vomitory``), ocupa una plaza durante su tiempo de paso y al
    soltarla se sienta (``t_seated``, ``late``).

    Rellena ``t_vomitory``, ``t_seated``, ``conflict`` y ``late``. Inc1: sin
    conflictos por asiento (I1 llega en T2.5), así que ``conflict`` queda en
    ``False``.
    """
    env = ctx.env
    assert ctx.stadium is not None, "build_stadium_resources debe ejecutarse antes (E0)"
    assert not math.isnan(spectator.t_end_control), "seating_process exige t_end_control"

    t_ready_s = min_to_s(spectator.t_end_control)
    if env.now < t_ready_s:
        yield env.timeout(t_ready_s - env.now)

    yield env.timeout(spectator.distance_m / spectator.speed_mps)
    spectator.t_vomitory = s_to_min(env.now)

    vomitory = ctx.stadium.vomitories[(spectator.zone, spectator.block)]
    with vomitory.request() as req:
        yield req
        yield env.timeout(float(ctx.stadium.vomitory_pass_s[spectator.id]))
        # T2.5: aquí, aún con la plaza retenida, ``yield from incidents.seat_conflict``.

    spectator.t_seated = s_to_min(env.now)
    spectator.late = is_late(spectator, ctx)


def is_late(spectator: Spectator, ctx: SimContext) -> bool:
    """Entrada tardía: llegó antes de ``t_start_min`` y se sentó después.

    Quien no se ha sentado (``t_seated`` NaN) no cuenta como tardío.
    """
    t_start = ctx.config.t_start_min
    return bool(spectator.t_arrival < t_start and spectator.t_seated > t_start)

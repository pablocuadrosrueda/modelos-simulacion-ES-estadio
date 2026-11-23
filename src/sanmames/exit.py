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

Números aleatorios comunes (D24): el desempate entre salidas igual de cargadas es
una variable por espectador. ``build_exit_resources`` sortea de una vez
``n_spectators`` uniformes del flujo ``"exit_choice"`` y el espectador ``id`` usa
la suya, como en D18.
"""

from __future__ import annotations

import math
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
import simpy

from .entities import Spectator, min_to_s, s_to_min

if TYPE_CHECKING:
    from .runner import SimContext


@dataclass
class ExitResources:
    """Salidas por ``(zone, exit_id)`` y su tiempo de paso actual (s/persona)."""

    exits: dict[tuple[str, int], simpy.Resource] = field(default_factory=dict)
    pass_time_s: dict[tuple[str, int], float] = field(default_factory=dict)
    blocked: set[tuple[str, int]] = field(default_factory=set)
    """Salidas inutilizadas (variante X7 con bloqueo)."""
    tie_u: np.ndarray = field(default_factory=lambda: np.empty(0))
    """Uniforme(0, 1) del espectador ``id`` para desempatar salidas (D24)."""
    reaction_s: np.ndarray = field(default_factory=lambda: np.empty(0))
    """Tiempo de reacción a la alarma (s) del espectador ``id``; lo rellena
    ``emergency.alarm_process`` al sonar la alarma (D25)."""


def exit_pass_time_s(width_m: float, rate_per_m_min: float) -> float:
    """Segundos por persona en una salida de anchura ``width_m``.

    Con ``rate_per_m_min`` personas por metro y minuto, la salida deja pasar
    ``width_m * rate_per_m_min`` personas/min, es decir, una cada
    ``60 / (width_m * rate_per_m_min)`` s (4 m y 66 -> 0,227 s).
    """
    if width_m <= 0 or rate_per_m_min <= 0:
        raise ValueError("width_m y rate_per_m_min deben ser > 0")
    return 60.0 / (width_m * rate_per_m_min)


def build_exit_resources(ctx: SimContext) -> ExitResources:
    """Crea las ``exits_per_zone`` salidas de cada macrozona.

    Por cada salida ``(zone, exit_id)`` (``exit_id`` 1-indexado) un ``Resource``
    de capacidad 1 con el paso ordinario, ninguna bloqueada. Sortea además los
    ``n_spectators`` números de desempate (D24).
    """
    cfg = ctx.config
    res = ExitResources()
    pass_s = exit_pass_time_s(cfg.exit_width_m, cfg.exit_rate_per_m_min)
    for zone in cfg.zones:
        for exit_id in range(1, cfg.exits_per_zone + 1):
            key = (zone, exit_id)
            res.exits[key] = simpy.Resource(ctx.env, capacity=1)
            res.pass_time_s[key] = pass_s
    res.tie_u = ctx.rngs["exit_choice"].random(cfg.n_spectators)
    return res


def release_time_min(spectator: Spectator, ctx: SimContext) -> float:
    """Instante (min) en que se libera la salida del espectador según la política.

    ``"simultaneous"``: ``t_end_min`` para todos. ``"staggered"``: la grada
    inferior en ``t_end_min`` y la superior ``exit_stagger_min`` después.
    """
    cfg = ctx.config
    if cfg.exit_policy == "simultaneous" or spectator.tier == "lower":
        return cfg.t_end_min
    if cfg.exit_policy == "staggered":
        return cfg.t_end_min + cfg.exit_stagger_min
    raise ValueError(f"exit_policy desconocida: {cfg.exit_policy!r}")


def queue_length(resource: simpy.Resource) -> int:
    """Personas en una salida: esperando más la que está pasando."""
    return len(resource.queue) + resource.count


def choose_exit(spectator: Spectator, ctx: SimContext) -> int:
    """Salida no bloqueada de su macrozona con menos cola.

    Si varias empatan, elige entre ellas con el número de desempate del
    espectador (D24): la ``floor(u * k)``-ésima de las ``k`` empatadas, en orden
    de ``exit_id``.
    """
    assert ctx.exits is not None, "build_exit_resources debe ejecutarse antes (E0)"
    res = ctx.exits
    zone = spectator.zone
    candidates = [
        e for e in range(1, ctx.config.exits_per_zone + 1) if (zone, e) not in res.blocked
    ]
    if not candidates:
        raise RuntimeError(f"La macrozona {zone} no tiene salidas disponibles")
    lengths = [queue_length(res.exits[(zone, e)]) for e in candidates]
    shortest = min(lengths)
    tied = [e for e, n in zip(candidates, lengths, strict=True) if n == shortest]
    k = min(int(res.tie_u[spectator.id] * len(tied)), len(tied) - 1)
    return tied[k]


def exit_process(spectator: Spectator, ctx: SimContext) -> Generator[Any, Any, None]:
    """Proceso SimPy: liberación -> desplazamiento -> cola -> paso por salida.

    Si se lanza antes de su liberación (E5), espera hasta entonces; si se lanza
    después (p. ej. se sentó tarde), sale en ese momento. Camina
    ``distance_m / speed_mps`` s, elige salida al llegar (``choose_exit``), hace
    cola y la atraviesa en ``pass_time_s`` (E6).

    Rellena ``exit_id``, ``t_exit_queue`` y ``t_exit``.
    """
    env = ctx.env
    assert ctx.exits is not None, "build_exit_resources debe ejecutarse antes (E0)"
    assert not math.isnan(spectator.t_seated), "exit_process exige t_seated"

    t_release_s = min_to_s(release_time_min(spectator, ctx))
    if env.now < t_release_s:
        yield env.timeout(t_release_s - env.now)

    yield env.timeout(spectator.distance_m / spectator.speed_mps)

    exit_id = choose_exit(spectator, ctx)
    key = (spectator.zone, exit_id)
    spectator.exit_id = exit_id
    spectator.t_exit_queue = s_to_min(env.now)
    with ctx.exits.exits[key].request() as req:
        yield req
        yield env.timeout(ctx.exits.pass_time_s[key])
    spectator.t_exit = s_to_min(env.now)

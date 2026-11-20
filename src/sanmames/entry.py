"""Fase A · Entrada: colas de puerta y control en torno (E1, E2, E3, I2, I3).

Responsable: A.

Memoria §3.1 pasos 3-4, §3.2 y §4.5:

* cada puerta tiene ``turnstiles_per_gate`` tornos modelados como un
  ``simpy.PriorityResource`` (capacidad = tornos de la puerta);
* FIFO por defecto; con ``queue_discipline == "priority"`` los grupos de
  ``priority_groups`` piden con prioridad mayor (no expulsiva);
* servicio Triangular(2, 4, 6) s; con prob. 3 % hay relectura (I2) que añade
  Uniforme(5, 15) s;
* I3 (avería): un proceso por torno pide el recurso con la máxima prioridad
  tras un tiempo Exponencial(240 min) y lo retiene Uniforme(3, 10) min; nunca
  corta un servicio en curso;
* si la puerta está cerrada (I4, ver ``incidents.py``) se redirige a la puerta
  de la macrozona con menos cola o se espera a que reabra.

Prioridades SimPy (menor = antes): ``PRIORITY_FAILURE`` < ``PRIORITY_HIGH`` <
``PRIORITY_NORMAL``.
"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import simpy

from .entities import Spectator, min_to_s, s_to_min

if TYPE_CHECKING:
    from .runner import SimContext

PRIORITY_FAILURE = -1
PRIORITY_HIGH = 0
PRIORITY_NORMAL = 1


@dataclass
class EntryResources:
    """Recursos de la fase de entrada, indexados por ``(zone, gate)``."""

    turnstiles: dict[tuple[str, int], simpy.PriorityResource] = field(default_factory=dict)
    gate_open: dict[tuple[str, int], bool] = field(default_factory=dict)
    """Estado ``puerta_abierta[p]``; lo modifica ``incidents.gate_closure_process``."""
    reopen_event: dict[tuple[str, int], simpy.Event] = field(default_factory=dict)
    """Evento que se dispara al reabrir la puerta (para quien espera sin redirección)."""
    failed_turnstiles: dict[tuple[str, int], int] = field(default_factory=dict)
    """``tornos_averiados[p]``."""


def build_entry_resources(ctx: SimContext) -> EntryResources:
    """Crea tornos y estado de puertas para todas las macrozonas de ``ctx.config``.

    Por cada puerta ``(zone, gate)`` (``gate`` 1-indexada): un
    ``PriorityResource`` con ``turnstiles_per_gate`` plazas, la puerta abierta,
    un evento de reapertura sin disparar y 0 tornos averiados.
    """
    cfg = ctx.config
    res = EntryResources()
    for zone in cfg.zones:
        for gate in range(1, cfg.gates_per_zone + 1):
            key = (zone, gate)
            res.turnstiles[key] = simpy.PriorityResource(ctx.env, capacity=cfg.turnstiles_per_gate)
            res.gate_open[key] = True
            res.reopen_event[key] = ctx.env.event()
            res.failed_turnstiles[key] = 0
    return res


def priority_of(spectator: Spectator, ctx: SimContext) -> int:
    """Prioridad SimPy del espectador en el torno según la disciplina de cola.

    FIFO: todos ``PRIORITY_NORMAL``; a igual prioridad, SimPy atiende por orden
    de petición. La disciplina ``"priority"`` (X3) llega en T2.4.
    """
    if ctx.config.queue_discipline == "fifo":
        return PRIORITY_NORMAL
    raise NotImplementedError("T2.4-A: priority_of con queue_discipline='priority'")


def choose_gate(spectator: Spectator, ctx: SimContext) -> int:
    """Puerta a la que se une el espectador (E1), aplicando la redirección de I4."""
    raise NotImplementedError("T2.7-A: choose_gate")


def entry_process(spectator: Spectator, ctx: SimContext) -> Generator[Any, Any, None]:
    """Proceso SimPy: llegada -> cola -> torno (E1-E3).

    Rellena ``gate_used``, ``t_start_control``, ``t_end_control`` y
    ``read_failure``. Al terminar, el llamador continúa con
    ``stadium.seating_process``.

    Si se lanza antes de ``t_arrival``, espera hasta esa hora. Inc1: usa la
    puerta asignada (``spectator.gate``; la redirección de I4 llega en T2.7) y
    no aplica I2 (T2.2), así que ``read_failure`` queda en ``False``.
    """
    env = ctx.env
    assert ctx.entry is not None, "build_entry_resources debe ejecutarse antes (E0)"

    t_arrival_s = min_to_s(spectator.t_arrival)
    if env.now < t_arrival_s:
        yield env.timeout(t_arrival_s - env.now)

    gate = spectator.gate
    spectator.gate_used = gate
    turnstiles = ctx.entry.turnstiles[(spectator.zone, gate)]
    with turnstiles.request(priority=priority_of(spectator, ctx), preempt=False) as req:
        yield req
        spectator.t_start_control = s_to_min(env.now)
        yield env.timeout(spectator.service_s)
        spectator.t_end_control = s_to_min(env.now)


def turnstile_failure_process(zone: str, gate: int, ctx: SimContext) -> Generator[Any, Any, None]:
    """Proceso SimPy de averías (I3) de los tornos de una puerta."""
    raise NotImplementedError("T2.3-A: turnstile_failure_process")

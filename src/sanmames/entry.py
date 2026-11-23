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

from .entities import Incident, Spectator, gate_label, min_to_s, s_to_min
from .incidents import log_incident

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

    * ``"fifo"``: todos ``PRIORITY_NORMAL``; a igual prioridad SimPy atiende por
      orden de petición.
    * ``"priority"`` (X3): los grupos de ``config.priority_groups`` piden con
      ``PRIORITY_HIGH`` y pasan por delante de los ``PRIORITY_NORMAL`` que esperan.
      Es **no expulsiva**: ``entry_process`` pide siempre con ``preempt=False``, así
      que un control ya iniciado nunca se interrumpe. Dentro de cada nivel sigue
      siendo FIFO.
    """
    cfg = ctx.config
    if cfg.queue_discipline == "fifo":
        return PRIORITY_NORMAL
    if cfg.queue_discipline == "priority":
        return PRIORITY_HIGH if spectator.group in cfg.priority_groups else PRIORITY_NORMAL
    raise ValueError(f"queue_discipline desconocida: {cfg.queue_discipline!r}")


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
    on_time = env.now <= t_arrival_s
    if env.now < t_arrival_s:
        yield env.timeout(t_arrival_s - env.now)

    gate = spectator.gate
    spectator.gate_used = gate
    turnstiles = ctx.entry.turnstiles[(spectator.zone, gate)]
    t_request_s = env.now
    with turnstiles.request(priority=priority_of(spectator, ctx), preempt=False) as req:
        yield req
        if on_time and env.now == t_request_s:
            # Sin cola: la espera es exactamente 0 (s_to_min(min_to_s(t)) puede
            # quedar ~1e-14 min por debajo de t_arrival; aviso de B en T1.3).
            spectator.t_start_control = spectator.t_arrival
        else:
            spectator.t_start_control = s_to_min(env.now)
        yield env.timeout(spectator.service_s)
        spectator.t_end_control = s_to_min(env.now)


def turnstile_failure_process(zone: str, gate: int, ctx: SimContext) -> Generator[Any, Any, None]:
    """Proceso SimPy de averías (I3) de los tornos de una puerta.

    Lanza un sub-proceso por torno ``k = 1..turnstiles_per_gate`` (ver
    ``_turnstile_failure_loop``) y espera a todos; como los bucles no terminan,
    la réplica acaba por la condición del runner (``finished | time_limit``).
    Si ``incidents.turnstile_failure.enabled`` es falso termina al instante.
    """
    cfg = ctx.config
    if not cfg.incidents.turnstile_failure.enabled:
        return
    loops = [
        ctx.env.process(_turnstile_failure_loop(zone, gate, k, ctx))
        for k in range(1, cfg.turnstiles_per_gate + 1)
    ]
    yield ctx.env.all_of(loops)


def _turnstile_failure_loop(
    zone: str, gate: int, k: int, ctx: SimContext
) -> Generator[Any, Any, None]:
    """Ciclo de fallo y reparación del torno ``k`` de la puerta ``(zone, gate)`` (I3).

    1. Funciona Exponencial(``mtbf_min``) (el reloj cuenta solo en funcionamiento,
       D21).
    2. Pide una plaza del recurso de la puerta con ``PRIORITY_FAILURE`` y
       ``preempt=False``: adelanta a todos los que esperan, también a
       ``PRIORITY_HIGH``, pero nunca corta un servicio en curso.
    3. Al conseguirla, el torno queda parado Uniforme(``repair_min``) min: suma
       en ``failed_turnstiles`` y registra una incidencia ``I3`` con ``t_end``
       al terminar la reparación.

    Usa un generador propio derivado de ``(zone, gate, k)`` (D21), así que el
    calendario de sorteos de un torno es el mismo en todos los escenarios.
    """
    env = ctx.env
    params = ctx.config.incidents.turnstile_failure
    assert ctx.entry is not None, "build_entry_resources debe ejecutarse antes (E0)"
    key = (zone, gate)
    turnstiles = ctx.entry.turnstiles[key]
    rng = ctx.rngs.substream("turnstile_failure", zone, gate, k)
    label = f"{gate_label(zone, gate)}-T{k}"
    while True:
        yield env.timeout(min_to_s(rng.exponential(params.mtbf_min)))
        repair_s = min_to_s(rng.uniform(params.repair_min.low, params.repair_min.high))
        with turnstiles.request(priority=PRIORITY_FAILURE, preempt=False) as req:
            yield req
            ctx.entry.failed_turnstiles[key] += 1
            incident = log_incident(ctx, Incident("I3", zone, label, t_start=s_to_min(env.now)))
            yield env.timeout(repair_s)
            ctx.entry.failed_turnstiles[key] -= 1
            incident.t_end = s_to_min(env.now)


def start_turnstile_failure_processes(ctx: SimContext) -> list[simpy.Process]:
    """Lanza ``turnstile_failure_process`` en todas las puertas (I3, E0).

    Orden fijo: ``config.zones`` y, dentro de cada una, puertas 1..``gates_per_zone``.
    Debe llamarse después de ``build_entry_resources``. Si
    ``incidents.turnstile_failure.enabled`` es falso no crea ningún proceso y
    devuelve una lista vacía.
    """
    cfg = ctx.config
    if not cfg.incidents.turnstile_failure.enabled:
        return []
    return [
        ctx.env.process(turnstile_failure_process(zone, gate, ctx))
        for zone in cfg.zones
        for gate in range(1, cfg.gates_per_zone + 1)
    ]

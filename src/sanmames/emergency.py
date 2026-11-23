"""Fase D · Evacuación de emergencia (E7, E8).

Responsable: B.

Memoria §3.1 Fase D:

* en ``emergency.alarm_min`` (t = +40) suena la alarma (E7): se cierran los
  accesos; quien siga en una cola exterior abandona (``abandoned = True``) y no
  cuenta en la evacuación;
* la anchura de las salidas se multiplica por ``exit_width_factor`` (x1,3);
* cada espectador dentro espera su reacción Triangular(30, 60, 120) s (flujo
  ``"reaction"``) y camina a ``speed_factor`` (x1,2) veces su velocidad hasta
  la salida de su macrozona con menos cola;
* con ``blocked_exit`` una salida de ``blocked_exit_zone`` queda inutilizada;
* al cruzar la salida registra ``t_safe``; el último marca E8.

Reparto con el runner (D25): ``alarm_process`` cambia el estado (fase, puertas,
salidas, tiempos de reacción) e interrumpe con ``Process.interrupt`` los
procesos de los espectadores que recibe en ``journeys``. El proceso de cada
espectador (runner, T4.3) captura ``simpy.Interrupt`` y continúa con
``yield from evacuation_process(sp, ctx)``, que decide qué le toca según dónde
estaba al sonar la alarma (:func:`status_at_alarm`).
"""

from __future__ import annotations

import math
from collections.abc import Generator, Sequence
from typing import TYPE_CHECKING, Any

import simpy

from .arrivals import sample_service_times
from .entities import Spectator, min_to_s, s_to_min
from .exit import choose_exit, exit_pass_time_s

if TYPE_CHECKING:
    from .runner import SimContext

BLOCKED_EXIT_ID = 1
"""Salida que se inutiliza en ``blocked_exit_zone`` con ``blocked_exit`` (D25)."""

NOT_ARRIVED = "not_arrived"
OUTSIDE_QUEUE = "outside_queue"
INSIDE = "inside"
ALREADY_OUT = "already_out"


def status_at_alarm(spectator: Spectator, t_alarm_min: float) -> str:
    """Dónde está el espectador al sonar la alarma (D14, D25).

    * ``NOT_ARRIVED``: aún no ha llegado; ya no llega y no cuenta.
    * ``OUTSIDE_QUEUE``: ha llegado pero no ha terminado el control (en cola,
      esperando reapertura o pasando el torno): abandona.
    * ``INSIDE``: ha pasado el torno (caminando, en el vomitorio, en un
      conflicto o sentado): evacúa.
    * ``ALREADY_OUT``: ya salió por la salida ordinaria.
    """
    if not math.isnan(spectator.t_exit):
        return ALREADY_OUT
    if spectator.t_arrival > t_alarm_min:
        return NOT_ARRIVED
    if math.isnan(spectator.t_end_control) or spectator.t_end_control > t_alarm_min:
        return OUTSIDE_QUEUE
    return INSIDE


def alarm_process(
    ctx: SimContext, journeys: Sequence[simpy.Process] | None = None
) -> Generator[Any, Any, None]:
    """Proceso SimPy que en ``alarm_min`` dispara la evacuación (E7).

    Si ``emergency.enabled`` es falso no hace nada. Si no, en ``alarm_min``:

    1. pone ``ctx.phase = "evacuation"`` y cierra todas las puertas de acceso;
    2. sortea los ``n_spectators`` tiempos de reacción del flujo ``"reaction"``
       (``ExitResources.reaction_s``, por ``id``; números comunes, D25);
    3. ensancha las salidas: ``pass_time_s`` pasa a corresponder a una anchura
       ``exit_width_m * exit_width_factor``;
    4. con ``blocked_exit``, inutiliza la salida ``BLOCKED_EXIT_ID`` de
       ``blocked_exit_zone``;
    5. interrumpe los procesos vivos de ``journeys`` (``journeys[i]`` es el del
       espectador ``id == i``), que continúan con :func:`evacuation_process`.

    Raises:
        ValueError: si ``alarm_min`` ya ha pasado al lanzar el proceso.
    """
    em = ctx.config.emergency
    if not em.enabled:
        return
    env = ctx.env
    assert ctx.entry is not None and ctx.exits is not None, "recursos de E0 sin crear"

    t_alarm_s = min_to_s(em.alarm_min)
    if env.now > t_alarm_s:
        raise ValueError(f"emergency.alarm_min = {em.alarm_min} ya ha pasado")
    yield env.timeout(t_alarm_s - env.now)

    cfg = ctx.config
    ctx.phase = "evacuation"
    for key in ctx.entry.gate_open:
        ctx.entry.gate_open[key] = False

    exits = ctx.exits
    exits.reaction_s = sample_service_times(em.reaction_s, cfg.n_spectators, ctx.rngs["reaction"])
    evac_pass_s = exit_pass_time_s(cfg.exit_width_m * em.exit_width_factor, cfg.exit_rate_per_m_min)
    for key in exits.pass_time_s:
        exits.pass_time_s[key] = evac_pass_s
    if em.blocked_exit:
        exits.blocked.add((em.blocked_exit_zone, BLOCKED_EXIT_ID))

    for journey in journeys or ():
        if journey.is_alive:
            journey.interrupt("alarm")


def evacuation_process(spectator: Spectator, ctx: SimContext) -> Generator[Any, Any, None]:
    """Proceso SimPy de evacuación de un espectador (reacción -> marcha -> salida).

    Se llama después de la alarma, normalmente desde el ``except
    simpy.Interrupt`` del proceso del espectador. Según :func:`status_at_alarm`:

    * fuera en cola: ``abandoned = True`` y termina;
    * no había llegado o ya había salido: no hace nada;
    * dentro: espera su reacción, recorre ``distance_m`` completa (D14) a
      ``speed_mps * speed_factor``, elige la salida no bloqueada con menos cola,
      hace cola y la atraviesa con el paso de evacuación (E8).

    Rellena ``abandoned`` o bien ``exit_id``, ``t_exit_queue`` y ``t_safe``.
    """
    env = ctx.env
    em = ctx.config.emergency
    assert ctx.exits is not None and len(ctx.exits.reaction_s), "la alarma no ha sonado"

    status = status_at_alarm(spectator, em.alarm_min)
    if status == OUTSIDE_QUEUE:
        spectator.abandoned = True
        return
    if status != INSIDE:
        return
    _close_open_conflict(spectator, ctx)

    yield env.timeout(float(ctx.exits.reaction_s[spectator.id]))
    yield env.timeout(spectator.distance_m / (spectator.speed_mps * em.speed_factor))

    exit_id = choose_exit(spectator, ctx)
    key = (spectator.zone, exit_id)
    spectator.exit_id = exit_id
    spectator.t_exit_queue = s_to_min(env.now)
    with ctx.exits.exits[key].request() as req:
        yield req
        yield env.timeout(ctx.exits.pass_time_s[key])
    spectator.t_safe = s_to_min(env.now)


def _close_open_conflict(spectator: Spectator, ctx: SimContext) -> None:
    """Un conflicto I1 en curso al sonar la alarma se da por terminado entonces."""
    t_alarm = ctx.config.emergency.alarm_min
    for inc in ctx.incidents:
        if inc.kind == "I1" and inc.spectator_id == spectator.id and math.isnan(inc.t_end):
            inc.t_end = t_alarm

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
"""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from .entities import Spectator

if TYPE_CHECKING:
    from .runner import SimContext


def alarm_process(ctx: SimContext) -> Generator[Any, Any, None]:
    """Proceso SimPy que en ``alarm_min`` dispara la evacuación (E7)."""
    raise NotImplementedError("T4.1-B: alarm_process")


def evacuation_process(spectator: Spectator, ctx: SimContext) -> Generator[Any, Any, None]:
    """Proceso SimPy de evacuación de un espectador (reacción -> marcha -> salida).

    Rellena ``exit_id``, ``t_exit_queue`` y ``t_safe``.
    """
    raise NotImplementedError("T4.1-B: evacuation_process")

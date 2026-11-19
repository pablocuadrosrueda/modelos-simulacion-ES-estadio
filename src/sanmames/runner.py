"""Orquestación de una réplica (E0, E9).

Responsable: C.

``run_replica`` es el único punto de entrada a la simulación:

1. E0: crea ``simpy.Environment(initial_time=t_open_min * 60)``, los
   :class:`~sanmames.rng.RngStreams` de la semilla, los recursos
   (``entry``, ``stadium``, ``exit``) y los espectadores (``arrivals``);
2. lanza un proceso por espectador que encadena entrada -> asiento ->
   (permanencia) -> salida, y los procesos auxiliares (averías, cierre de
   puerta, alarma) según la configuración;
3. E9: corre hasta que salen/evacuan todos o hasta ``max_sim_hours``;
4. devuelve el DataFrame de espectadores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pandas as pd

from .config import Config
from .entities import Incident, Spectator
from .rng import RngStreams

if TYPE_CHECKING:
    import simpy

    from .entry import EntryResources
    from .exit import ExitResources
    from .stadium import StadiumResources

PHASES = ("entry", "match", "exit", "evacuation")


@dataclass
class SimContext:
    """Estado compartido de una réplica. Se pasa a todos los procesos SimPy."""

    env: simpy.Environment
    config: Config
    rngs: RngStreams
    spectators: list[Spectator] = field(default_factory=list)
    incidents: list[Incident] = field(default_factory=list)
    entry: EntryResources | None = None
    stadium: StadiumResources | None = None
    exits: ExitResources | None = None
    phase: str = "entry"
    """Fase actual (``PHASES``)."""


def run_replica(config: Config, seed: int) -> pd.DataFrame:
    """Simula una réplica completa (un partido) con la semilla ``seed``.

    Args:
        config: escenario ya validado (``config.load_config`` / ``load_experiment``).
        seed: semilla de la réplica; misma semilla => mismo resultado.

    Returns:
        DataFrame con una fila por espectador y columnas
        ``entities.SPECTATOR_COLUMNS`` (en ese orden). Tiempos en minutos
        respecto al inicio del partido. ``df.attrs`` contiene
        ``"incidents"`` (DataFrame con ``entities.INCIDENT_COLUMNS``),
        ``"seed"`` y ``"scenario"`` (``config.name``).
    """
    raise NotImplementedError("T1.4-C: run_replica")

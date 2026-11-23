"""Orquestación de una réplica (E0, E9).

Responsable: C.

``run_replica`` es el único punto de entrada a la simulación:

1. E0: crea ``simpy.Environment(initial_time=t_open_min * 60)``, los
   :class:`~sanmames.rng.RngStreams` de la semilla, los recursos
   (``entry``, ``stadium``, ``exit``) y los espectadores (``arrivals``);
2. lanza un proceso por espectador que encadena entrada -> asiento ->
   (permanencia) -> salida, y los procesos auxiliares (averías, cierre de
   puerta, alarma) según la configuración;
3. E9: en Inc1 corre hasta que todos se sientan o hasta ``max_sim_hours``;
4. devuelve el DataFrame de espectadores.
"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

import pandas as pd
import simpy

from .arrivals import generate_spectators
from .config import Config
from .entities import INCIDENT_COLUMNS, SPECTATOR_COLUMNS, Incident, Spectator, min_to_s
from .entry import build_entry_resources, entry_process, start_turnstile_failure_processes
from .incidents import gate_closure_process
from .rng import RngStreams
from .stadium import build_stadium_resources, seating_process

if TYPE_CHECKING:
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


def _entry_and_seating(spectator: Spectator, ctx: SimContext) -> Generator[Any, Any, None]:
    """Un único proceso conserva al espectador durante entrada y ubicación."""
    yield from entry_process(spectator, ctx)
    yield from seating_process(spectator, ctx)


def run_replica(config: Config, seed: int) -> pd.DataFrame:
    """Simula llegada -> entrada -> asiento con la semilla ``seed`` (Inc1).

    Termina al sentarse el último espectador o al alcanzar ``max_sim_hours``
    desde la apertura. Si se alcanza ese límite, conserva todos los espectadores
    y deja en NaN los sucesos pendientes. Admite FIFO/prioridad, conflictos I1,
    averías I3 y cierre I4. I2 y emergencia siguen pendientes y se rechazan
    explícitamente. La permanencia y salida se integran en T3.3.

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
    if config.incidents.read_failure.enabled:
        raise NotImplementedError("Fallo de lectura I2 pendiente de T2.2; desactiva read_failure")
    if config.emergency.enabled:
        raise NotImplementedError("Evacuación pendiente de Inc4; desactiva emergency.enabled")
    env = simpy.Environment(initial_time=min_to_s(config.t_open_min))
    ctx = SimContext(env=env, config=config, rngs=RngStreams(seed))
    ctx.entry = build_entry_resources(ctx)
    start_turnstile_failure_processes(ctx)
    env.process(gate_closure_process(ctx))
    ctx.stadium = build_stadium_resources(ctx)
    ctx.spectators = generate_spectators(config, ctx.rngs)

    # D16/D18: la lista viene ordenada por llegada e id. Cada proceso espera
    # por sí mismo hasta la llegada y usa los tiempos aleatorios de su espectador.
    journeys = [env.process(_entry_and_seating(sp, ctx)) for sp in ctx.spectators]
    finished = env.all_of(journeys)
    time_limit = env.timeout(min_to_s(config.max_sim_hours * 60))
    env.run(until=finished | time_limit)

    df = pd.DataFrame([asdict(sp) for sp in ctx.spectators], columns=SPECTATOR_COLUMNS)
    df.attrs["incidents"] = pd.DataFrame(
        [asdict(incident) for incident in ctx.incidents], columns=INCIDENT_COLUMNS
    )
    df.attrs["seed"] = seed
    df.attrs["scenario"] = config.name
    return df

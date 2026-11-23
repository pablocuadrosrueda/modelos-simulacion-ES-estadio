"""Entidades del modelo (memoria §4.1).

Responsable: A.

* :class:`Spectator`: entidad principal. Una fila del DataFrame de resultados
  por espectador; las columnas están en :data:`SPECTATOR_COLUMNS` y se
  describen en ``docs/CONTRATOS.md``.
* :class:`Incident`: registro auxiliar de cada incidencia I1-I4.

Convención de tiempos: todos los ``t_*`` son **minutos respecto al inicio del
partido** (t = 0; apertura de puertas en t = -90). ``NaN`` = el suceso no ha
ocurrido (p. ej. ``t_safe`` fuera de una evacuación).
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass

NAN = math.nan

TIERS = ("lower", "upper")
INCIDENT_KINDS = ("I1", "I2", "I3", "I4")


@dataclass
class Spectator:
    """Espectador individual. Sus atributos determinan ruta, prioridad y tiempos."""

    # -- atributos asignados al generarlo (arrivals.py) ---------------------
    id: int
    zone: str
    """Macrozona (A, B, C, D)."""
    gate: int
    """Puerta asignada dentro de la macrozona (1..gates_per_zone)."""
    block: int
    """Bloque de grada dentro de la macrozona (1..blocks_per_zone)."""
    tier: str
    """``"lower"`` (bloques 1-5) o ``"upper"`` (6-10)."""
    group: str
    """Clave de ``Config.groups``: standard, elderly, reduced_mobility."""
    speed_mps: float
    """Velocidad de marcha ya multiplicada por el factor del grupo."""
    distance_m: float
    """Distancia puerta -> asiento; se reutiliza para salir."""
    t_arrival: float
    """Llegada a la cola de su puerta (E1)."""
    service_s: float
    """Tiempo de servicio en torno (s), ya sorteado: Triangular(``service_time_s``).
    Se fija al generarlo para que sea el mismo en todos los escenarios (D17)."""

    # -- rellenados durante la simulación ---------------------------------
    gate_used: int = -1
    """Puerta por la que entra realmente (difiere de ``gate`` si hubo redirección)."""
    t_start_control: float = NAN
    """Inicio del control en torno (E2)."""
    t_end_control: float = NAN
    """Fin del control (E3)."""
    read_failure: bool = False
    """Hubo relectura (I2)."""
    t_vomitory: float = NAN
    """Llegada a la cola del vomitorio de su bloque."""
    t_seated: float = NAN
    """Se sienta (E4)."""
    conflict: bool = False
    """Tuvo conflicto por asiento (I1)."""
    late: bool = False
    """Llegó antes de t=0 y se sentó después de t=0."""
    exit_id: int = -1
    """Salida usada dentro de su macrozona (1..exits_per_zone)."""
    t_exit_queue: float = NAN
    """Llegada a la cola de la salida."""
    t_exit: float = NAN
    """Atraviesa la salida en la salida ordinaria (E6)."""
    abandoned: bool = False
    """Estaba en una cola exterior al sonar la alarma y abandona (no cuenta en evacuación)."""
    t_safe: float = NAN
    """Llega a zona segura en la evacuación (E8)."""


SPECTATOR_COLUMNS: list[str] = [f.name for f in dataclasses.fields(Spectator)]
"""Columnas, en orden, del DataFrame que devuelve ``runner.run_replica``."""


@dataclass
class Incident:
    """Registro de una incidencia (para contar cuántas hay y cuánto duran)."""

    kind: str
    """I1 conflicto, I2 fallo de lectura, I3 avería de torno, I4 cierre de puerta."""
    zone: str
    resource: str
    """Recurso afectado, p. ej. ``"A-G1-T2"`` (torno), ``"A-B3"`` (vomitorio), ``"A-G1"``."""
    t_start: float
    t_end: float = NAN
    spectator_id: int = -1
    """Espectador implicado (I1, I2); -1 si no aplica (I3, I4)."""


INCIDENT_COLUMNS: list[str] = [f.name for f in dataclasses.fields(Incident)]
"""Columnas del DataFrame de incidencias (``df.attrs["incidents"]``)."""


def gate_label(zone: str, gate: int) -> str:
    """Identificador legible de una puerta: ``"A-G1"``."""
    return f"{zone}-G{gate}"


def block_label(zone: str, block: int) -> str:
    """Identificador legible de un bloque/vomitorio: ``"A-B3"``."""
    return f"{zone}-B{block}"


def exit_label(zone: str, exit_id: int) -> str:
    """Identificador legible de una salida: ``"A-S2"``."""
    return f"{zone}-S{exit_id}"


# --------------------------------------------------------------------------
# Reloj
# --------------------------------------------------------------------------
# El reloj de SimPy (env.now) va en SEGUNDOS con t = 0 en el inicio del partido:
# el entorno se crea con ``simpy.Environment(initial_time=config.t_open_min * 60)``.


def min_to_s(t_min: float) -> float:
    """Minutos (respecto al inicio) -> segundos de reloj SimPy."""
    return t_min * 60.0


def s_to_min(t_s: float) -> float:
    """Segundos de reloj SimPy -> minutos respecto al inicio (para los resultados)."""
    return t_s / 60.0

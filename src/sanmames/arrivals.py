"""Generación de espectadores y horas de llegada (E0, RF02).

Responsable: A.

Memoria §3.1 (Fase A, pasos 1-2) y §4.3:

* hora de llegada: se sortea la franja de 15 min con las probabilidades del
  perfil activo y un instante uniforme dentro de ella (flujo ``"arrivals"``);
* macrozona según ``zone_share``; puerta y bloque equiprobables dentro de la
  macrozona (flujo ``"assignment"``);
* grupo según ``groups.*.share`` (flujo ``"group"``);
* velocidad Normal(1,45; 0,23) truncada en [0,6; 2,2] x factor del grupo
  (flujo ``"speed"``);
* distancia Uniforme(60, 180) m (flujo ``"distance"``).
"""

from __future__ import annotations

import numpy as np

from .config import ArrivalBin, Config, TruncNormal
from .entities import Spectator
from .rng import RngStreams


def sample_arrival_times(
    profile: tuple[ArrivalBin, ...], n: int, rng: np.random.Generator
) -> np.ndarray:
    """Devuelve ``n`` horas de llegada (min respecto al inicio), ordenadas o no.

    Args:
        profile: franjas del perfil activo (``config.active_profile``).
        n: número de espectadores.
        rng: generador del flujo ``"arrivals"``.
    """
    raise NotImplementedError("T1.1-A: sample_arrival_times")


def sample_truncated_normal(params: TruncNormal, n: int, rng: np.random.Generator) -> np.ndarray:
    """``n`` muestras de una normal truncada en ``[params.min, params.max]``."""
    raise NotImplementedError("T1.1-A: sample_truncated_normal")


def generate_spectators(config: Config, rngs: RngStreams) -> list[Spectator]:
    """Crea los ``config.n_spectators`` espectadores con sus atributos iniciales.

    Los campos que se rellenan durante la simulación quedan con su valor por
    defecto. ``id`` va de 0 a N-1. Debe ser determinista dada la semilla.
    """
    raise NotImplementedError("T1.1-A: generate_spectators")

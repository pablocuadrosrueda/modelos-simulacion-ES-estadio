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

Cada atributo sale de su propio flujo y se sortea vectorizado para los N
espectadores, de modo que cambiar un parámetro (p. ej. el perfil en X2) no
desplaza los números de los demás atributos (números aleatorios comunes).
Los espectadores se devuelven ordenados por hora de llegada: ``id`` crece con
``t_arrival``.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import truncnorm

from .config import ArrivalBin, Config, Triangular, TruncNormal
from .entities import Spectator
from .rng import RngStreams


def _choice(rng: np.random.Generator, n: int, probs: list[float] | tuple[float, ...]) -> np.ndarray:
    """``n`` índices 0..k-1 según ``probs`` (renormalizadas: la config tolera 1e-6)."""
    p = np.asarray(probs, dtype=float)
    return rng.choice(len(p), size=n, p=p / p.sum())


def sample_arrival_times(
    profile: tuple[ArrivalBin, ...], n: int, rng: np.random.Generator
) -> np.ndarray:
    """Devuelve ``n`` horas de llegada (min respecto al inicio), sin ordenar.

    Para cada espectador se sortea la franja con las probabilidades del perfil y
    un instante uniforme dentro de ella, ``[start_min, end_min)``.

    Args:
        profile: franjas del perfil activo (``config.active_profile``).
        n: número de espectadores.
        rng: generador del flujo ``"arrivals"``.
    """
    bins = _choice(rng, n, [b.prob for b in profile])
    start = np.array([b.start_min for b in profile])[bins]
    end = np.array([b.end_min for b in profile])[bins]
    return rng.uniform(start, end)


def sample_truncated_normal(params: TruncNormal, n: int, rng: np.random.Generator) -> np.ndarray:
    """``n`` muestras de una normal truncada en ``[params.min, params.max]``.

    Por inversión de la función de distribución: consume exactamente ``n``
    uniformes del flujo (sin rechazo), lo que mantiene alineados los números
    aleatorios comunes. Con ``sd == 0`` devuelve la media recortada al rango.
    """
    if params.sd == 0:
        return np.full(n, float(np.clip(params.mean, params.min, params.max)))
    a = (params.min - params.mean) / params.sd
    b = (params.max - params.mean) / params.sd
    u = rng.random(n)
    x = truncnorm.ppf(u, a, b, loc=params.mean, scale=params.sd)
    return np.clip(x, params.min, params.max)  # por redondeo en las colas


def sample_service_times(params: Triangular, n: int, rng: np.random.Generator) -> np.ndarray:
    """``n`` tiempos de servicio (s) ~ Triangular(low, mode, high).

    Consume exactamente ``n`` números del flujo. Admite la triangular degenerada
    (``low == high``), que numpy rechaza.
    """
    if params.low == params.high:
        return np.full(n, float(params.low))
    return rng.triangular(params.low, params.mode, params.high, size=n)


def generate_spectators(config: Config, rngs: RngStreams) -> list[Spectator]:
    """Crea los ``config.n_spectators`` espectadores con sus atributos iniciales.

    Los campos que se rellenan durante la simulación quedan con su valor por
    defecto. ``id`` va de 0 a N-1 en orden de llegada. Determinista dada la
    semilla.
    """
    n = config.n_spectators

    t_arrival = np.sort(sample_arrival_times(config.active_profile, n, rngs["arrivals"]))

    assign = rngs["assignment"]
    zone_idx = _choice(assign, n, config.zone_share)
    gates = assign.integers(1, config.gates_per_zone + 1, size=n)
    blocks = assign.integers(1, config.blocks_per_zone + 1, size=n)

    group_names = list(config.groups)
    group_idx = _choice(rngs["group"], n, [config.groups[g].share for g in group_names])
    factors = np.array([config.groups[g].speed_factor for g in group_names])[group_idx]

    speeds = sample_truncated_normal(config.speed_mps, n, rngs["speed"]) * factors
    distances = rngs["distance"].uniform(config.distance_m.low, config.distance_m.high, size=n)
    services = sample_service_times(config.service_time_s, n, rngs["service"])

    return [
        Spectator(
            id=i,
            zone=config.zones[zone_idx[i]],
            gate=int(gates[i]),
            block=int(blocks[i]),
            tier=config.tier_of_block(int(blocks[i])),
            group=group_names[group_idx[i]],
            speed_mps=float(speeds[i]),
            distance_m=float(distances[i]),
            t_arrival=float(t_arrival[i]),
            service_s=float(services[i]),
        )
        for i in range(n)
    ]

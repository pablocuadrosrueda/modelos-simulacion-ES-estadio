"""Comprobación previa de capacidad (memoria §4.3), sin simulación.

Responsable: A (T2.1).

Cálculos analíticos a partir de una :class:`~sanmames.config.Config`, para
contrastar el modelo con la memoria y servir de referencia a la verificación
por simulación (``docs/VERIFICACION.md``). Todo sale de la configuración: no
hay números del modelo en el código.

Unidades: segundos para tiempos de servicio y paso, personas/min para ritmos.
"""

from __future__ import annotations

from .config import ArrivalBin, Config


def mean_service_s(config: Config, *, with_read_failure: bool | None = None) -> float:
    """Servicio medio por persona en el torno, E[S] (s).

    Triangular(``service_time_s``) más, si I2 cuenta, ``prob × media(extra_s)``
    (la relectura ocupa el torno, D26). Por defecto I2 cuenta si está activa.
    """
    rf = config.incidents.read_failure
    use_rf = rf.enabled if with_read_failure is None else with_read_failure
    extra = rf.prob * rf.extra_s.mean if use_rf else 0.0
    return config.service_time_s.mean + extra


def turnstile_availability(config: Config, *, with_failures: bool | None = None) -> float:
    """Fracción del tiempo que un torno funciona: ``mtbf / (mtbf + media reparación)``.

    Coherente con D22 (el tiempo entre fallos se mide en funcionamiento). Vale 1
    si I3 no cuenta. Por defecto I3 cuenta si está activa.
    """
    tf = config.incidents.turnstile_failure
    use_tf = tf.enabled if with_failures is None else with_failures
    if not use_tf:
        return 1.0
    return tf.mtbf_min / (tf.mtbf_min + tf.repair_min.mean)


def capacity_per_turnstile_min(
    config: Config, *, with_read_failure: bool | None = None, with_failures: bool | None = None
) -> float:
    """Personas/min que atiende un torno siempre ocupado: ``60 / E[S] × disponibilidad``."""
    return (
        60.0
        / mean_service_s(config, with_read_failure=with_read_failure)
        * turnstile_availability(config, with_failures=with_failures)
    )


def total_capacity_min(config: Config, **kw: bool | None) -> float:
    """Capacidad de todos los tornos del estadio (personas/min)."""
    return config.n_turnstiles * capacity_per_turnstile_min(config, **kw)


def peak_bin(config: Config) -> ArrivalBin:
    """Franja del perfil activo con más llegadas por minuto."""
    return max(config.active_profile, key=lambda b: b.prob / (b.end_min - b.start_min))


def peak_arrival_rate_min(config: Config) -> float:
    """λ en la franja más cargada del perfil activo (personas/min, todo el estadio)."""
    b = peak_bin(config)
    return config.n_spectators * b.prob / (b.end_min - b.start_min)


def traffic_intensity(config: Config, **kw: bool | None) -> float:
    """ρ = λ_pico / capacidad total de los tornos (> 1: la cola crece en la punta)."""
    return peak_arrival_rate_min(config) / total_capacity_min(config, **kw)


def zone_turnstile_capacity_min(config: Config, **kw: bool | None) -> float:
    """Personas/min que dejan pasar los tornos de una macrozona."""
    return (
        config.gates_per_zone
        * config.turnstiles_per_gate
        * capacity_per_turnstile_min(config, **kw)
    )


def zone_vomitory_capacity_min(config: Config) -> float:
    """Personas/min que admiten los vomitorios de una macrozona.

    ``blocks_per_zone × vomitory_capacity`` plazas, cada una ocupada en media
    ``media(vomitory_pass_s)`` segundos (sin conflictos I1).
    """
    places = config.blocks_per_zone * config.vomitory_capacity
    return places * 60.0 / config.vomitory_pass_s.mean


def zone_exit_time_min(
    config: Config, *, evacuation: bool = False, blocked_exit: bool = False
) -> float:
    """Minutos que tarda una macrozona en cruzar sus salidas a pleno ritmo.

    ``(N / nº zonas) / (salidas × anchura × ritmo)``. En evacuación la anchura
    efectiva se multiplica por ``emergency.exit_width_factor``; con salida
    bloqueada queda una salida menos en la zona.
    """
    exits = config.exits_per_zone - (1 if blocked_exit else 0)
    width = config.exit_width_m * (config.emergency.exit_width_factor if evacuation else 1.0)
    rate = exits * width * config.exit_rate_per_m_min
    return config.n_spectators / len(config.zones) / rate

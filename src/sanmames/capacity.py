"""Comprobación previa de capacidad (memoria §4.3), sin simulación.

Responsable: A (T2.1).

Cálculos analíticos a partir de una :class:`~sanmames.config.Config`, para
contrastar el modelo con la memoria y servir de referencia a la verificación
por simulación (``docs/VERIFICACION.md``). Todo sale de la configuración: no
hay números del modelo en el código.

Unidades: segundos para tiempos de servicio y paso, personas/min para ritmos.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

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


# =============================================================================
# Modelo fluido de una puerta (T6.2)
# =============================================================================
#
# Aproximación determinista de la cola: llegadas y servicios como caudales
# continuos (personas/min). Ignora la variabilidad, así que con ρ < 1 da espera
# nula; con ρ > 1 da el orden de magnitud y la forma (crecimiento lineal de la
# espera a ritmo ρ − 1 en la punta). Sirve para contrastar la simulación con ρ.

FLUID_STEP_MIN = 0.01
"""Paso de integración del modelo fluido (min). Precisión numérica, no del modelo."""


def fluid_waits(
    t: Sequence[float], arrival_rate: Sequence[float], service_rate: Sequence[float]
) -> tuple[np.ndarray, np.ndarray]:
    """Cola fluida FIFO en una rejilla uniforme ``t`` (min).

    ``arrival_rate[i]`` y ``service_rate[i]`` son caudales (pers/min) en
    ``[t[i], t[i+1])``. Devuelve ``(cola, espera)``: personas en cola al inicio de
    cada paso y minutos que espera quien llega en ese instante (hasta que la
    salida acumulada alcanza su llegada acumulada). La capacidad puede ser 0 (puerta
    cerrada). Si la cola no se vacía antes del final de la rejilla, la espera de
    los últimos es ``inf``.
    """
    t = np.asarray(t, dtype=float)
    lam = np.asarray(arrival_rate, dtype=float)
    mu = np.asarray(service_rate, dtype=float)
    dt = np.diff(t)
    queue = np.zeros(len(t))
    served = np.zeros(len(t))
    for i, h in enumerate(dt):
        out = min(mu[i] * h, queue[i] + lam[i] * h)
        queue[i + 1] = queue[i] + lam[i] * h - out
        served[i + 1] = served[i] + out
    # Quien llega en el paso i es el último de ``arrived[i + 1]``: sale cuando la
    # salida acumulada lo alcanza (tolerancia numérica de la suma en coma flotante).
    arrived = served + queue
    idx = np.searchsorted(served, arrived[1:] - 1e-9, side="left")
    wait = np.full(len(t), np.inf)
    ok = np.flatnonzero(idx < len(t))
    wait[ok] = t[idx[ok]] - t[ok + 1]
    wait[-1] = wait[-2] if len(t) > 1 else 0.0
    return queue, np.maximum(wait, 0.0)


def _gate_grid(config: Config, tail_min: float) -> tuple[np.ndarray, np.ndarray]:
    """Rejilla y caudal de llegadas a una puerta (reparto uniforme) con el perfil activo."""
    profile = config.active_profile
    start, end = profile[0].start_min, profile[-1].end_min + tail_min
    t = np.arange(start, end + FLUID_STEP_MIN / 2, FLUID_STEP_MIN)
    per_gate = config.n_spectators / (len(config.zones) * config.gates_per_zone)
    lam = np.zeros(len(t))
    for b in profile:
        lam[(t >= b.start_min) & (t < b.end_min)] = per_gate * b.prob / (b.end_min - b.start_min)
    return t, lam


def fluid_entry_wait(config: Config, *, tail_min: float = 120.0) -> dict[str, float]:
    """Espera media y máxima (min) del modelo fluido en una puerta típica.

    Caudal por puerta = λ(t) / (zonas × puertas); capacidad =
    ``turnstiles_per_gate × capacity_per_turnstile_min``. ``tail_min`` alarga la
    rejilla tras la última franja para que la cola se vacíe.
    """
    t, lam = _gate_grid(config, tail_min)
    mu = np.full(len(t), config.turnstiles_per_gate * capacity_per_turnstile_min(config))
    _, wait = fluid_waits(t, lam, mu)
    weights = lam * FLUID_STEP_MIN
    return {
        "wait_mean_min": float(np.sum(wait * weights) / np.sum(weights)),
        "wait_max_min": float(np.max(wait[lam > 0])),
    }


def fluid_closure_wait(config: Config, *, redirect: bool, tail_min: float = 120.0) -> float:
    """Espera media fluida (min) de quien llega a la puerta cerrada durante el cierre I4.

    Sin redirección la puerta tiene capacidad 0 durante ``duration_min`` y la cola
    acumulada se atiende después en orden (D13). Con redirección esas llegadas se
    reparten por igual entre las demás puertas de la macrozona (equivale a «la de
    menos cola» en el límite fluido, D23) y se mide su espera allí.
    """
    gc = config.incidents.gate_closure
    t, lam = _gate_grid(config, tail_min)
    closed = (t >= gc.start_min) & (t < gc.start_min + gc.duration_min)
    mu_gate = config.turnstiles_per_gate * capacity_per_turnstile_min(config)
    if redirect:
        others = config.gates_per_zone - 1
        lam_eff = np.where(closed, lam * (others + 1) / others, lam)
        mu = np.full(len(t), mu_gate)
    else:
        lam_eff = lam
        mu = np.where(closed, 0.0, mu_gate)
    _, wait = fluid_waits(t, lam_eff, mu)
    w = lam * closed
    return float(np.sum(wait * w) / np.sum(w))


def busy_rate_per_turnstile(df: pd.DataFrame, config: Config, min_len: float = 5.0) -> float:
    """Servicios por torno y minuto observados en una réplica mientras hay cola.

    Une por puerta usada los intervalos ``[t_arrival, t_start_control)`` con espera
    y cuenta los fines de control dentro de los periodos de cola de ``min_len`` min
    o más (en los cortos domina el efecto de borde: cada periodo acaba en un fin).
    Con cola sostenida debe acercarse a :func:`capacity_per_turnstile_min`. NaN si
    no hay periodos de cola largos.
    """
    done, busy = 0, 0.0
    for _, d in df.groupby(["zone", "gate_used"]):
        waits = sorted(
            (a, b) for a, b in zip(d.t_arrival, d.t_start_control, strict=True) if b - a > 1e-9
        )
        merged: list[list[float]] = []
        for a, b in waits:
            if merged and a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        ends = np.sort(d.t_end_control.to_numpy())
        for a, b in merged:
            if b - a >= min_len:
                busy += b - a
                done += int(np.searchsorted(ends, b) - np.searchsorted(ends, a, side="right"))
    return done / (busy * config.turnstiles_per_gate) if busy else float("nan")

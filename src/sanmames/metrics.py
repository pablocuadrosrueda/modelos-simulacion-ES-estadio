"""KPIs por réplica (memoria §2.2 y §4.4).

Responsable: C.

``compute_kpis`` recibe el DataFrame de una réplica (una fila por espectador,
columnas ``entities.SPECTATOR_COLUMNS``) y devuelve un dict con las claves de
:data:`KPI_COLUMNS`. Las definiciones exactas están en ``docs/CONTRATOS.md``.
Un KPI que no aplica al escenario (p. ej. evacuación sin emergencia) vale NaN.

Los estadísticos ponderados en el tiempo (cola máxima, utilización) se
reconstruyen a partir de los instantes de cada espectador, de modo que el
DataFrame es autosuficiente.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from .config import Config

ID_COLUMNS: list[str] = ["experiment", "scenario", "replica", "seed"]
"""Columnas identificativas de cada fila de la tabla de KPIs (las añade experiments.py)."""

KPI_COLUMNS: list[str] = [
    "n_spectators",  # espectadores simulados
    "n_entered",  # pasan el torno
    "wait_mean_min",  # P1-P4, P7: media de t_start_control - t_arrival
    "wait_p95_min",  # P1-P4, P7: percentil 95 de la espera
    "pct_wait_lt_10",  # P2: % con espera < 10 min
    "queue_max_gate",  # P1, P7: máximo de personas en cola en una misma puerta
    "turnstile_util",  # P1, P2: tiempo ocupado / tiempo disponible (0-1)
    "access_mean_min",  # media de t_seated - t_arrival
    "late_pct",  # P1-P4, P6: % de t_arrival < 0 que se sientan con t_seated > 0
    "wait_mean_priority_min",  # P4: espera media de priority_groups
    "wait_mean_rest_min",  # P4: espera media del resto
    "group_wait_diff_min",  # P4: priorizados - resto
    "conflict_delay_s",  # P6: espera extra en vomitorios con conflicto vs sin
    "n_conflicts",  # I1
    "n_read_failures",  # I2
    "n_turnstile_failures",  # I3
    "exit_time_min",  # P5: última t_exit - t_end_min
    "exit_queue_max",  # P5: máximo de personas en cola en una misma salida
    "evac_time_min",  # P8: última t_safe - alarm_min
    "evac_pct_ref",  # P8: % de evacuables en zona segura a los reference_min
    "n_abandoned",  # P8: en cola exterior al sonar la alarma
]
"""Columnas de KPIs que devuelve :func:`compute_kpis` (en este orden)."""


def queue_length_max(start: pd.Series, end: pd.Series) -> int:
    """Máximo de elementos simultáneamente en ``[start, end)`` (cola reconstruida).

    Útil para la cola de una puerta (``t_arrival``, ``t_start_control``) o de
    una salida (``t_exit_queue``, ``t_exit``). Empareja las series por posición.
    Ignora filas con NaN en ``start``. Si ``end`` es NaN, el elemento sigue
    esperando. Una espera de duración cero no ocupa cola; en un empate de
    tiempos, las salidas se procesan antes que las llegadas.
    """
    events: list[tuple[float, int]] = []
    for arrival, departure in zip(start, end, strict=True):
        if pd.isna(arrival):
            continue
        if pd.notna(departure):
            if departure < arrival:
                raise ValueError("El fin de una espera no puede preceder a su inicio")
            if departure == arrival:
                continue
            events.append((departure, -1))
        events.append((arrival, 1))

    queued = peak = 0
    for _, change in sorted(events):
        queued += change
        peak = max(peak, queued)
    return peak


def compute_kpis(df: pd.DataFrame, config: Config) -> dict[str, Any]:
    """Calcula los KPIs de entrada de una réplica (T1.5).

    Los indicadores de grupos, incidencias, salida y evacuación quedan en
    NaN hasta sus tareas correspondientes. Las medias de espera y acceso usan
    los tiempos observados, sin convertir los sucesos pendientes en ceros.
    Sin observaciones, las medias y porcentajes son NaN; los recuentos y la
    cola máxima son cero. La utilización requiere algún control terminado.

    Args:
        df: resultado de ``runner.run_replica`` (columnas ``SPECTATOR_COLUMNS``;
            ``df.attrs["incidents"]`` con las incidencias).
        config: configuración con la que se generó ``df``.

    Returns:
        dict con exactamente las claves de :data:`KPI_COLUMNS`.
    """
    kpis: dict[str, Any] = dict.fromkeys(KPI_COLUMNS, math.nan)
    kpis["n_spectators"] = len(df)
    kpis["n_entered"] = int(df["t_end_control"].notna().sum())

    # Los tiempos del DataFrame ya están en minutos (no son el reloj SimPy).
    waits = (df["t_start_control"] - df["t_arrival"]).dropna()
    if not waits.empty:
        kpis["wait_mean_min"] = float(waits.mean())
        kpis["wait_p95_min"] = float(waits.quantile(0.95))
        kpis["pct_wait_lt_10"] = float((waits < 10).mean() * 100)

    # Las puertas se numeran dentro de cada macrozona: A-G1 y B-G1 son distintas.
    kpis["queue_max_gate"] = max(
        (
            queue_length_max(gate["t_arrival"], gate["t_start_control"])
            for _, gate in df.groupby(["zone", "gate"])
        ),
        default=0,
    )

    service = df["t_end_control"] - df["t_start_control"]
    control_window = df["t_end_control"].max() - config.t_open_min
    if service.notna().any() and control_window > 0:
        # D12: todos los tornos nominales, desde apertura hasta el último control.
        kpis["turnstile_util"] = float(service.sum() / (config.n_turnstiles * control_window))

    access = (df["t_seated"] - df["t_arrival"]).dropna()
    if not access.empty:
        kpis["access_mean_min"] = float(access.mean())

    before_kickoff = df["t_arrival"] < config.t_start_min
    if before_kickoff.any():
        kpis["late_pct"] = float(
            (df.loc[before_kickoff, "t_seated"] > config.t_start_min).mean() * 100
        )
    return kpis

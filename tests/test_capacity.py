"""T2.1 · Comprobación de capacidad (memoria §4.3) y casos límite (§5.3).

Parte A: analítica, sin simulación (``sanmames.capacity``).
Parte B: con ``run_replica`` y ``compute_kpis``, en una macrozona (N/4) para que
sea rápida; la réplica completa (N = 48.775) solo con ``RUN_SLOW=1``.

Hasta que el runner admita I2 (hoy lanza ``NotImplementedError``), la parte B
desactiva el fallo de lectura y compara con el teórico sin I2.
"""

from __future__ import annotations

import os
import time
from typing import Any

import numpy as np
import pandas as pd
import pytest

from sanmames import capacity as cap
from sanmames.config import Config, deep_merge, load_config
from sanmames.metrics import compute_kpis
from sanmames.runner import run_replica

SEEDS = (20261105, 20261106, 20261107)


def cfg_with(**overrides: Any) -> Config:
    return load_config(overrides=overrides)


# =============================================================================
# Parte A · analítica
# =============================================================================


def test_mean_service_with_and_without_read_failure(base_config: Config) -> None:
    assert cap.mean_service_s(base_config) == pytest.approx(4.3)
    assert cap.mean_service_s(base_config, with_read_failure=False) == pytest.approx(4.0)


def test_turnstile_availability(base_config: Config) -> None:
    assert cap.turnstile_availability(base_config) == pytest.approx(0.974, abs=5e-4)
    assert cap.turnstile_availability(base_config, with_failures=False) == 1.0


def test_capacity_per_turnstile_and_total(base_config: Config) -> None:
    assert cap.capacity_per_turnstile_min(base_config) == pytest.approx(13.6, abs=0.05)
    assert base_config.n_turnstiles == 72
    assert cap.total_capacity_min(base_config) == pytest.approx(978, abs=1)


@pytest.mark.parametrize("turnstiles, rho", [(2, 1.40), (3, 0.93), (4, 0.70)])
def test_traffic_intensity_base_profile(turnstiles: int, rho: float) -> None:
    cfg = cfg_with(turnstiles_per_gate=turnstiles)
    assert cap.traffic_intensity(cfg) == pytest.approx(rho, abs=0.005)


def test_traffic_intensity_anticipated_profile_uses_real_peak() -> None:
    # La memoria da ρ ≈ 0,65 para el perfil anticipado, pero su franja más
    # cargada es −45 a −30 (24,4 % → ≈ 793 pers/min), no −30 a −15 (19,6 %):
    # con el pico real ρ ≈ 0,81. El 0,65 es un error de la memoria, no del modelo.
    cfg = cfg_with(arrival_profile="anticipated")
    peak = cap.peak_bin(cfg)
    assert (peak.start_min, peak.end_min, peak.prob) == (-45, -30, 0.244)
    assert cap.peak_arrival_rate_min(cfg) == pytest.approx(793.4, abs=0.1)
    assert cap.traffic_intensity(cfg) == pytest.approx(0.81, abs=0.005)


def test_vomitories_do_not_bottleneck_turnstiles(base_config: Config) -> None:
    vom = cap.zone_vomitory_capacity_min(base_config)
    turn = cap.zone_turnstile_capacity_min(base_config)
    assert vom == pytest.approx(411, abs=1)
    assert turn == pytest.approx(245, abs=1)
    assert vom > turn


@pytest.mark.parametrize(
    "kw, minutes",
    [({}, 7.7), ({"evacuation": True}, 5.9), ({"evacuation": True, "blocked_exit": True}, 7.1)],
)
def test_zone_exit_time(base_config: Config, kw: dict[str, bool], minutes: float) -> None:
    assert cap.zone_exit_time_min(base_config, **kw) == pytest.approx(minutes, abs=0.05)


# =============================================================================
# Parte B · simulación (una macrozona, N/4)
# =============================================================================

ONE_ZONE = {"zones": ["A"], "zone_share": [1.0], "n_spectators": 12194}
NO_I2 = {"incidents": {"read_failure": {"enabled": False}}}
NO_INCIDENTS = {
    "incidents": {
        "read_failure": {"enabled": False},
        "turnstile_failure": {"enabled": False},
        "seat_conflict": {"enabled": False},
    }
}


def zone_cfg(turnstiles: int, incidents: dict[str, Any] = NO_I2, **extra: Any) -> Config:
    return load_config(
        overrides=deep_merge(
            deep_merge(ONE_ZONE, incidents), {"turnstiles_per_gate": turnstiles, **extra}
        )
    )


def busy_rate_per_turnstile(df: pd.DataFrame, cfg: Config, min_len: float = 5.0) -> float:
    """Servicios por torno y minuto mientras hay cola en la puerta.

    Une los intervalos ``[t_arrival, t_start_control)`` con espera de cada puerta y
    cuenta los fines de control dentro. Solo periodos de cola de ``min_len`` min o
    más: en los cortos domina el efecto de borde (cada periodo acaba en un fin).
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
    assert busy > 0, "no hay periodos de cola largos"
    return done / (busy * cfg.turnstiles_per_gate)


def test_zone_and_group_shares() -> None:
    cfg = load_config(overrides=deep_merge(NO_I2, {"n_spectators": 4000}))
    df = run_replica(cfg, SEEDS[0])
    zones = df.zone.value_counts(normalize=True)
    for z, share in zip(cfg.zones, cfg.zone_share, strict=True):
        assert zones[z] == pytest.approx(share, abs=0.03)
    groups = df.group.value_counts(normalize=True)
    for g, params in cfg.groups.items():
        assert groups.get(g, 0.0) == pytest.approx(params.share, abs=0.015)


@pytest.mark.parametrize(
    "incidents, with_failures", [(NO_I2, True), (NO_INCIDENTS, False)], ids=["I3", "sin"]
)
def test_service_rate_with_queue_matches_theory(
    incidents: dict[str, Any], with_failures: bool
) -> None:
    """Con 2 tornos (ρ > 1) hay cola sostenida: el ritmo observado ≈ el teórico."""
    cfg = zone_cfg(2, incidents)
    theory = cap.capacity_per_turnstile_min(cfg, with_failures=with_failures)
    rates = [busy_rate_per_turnstile(run_replica(cfg, s), cfg) for s in SEEDS[:2]]
    assert np.mean(rates) == pytest.approx(theory, rel=0.03)


def test_many_turnstiles_no_queue() -> None:
    cfg = zone_cfg(10, NO_INCIDENTS)
    k = compute_kpis(run_replica(cfg, SEEDS[0]), cfg)
    assert k["wait_p95_min"] < 0.01
    assert k["pct_wait_lt_10"] == 100.0


def test_capacity_ordering_2_3_4_turnstiles() -> None:
    """X1 en una macrozona: con 2 tornos la cola crece; con 4, esperas pequeñas."""
    k = {t: compute_kpis(run_replica(zone_cfg(t), SEEDS[0]), zone_cfg(t)) for t in (2, 3, 4)}
    assert k[2]["wait_p95_min"] > 5.0  # ρ ≈ 1,30 sin I2; ver ESTADO (p95 > 10 con I2)
    assert k[2]["wait_p95_min"] > k[3]["wait_p95_min"] > k[4]["wait_p95_min"]
    assert k[4]["wait_p95_min"] < 0.2
    assert k[2]["turnstile_util"] > k[3]["turnstile_util"] > k[4]["turnstile_util"]


def test_utilization_matches_offered_load() -> None:
    """D12: U = trabajo ofrecido / (c · T), T desde la apertura al último fin de control."""
    cfg = zone_cfg(3)
    df = run_replica(cfg, SEEDS[0])
    k = compute_kpis(df, cfg)
    window = df.t_end_control.max() - cfg.t_open_min
    offered = len(df) * cap.mean_service_s(cfg) / 60
    assert k["turnstile_util"] == pytest.approx(offered / (cfg.n_turnstiles * window), rel=0.02)
    assert k["turnstile_util"] < cap.traffic_intensity(cfg)


@pytest.mark.xfail(
    strict=True, raises=NotImplementedError, reason="runner aún rechaza I2 (C, ver AVISOS)"
)
def test_full_x0_with_all_incidents_runs() -> None:
    cfg = load_config(overrides={"n_spectators": 2000})
    assert cfg.incidents.read_failure.enabled
    run_replica(cfg, SEEDS[0])


@pytest.mark.skipif(not os.environ.get("RUN_SLOW"), reason="lento: RUN_SLOW=1")
def test_full_replica_wall_time() -> None:
    cfg = load_config(overrides=NO_I2)
    t0 = time.perf_counter()
    df = run_replica(cfg, SEEDS[0])
    elapsed = time.perf_counter() - t0
    assert len(df) == cfg.n_spectators
    assert elapsed < 60  # D15: holgado; el dato real va en docs/VERIFICACION.md

#!/usr/bin/env python3
"""T2.1 · Verificación de capacidad (memoria §4.3, §5.3) y tiempo de réplica (D15).

Imprime una tabla «comprobación | esperado | obtenido | ok» y los tiempos de pared.
Usa la API pública: ``load_config``, ``run_replica``, ``compute_kpis`` y las
fórmulas de ``sanmames.capacity``.

Uso::

    python scripts/validate_capacity.py            # completo (≈ 1 min)
    python scripts/validate_capacity.py --reps 3   # menos réplicas por caso
"""

from __future__ import annotations

import argparse
import platform
import resource
import subprocess
import sys
import time
from typing import Any

import numpy as np

from sanmames import capacity as cap
from sanmames.config import Config, deep_merge, load_config
from sanmames.metrics import compute_kpis
from sanmames.runner import run_replica

BASE_SEED = 20261105
NO_I2 = {"incidents": {"read_failure": {"enabled": False}}}
NO_INCIDENTS = {
    "incidents": {
        "read_failure": {"enabled": False},
        "turnstile_failure": {"enabled": False},
        "seat_conflict": {"enabled": False},
    }
}

Row = tuple[str, str, str, bool]


def row(name: str, expected: float, got: float, tol: float, fmt: str = ".3f") -> Row:
    return (name, f"{expected:{fmt}}", f"{got:{fmt}}", abs(got - expected) <= tol)


def cond(name: str, expected: str, got: str, ok: bool) -> Row:
    return (name, expected, got, ok)


def cfg(*overrides: dict[str, Any]) -> Config:
    merged: dict[str, Any] = {}
    for o in overrides:
        merged = deep_merge(merged, o)
    return load_config(overrides=merged)


def busy_rate_per_turnstile(df: Any, config: Config, min_len: float = 5.0) -> float:
    """Servicios por torno y minuto en periodos de cola de ``min_len`` min o más."""
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


def analytic_rows() -> list[Row]:
    base = load_config()
    ant = cfg({"arrival_profile": "anticipated"})
    rows = [
        row("E[S] con I2 (s)", 4.3, cap.mean_service_s(base), 0.01, ".2f"),
        row("E[S] sin I2 (s)", 4.0, cap.mean_service_s(base, with_read_failure=False), 0.01, ".2f"),
        row("Disponibilidad del torno", 0.974, cap.turnstile_availability(base), 5e-4),
        row(
            "Capacidad por torno (pers/min)",
            13.6,
            cap.capacity_per_turnstile_min(base),
            0.05,
            ".2f",
        ),
        row("Capacidad 72 tornos (pers/min)", 978, cap.total_capacity_min(base), 1, ".0f"),
    ]
    for t, rho in ((2, 1.40), (3, 0.93), (4, 0.70)):
        rows.append(
            row(
                f"ρ perfil base, {t} tornos",
                rho,
                cap.traffic_intensity(cfg({"turnstiles_per_gate": t})),
                0.005,
                ".2f",
            )
        )
    rows += [
        row("λ pico anticipado (pers/min)", 793.4, cap.peak_arrival_rate_min(ant), 0.1, ".1f"),
        row("ρ perfil anticipado (memoria: 0,65)", 0.81, cap.traffic_intensity(ant), 0.005, ".2f"),
        row(
            "Vomitorios por macrozona (pers/min)",
            411,
            cap.zone_vomitory_capacity_min(base),
            1,
            ".0f",
        ),
        row(
            "Tornos por macrozona (pers/min)", 245, cap.zone_turnstile_capacity_min(base), 1, ".0f"
        ),
        row("Vaciado de una macrozona (min)", 7.7, cap.zone_exit_time_min(base), 0.05, ".2f"),
        row(
            "Evacuación, todas las salidas (min)",
            5.9,
            cap.zone_exit_time_min(base, evacuation=True),
            0.05,
            ".2f",
        ),
        row(
            "Evacuación, una salida bloqueada (min)",
            7.1,
            cap.zone_exit_time_min(base, evacuation=True, blocked_exit=True),
            0.05,
            ".2f",
        ),
    ]
    return rows


def simulation_rows(reps: int) -> tuple[list[Row], dict[str, float]]:
    seeds = [BASE_SEED + i for i in range(reps)]
    rows: list[Row] = []
    timing: dict[str, float] = {}

    try:
        run_replica(cfg({"n_spectators": 500}), seeds[0])
        x0_ok = True
    except NotImplementedError:
        x0_ok = False
    rows.append(
        cond(
            "X0 con todas las incidencias se ejecuta",
            "sí",
            "sí" if x0_ok else "no (I2 rechazada por el runner)",
            x0_ok,
        )
    )

    x0 = load_config() if x0_ok else cfg(NO_I2)
    label = "X0" if x0_ok else "X0 sin I2"
    t0 = time.perf_counter()
    dfs = [run_replica(x0, s) for s in seeds]
    timing[f"{reps} réplicas {label} (s)"] = time.perf_counter() - t0
    kpis = [compute_kpis(df, x0) for df in dfs]
    df0 = dfs[0]

    zones = df0.zone.value_counts(normalize=True)
    worst_zone = max(abs(zones[z] - s) for z, s in zip(x0.zones, x0.zone_share, strict=True))
    rows.append(row(f"{label}: máx. desviación del 25 % por zona", 0.0, worst_zone, 0.01, ".4f"))
    groups = df0.group.value_counts(normalize=True)
    worst_group = max(abs(groups.get(g, 0.0) - p.share) for g, p in x0.groups.items())
    rows.append(row(f"{label}: máx. desviación 88/10/2 % por grupo", 0.0, worst_group, 0.01, ".4f"))

    window = np.mean([df.t_end_control.max() - x0.t_open_min for df in dfs])
    offered = x0.n_spectators * cap.mean_service_s(x0) / 60 / (x0.n_turnstiles * window)
    util = float(np.mean([k["turnstile_util"] for k in kpis]))
    rows.append(row(f"{label}: utilización (D12) vs trabajo ofrecido", offered, util, 0.01))
    rows.append(
        row(
            f"{label}: tiempo de vaciado (min; capacidad 7,7)",
            cap.zone_exit_time_min(x0),
            float(np.mean([k["exit_time_min"] for k in kpis])),
            1.0,
            ".2f",
        )
    )

    for name, inc, failures in (("con I3", NO_I2, True), ("sin incidencias", NO_INCIDENTS, False)):
        c2 = cfg(inc, {"turnstiles_per_gate": 2})
        theory = cap.capacity_per_turnstile_min(c2, with_failures=failures)
        rate = float(np.mean([busy_rate_per_turnstile(run_replica(c2, s), c2) for s in seeds[:2]]))
        rows.append(
            row(f"Ritmo por torno con cola, 2 tornos {name}", theory, rate, 0.03 * theory, ".2f")
        )

    p95: dict[int, float] = {}
    for t in (2, 3, 4, 10):
        ct = cfg(NO_INCIDENTS if t == 10 else NO_I2, {"turnstiles_per_gate": t})
        p95[t] = float(
            np.mean([compute_kpis(run_replica(ct, s), ct)["wait_p95_min"] for s in seeds[:2]])
        )
    rows += [
        cond(
            "10 tornos sin incidencias: p95 espera ≈ 0",
            "< 0,01 min",
            f"{p95[10]:.3f}",
            p95[10] < 0.01,
        ),
        cond("4 tornos: esperas pequeñas", "p95 < 0,2 min", f"{p95[4]:.3f}", p95[4] < 0.2),
        cond("3 tornos (X0 sin I2)", "p95 < 2 min", f"{p95[3]:.3f}", p95[3] < 2),
        cond(
            "2 tornos (ρ > 1): p95 espera",
            "> 10 min (con I2)",
            f"{p95[2]:.2f} (sin I2)",
            p95[2] > 10,
        ),
    ]
    timing["1 réplica (s, media)"] = timing[f"{reps} réplicas {label} (s)"] / reps
    timing["memoria pico del proceso (MB)"] = _max_rss_mb()
    return rows, timing


def _max_rss_mb() -> float:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return rss / 1e6 if sys.platform == "darwin" else rss / 1e3  # bytes en macOS, KiB en Linux


def print_table(rows: list[Row]) -> None:
    w = max(len(r[0]) for r in rows)
    print(f"| {'comprobación':<{w}} | esperado | obtenido | ok |")
    print(f"|{'-' * (w + 2)}|---|---|---|")
    for name, exp, got, ok in rows:
        print(f"| {name:<{w}} | {exp} | {got} | {'✓' if ok else '✗'} |")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reps", type=int, default=10, help="réplicas de X0 (por defecto 10)")
    args = parser.parse_args(argv)

    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    print(f"Python {platform.python_version()} · commit {commit or '?'} · {platform.platform()}\n")
    print("## Parte A · analítica\n")
    print_table(analytic_rows())
    print("\n## Parte B · simulación\n")
    rows, timing = simulation_rows(args.reps)
    print_table(rows)
    print("\n## Tiempos (D15)\n")
    for k, v in timing.items():
        print(f"* {k}: {v:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

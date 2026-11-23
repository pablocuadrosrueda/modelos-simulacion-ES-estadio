#!/usr/bin/env python3
"""Sensibilidad del instante del cierre de puerta (I4) para X6 / P7.

Recorre ``incidents.gate_closure.start_min`` (y la duración en algunos casos), con
y sin redirección, con semillas comunes (D11) sobre la base con todas sus
incidencias. Escribe una fila por réplica en ``results/estudio_x6.csv`` e imprime
tablas en Markdown con media ± semianchura del IC 95 % y la diferencia emparejada
sin − con redirección.

Usa la API pública: ``load_config``, ``run_replica``, ``compute_kpis``,
``experiments.replica_seed`` y ``analysis.confidence_interval``.

Uso::

    python scripts/study_gate_closure.py               # 5 réplicas por celda (≈ 5 min)
    python scripts/study_gate_closure.py --reps 2      # prueba rápida
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from sanmames.analysis import confidence_interval
from sanmames.config import Config, load_config
from sanmames.experiments import DEFAULT_BASE_SEED, replica_seed
from sanmames.metrics import compute_kpis
from sanmames.runner import run_replica

STARTS = (-45, -30, -20, -10, 0, 20)
LONG_STARTS = (-30, -20, -10)  # también con 20 min de cierre
DURATIONS = {10: STARTS, 20: LONG_STARTS}
OUT = Path("results/estudio_x6.csv")

# KPI -> (etiqueta, decimales)
METRICS: dict[str, tuple[str, int]] = {
    "a1_wait_mean_s": ("Espera media A-1 (s)", 0),
    "a1_wait_max_min": ("Espera máx. A-1 (min)", 1),
    "a1_pct_gt_10": ("% A-1 > 10 min", 1),
    "wait_mean_min": ("Espera media global (min)", 3),
    "wait_p95_min": ("p95 global (min)", 2),
    "queue_max_gate": ("Cola máx. puerta", 0),
    "late_pct": ("Entrada tardía (%)", 2),
    "a1_arrivals_closed": ("Llegan a A-1 en el cierre", 0),
    "a1_queue_at_close": ("En cola en A-1 al cerrar", 0),
}


def scenario_config(start: float | None, duration: float, redirect: bool) -> Config:
    """Base con el cierre en ``start`` (``None`` = sin cierre) y la redirección dada."""
    gc: dict[str, Any] = {"enabled": start is not None, "duration_min": duration}
    if start is not None:
        gc["start_min"] = start
    return load_config(
        overrides={
            "name": "sin_cierre" if start is None else f"cierre_{start:+g}_{duration:g}",
            "redirect_on_gate_closure": redirect,
            "incidents": {"gate_closure": gc},
        }
    )


def replica_row(config: Config, seed: int) -> dict[str, Any]:
    """KPIs globales de ``compute_kpis`` más los de la puerta cerrada."""
    df = run_replica(config, seed)
    kpis = compute_kpis(df, config)
    gc = config.incidents.gate_closure
    assigned = df[(df.zone == gc.zone) & (df.gate == gc.gate)]
    wait = assigned.t_start_control - assigned.t_arrival
    close, reopen = gc.start_min, gc.start_min + gc.duration_min
    return {
        "a1_wait_mean_s": float(wait.mean() * 60),
        "a1_wait_max_min": float(wait.max()),
        "a1_pct_gt_10": float((wait > 10).mean() * 100),
        "wait_mean_min": kpis["wait_mean_min"],
        "wait_p95_min": kpis["wait_p95_min"],
        "queue_max_gate": kpis["queue_max_gate"],
        "late_pct": kpis["late_pct"],
        # Cuántos llegan a esa puerta durante el cierre (los que el cierre afecta, D23)
        "a1_arrivals_closed": int(
            ((assigned.t_arrival >= close) & (assigned.t_arrival < reopen)).sum()
        ),
        # Cuántos esperaban ya en su cola al cerrarse: D23 no los detiene
        "a1_queue_at_close": int(
            ((assigned.t_arrival < close) & (assigned.t_start_control > close)).sum()
        ),
    }


def run_all(reps: int, base_seed: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    cells = [(None, 10.0)] + [(s, float(d)) for d, starts in DURATIONS.items() for s in starts]
    for start, duration in cells:
        for redirect in (False, True):
            if start is None and redirect:
                continue  # sin cierre la redirección no actúa
            cfg = scenario_config(start, duration, redirect)
            for r in range(reps):
                seed = replica_seed(base_seed, r)
                rows.append(
                    {
                        "start_min": math.nan if start is None else start,
                        "duration_min": duration,
                        "redirect": redirect,
                        "replica": r,
                        "seed": seed,
                        **replica_row(cfg, seed),
                    }
                )
            print(f"  {cfg.name} redirect={redirect}: {reps} réplicas", file=sys.stderr)
    return pd.DataFrame(rows)


def fmt(mean: float, hw: float, nd: int) -> str:
    if math.isnan(mean):
        return "—"
    return f"{mean:.{nd}f}" if math.isnan(hw) else f"{mean:.{nd}f} ± {hw:.{nd}f}"


def tables(df: pd.DataFrame) -> str:
    """Tablas Markdown: niveles por celda y diferencia emparejada sin − con."""
    out: list[str] = []
    closed = df[df.start_min.notna()]
    for duration, block in closed.groupby("duration_min"):
        out.append(f"\n### Cierre de {duration:g} min: media ± IC 95 % (sin / con redirección)\n")
        cols = ["start_min", *METRICS]
        out.append("| " + " | ".join(["inicio"] + [METRICS[m][0] for m in METRICS]) + " |")
        out.append("|" + "---|" * len(cols))
        for start, cell in block.groupby("start_min"):
            vals = []
            for m, (_, nd) in METRICS.items():
                parts = [
                    fmt(*confidence_interval(cell[cell.redirect == red][m]), nd)
                    for red in (False, True)
                ]
                vals.append(" / ".join(parts))
            out.append(f"| {start:+g} | " + " | ".join(vals) + " |")

        out.append(
            f"\n### Cierre de {duration:g} min: diferencia sin − con redirección"
            " (IC 95 %, emparejada por semilla)\n"
        )
        diff_metrics = [
            "a1_wait_mean_s",
            "a1_wait_max_min",
            "a1_pct_gt_10",
            "wait_p95_min",
            "late_pct",
        ]
        out.append("| inicio | " + " | ".join(METRICS[m][0] for m in diff_metrics) + " |")
        out.append("|" + "---|" * (len(diff_metrics) + 1))
        for start, cell in block.groupby("start_min"):
            sin = cell[~cell.redirect].set_index("seed")
            con = cell[cell.redirect].set_index("seed")
            vals = [
                fmt(*confidence_interval((sin[m] - con[m]).dropna()), METRICS[m][1])
                for m in diff_metrics
            ]
            out.append(f"| {start:+g} | " + " | ".join(vals) + " |")

    ref = df[df.start_min.isna()]
    if not ref.empty:
        out.append("\n### Referencia sin cierre\n")
        out.append(
            "| " + " | ".join(METRICS[m][0] for m in METRICS if not m.startswith("a1_arr")) + " |"
        )
        out.append("|" + "---|" * (len(METRICS) - 1))
        out.append(
            "| "
            + " | ".join(
                fmt(*confidence_interval(ref[m]), nd)
                for m, (_, nd) in METRICS.items()
                if not m.startswith("a1_arr")
            )
            + " |"
        )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reps", type=int, default=5, help="réplicas por celda (5)")
    parser.add_argument("--base-seed", type=int, default=DEFAULT_BASE_SEED)
    args = parser.parse_args(argv)

    t0 = time.perf_counter()
    df = run_all(args.reps, args.base_seed)
    OUT.parent.mkdir(exist_ok=True)
    df.to_csv(OUT, index=False)
    print(tables(df))
    print(
        f"\n{len(df)} réplicas en {time.perf_counter() - t0:.0f} s; filas en {OUT}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    np.seterr(all="ignore")
    sys.exit(main())

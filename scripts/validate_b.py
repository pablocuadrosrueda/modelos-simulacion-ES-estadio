#!/usr/bin/env python3
"""Verificación de la parte B con la simulación completa (T6.2).

Tres comprobaciones que explican los resultados de P1, P6 y P8:

1. X5 con acomodadores casi ilimitados: si la saturación de X5 se debe a los
   acomodadores, la duración media de un conflicto debe bajar a la media teórica
   de la resolución, Triangular(1, 3, 10) min, es decir, 4,67 min.
2. X7 con todas las salidas: en las réplicas de `results/final` que no vacían en
   8 min, quién llega después de los 8 min y cuánto tarda el vaciado sin contar a
   las personas de movilidad reducida.
3. X0 sin conflictos por asiento: con las mismas semillas que `results/final`,
   cuánto bajan la entrada tardía y el tiempo de acceso al quitar los
   conflictos. Diferencia emparejada por semilla (con menos sin conflictos) con
   su intervalo de confianza del 95 %.

Uso: ``python scripts/validate_b.py [--reps 5] [--x0-reps 180]``. Con los valores
por defecto tarda unos 12 minutos; ``--x0-reps 0`` omite la tercera.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from sanmames.analysis import confidence_interval
from sanmames.config import deep_merge, load_config, load_experiment
from sanmames.experiments import replica_seed
from sanmames.metrics import compute_kpis
from sanmames.runner import run_replica

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / "configs" / "experiments"
BASE_SEED = 20261105
MANY_STEWARDS = 1000


def stewards_limit(n_reps: int) -> pd.DataFrame:
    """Duración media de I1 en X5 con 6 y con muchos acomodadores por zona."""
    x5 = load_experiment(EXPERIMENTS / "X5_6acomodadores.json").configs[0]
    rows = []
    for stewards in (6, MANY_STEWARDS):
        cfg = load_config(overrides=deep_merge(x5.raw, {"stewards_per_zone": stewards}))
        for r in range(n_reps):
            df = run_replica(cfg, replica_seed(BASE_SEED, r))
            inc = df.attrs["incidents"]
            i1 = inc[inc["kind"] == "I1"]
            rows.append(
                {
                    "acomodadores": stewards,
                    "replica": r,
                    "conflictos": len(i1),
                    "duracion_media_min": (i1["t_end"] - i1["t_start"]).mean(),
                }
            )
    return pd.DataFrame(rows)


def evacuation_failures() -> pd.DataFrame:
    """Réplicas de X7 con todas las salidas que no vacían en ``reference_min``."""
    kpis = pd.read_csv(ROOT / "results" / "final" / "kpis.csv")
    cfg = load_experiment(EXPERIMENTS / "X7_todas_salidas.json").configs[0]
    em = cfg.emergency
    failed = kpis[(kpis["scenario"] == cfg.name) & (kpis["evac_time_min"] > em.reference_min)]
    rows = []
    for seed in failed["seed"].astype(int):
        df = run_replica(cfg, seed)
        ev = df[df["t_safe"].notna()].copy()
        ev["evac_min"] = ev["t_safe"] - em.alarm_min
        late = ev[ev["evac_min"] > em.reference_min]
        last = ev.loc[ev["evac_min"].idxmax()]
        rows.append(
            {
                "seed": seed,
                "vaciado_min": ev["evac_min"].max(),
                "personas_tras_ref": len(late),
                "colectivos_tras_ref": ",".join(sorted(set(late["group"]))),
                "vaciado_sin_pmr_min": ev.loc[ev["group"] != "reduced_mobility", "evac_min"].max(),
                "marcha_ultimo_min": last["distance_m"]
                / (last["speed_mps"] * em.speed_factor)
                / 60,
                "cola_y_paso_ultimo_s": (last["t_safe"] - last["t_exit_queue"]) * 60,
            }
        )
    return pd.DataFrame(rows)


def x0_without_conflicts(n_reps: int) -> pd.DataFrame:
    """X0 frente a X0 sin I1 con las mismas semillas de ``results/final``.

    Los valores con conflictos se leen de ``results/final/kpis.csv``; los
    valores sin conflictos se simulan con las mismas semillas.
    """
    kpis = pd.read_csv(ROOT / "results" / "final" / "kpis.csv")
    x0 = load_experiment(EXPERIMENTS / "X0_base.json").configs[0]
    base = kpis[kpis["scenario"] == x0.name].sort_values("replica").head(n_reps)
    off = load_config(
        overrides=deep_merge(x0.raw, {"incidents": {"seat_conflict": {"enabled": False}}})
    )
    rows = []
    for row in base.itertuples():
        kp = compute_kpis(run_replica(off, int(row.seed)), off)
        rows.append(
            {
                "seed": int(row.seed),
                "late_con": row.late_pct,
                "late_sin": kp["late_pct"],
                "access_con": row.access_mean_min,
                "access_sin": kp["access_mean_min"],
            }
        )
    return pd.DataFrame(rows)


def summarize_x0(df: pd.DataFrame) -> pd.DataFrame:
    """Media, semianchura del IC del 95 % y n de cada columna y de las diferencias."""
    cols = {
        "Entrada tardía con conflictos (%)": df["late_con"],
        "Entrada tardía sin conflictos (%)": df["late_sin"],
        "Diferencia entrada tardía (puntos)": df["late_con"] - df["late_sin"],
        "Acceso medio con conflictos (min)": df["access_con"],
        "Acceso medio sin conflictos (min)": df["access_sin"],
        "Diferencia acceso medio (min)": df["access_con"] - df["access_sin"],
    }
    rows = []
    for name, values in cols.items():
        mean, half = confidence_interval(values)
        rows.append({"indicador": name, "media": mean, "semianchura": half, "n": len(values)})
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reps", type=int, default=5, help="réplicas por nivel en X5")
    parser.add_argument(
        "--x0-reps", type=int, default=180, help="semillas de X0 sin conflictos (0 la omite)"
    )
    args = parser.parse_args()

    pd.set_option("display.width", 140)
    st = stewards_limit(args.reps)
    print("1. X5: duración media de un conflicto (min)")
    print(st.groupby("acomodadores")["duracion_media_min"].agg(["mean", "min", "max"]).round(3))
    print()
    ev = evacuation_failures()
    print(f"2. X7 con todas las salidas: {len(ev)} réplicas no vacían en 8 min")
    print(ev.round(2).to_string(index=False))
    if len(ev):
        print(
            "Máximo de personas tras 8 min:",
            int(ev["personas_tras_ref"].max()),
            "| vaciado máximo sin PMR:",
            round(ev["vaciado_sin_pmr_min"].max(), 2),
            "min",
        )
    if args.x0_reps > 0:
        print()
        x0 = x0_without_conflicts(args.x0_reps)
        print(f"3. X0 con y sin conflictos por asiento, {len(x0)} semillas de results/final")
        print(summarize_x0(x0).round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

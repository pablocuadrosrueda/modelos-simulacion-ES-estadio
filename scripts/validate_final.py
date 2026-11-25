#!/usr/bin/env python3
"""T6.2 (A) · Verificación del modelo de entrada y capacidad frente a ``results/final``.

Lee los datos definitivos de T5.3 **sin modificarlos ni regenerarlos** y los
contrasta con la teoría (``sanmames.capacity``) y con la memoria. Solo simula
para reproducir réplicas concretas ya publicadas (reproducibilidad) y genera
espectadores (sin simular) para contrastar las entradas aleatorias.

Imprime tablas en Markdown para ``docs/VERIFICACION.md``.

Uso::

    python scripts/validate_final.py               # completo (≈ 1,5 min)
    python scripts/validate_final.py --quick       # 20 semillas por escenario, sin réplicas
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from sanmames import capacity as cap
from sanmames.analysis import confidence_interval
from sanmames.arrivals import generate_spectators
from sanmames.config import EXPERIMENTS_DIR, Config, load_experiment
from sanmames.metrics import KPI_COLUMNS, compute_kpis
from sanmames.rng import RngStreams
from sanmames.runner import run_replica

FINAL = Path(__file__).resolve().parents[1] / "results" / "final"
ALPHA = 0.05

# Escenarios con la misma entrada que X0 (solo cambian fases posteriores o la
# velocidad, que no interviene antes del torno): sus KPIs de entrada deben ser
# idénticos semilla a semilla por los números aleatorios comunes (D17).
SAME_ENTRY_AS_X0 = [
    "X4_escalonada",
    "X5_3acomodadores",
    "X5_6acomodadores",
    "X5_9acomodadores",
    "X7_todas_salidas",
    "X7_salida_bloqueada",
    "S1_vel_-15",
    "S1_vel_+15",
]
ENTRY_KPIS = ["n_entered", "wait_mean_min", "wait_p95_min", "queue_max_gate", "n_read_failures"]
# Mismos espectadores (N y atributos) que X0: mismos fallos de lectura I2 (D26).
SAME_I2_AS_X0 = ["X1_2tornos", "X1_4tornos", "X2_anticipado", "X3_prioridad", "X6_con_redireccion"]
PAIRS = [  # (alternativa, referencia, KPI) para medir la reducción de varianza
    ("X1_4tornos", "X0_base", "wait_mean_min"),
    ("X2_anticipado", "X0_base", "wait_mean_min"),
    ("X1_2tornos", "X0_base", "wait_mean_min"),
    ("X6_con_redireccion", "X6_sin_redireccion", "wait_mean_min"),
]
REPRODUCE = [("X0_base", 0), ("X1_2tornos", 0)]


def fmt(x: float, d: int = 3) -> str:
    """Número en formato español: miles con punto y decimales con coma."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    return f"{x:,.{d}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def ci(values: pd.Series, d: int = 3) -> str:
    m, h = confidence_interval(values.to_numpy())
    return f"{fmt(m, d)} ± {fmt(h, d)}"


def configs() -> dict[str, Config]:
    out: dict[str, Config] = {}
    for path in sorted(EXPERIMENTS_DIR.glob("*.json")):
        for c in load_experiment(path).configs:
            out[c.name] = c
    return out


def table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


# ----------------------------------------------------------------------------- 1


def section_capacity(cfgs: dict[str, Config], kpis: pd.DataFrame, audit: pd.DataFrame) -> str:
    x0 = cfgs["X0_base"]
    k0 = kpis[kpis.scenario.eq("X0_base")]
    a0 = audit[audit.scenario.eq("X0_base")]
    rf, tf = x0.incidents.read_failure, x0.incidents.turnstile_failure
    i2_rate = k0.n_read_failures / k0.n_spectators * 100
    window = a0.stop_time_min - x0.t_open_min
    expected_i3 = x0.n_turnstiles * window / (tf.mtbf_min + tf.repair_min.mean)
    rows = [
        ["Fallos de lectura I2 (% de espectadores)", fmt(rf.prob * 100, 2), ci(i2_rate, 3)],
        [
            "Averías I3 por réplica, 72 tornos en [apertura, fin] (D25)",
            f"{fmt(expected_i3.mean(), 1)} (72·T / (240 + 6,5))",
            ci(k0.n_turnstile_failures.astype(float), 1),
        ],
    ]
    return table(
        [f"Componente de la capacidad (X0, n = {len(k0)})", "Teórico", "results/final, IC 95 %"],
        rows,
    )


def section_rho(cfgs: dict[str, Config], kpis: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    rows, recs = [], []
    for name, c in cfgs.items():
        k = kpis[kpis.scenario.eq(name)]
        if k.empty:
            continue
        fl = cap.fluid_entry_wait(c)
        m, h = confidence_interval(k.wait_mean_min.to_numpy())
        recs.append({"scenario": name, "rho": cap.traffic_intensity(c), "wait": m})
        rows.append(
            [
                name,
                str(len(k)),
                fmt(cap.peak_arrival_rate_min(c), 1),
                fmt(cap.total_capacity_min(c), 0),
                fmt(cap.traffic_intensity(c), 3),
                fmt(fl["wait_mean_min"], 3),
                f"{fmt(m)} ± {fmt(h)}",
                fmt(fl["wait_max_min"], 2),
                ci(k.wait_p95_min),
                ci(k.queue_max_gate.astype(float), 0),
            ]
        )
    df = pd.DataFrame(recs).sort_values("rho")
    head = [
        "Escenario",
        "n",
        "λ pico (pers/min)",
        "Capacidad (pers/min)",
        "ρ",
        "Espera media fluida (min)",
        "Espera media observada (min)",
        "Espera máx. fluida (min)",
        "P95 observado (min)",
        "Cola máx. en una puerta",
    ]
    return table(head, sorted(rows, key=lambda r: float(r[4].replace(",", ".")))), df


def section_closure(cfgs: dict[str, Config], audit: pd.DataFrame) -> str:
    rows = []
    for name, redirect in (("X6_sin_redireccion", False), ("X6_con_redireccion", True)):
        a = audit[audit.scenario.eq(name)]
        c = cfgs[name]
        gc = c.incidents.gate_closure
        lam_gate = (
            c.n_spectators
            / (len(c.zones) * c.gates_per_zone)
            * sum(
                b.prob / (b.end_min - b.start_min)
                for b in c.active_profile
                if b.start_min <= gc.start_min < b.end_min
            )
        )
        rows.append(
            [
                name,
                str(len(a)),
                fmt(lam_gate * gc.duration_min, 0),
                ci(a.closure_arrivals.astype(float), 1),
                fmt(cap.fluid_closure_wait(c, redirect=redirect), 3),
                ci(a.closure_wait_mean_min),
            ]
        )
    head = [
        "Escenario",
        "n",
        "Llegadas en el cierre (teórico)",
        "Observadas",
        "Espera fluida (min)",
        "Espera observada (min)",
    ]
    return table(head, rows)


# ----------------------------------------------------------------------------- 2


def chi2_summary(counts: np.ndarray, probs: np.ndarray) -> tuple[float, float, float, float]:
    """(máx. desviación de la proporción, χ² agregado, p agregado, % de réplicas con p < α)."""
    total = counts.sum(axis=0)
    expected = probs * total.sum()
    chi2, p = stats.chisquare(total, expected)
    per = [stats.chisquare(r, probs * r.sum()).pvalue for r in counts]
    dev = float(np.max(np.abs(total / total.sum() - probs)))
    return dev, float(chi2), float(p), float(np.mean(np.array(per) < ALPHA) * 100)


def section_inputs(
    cfgs: dict[str, Config], kpis: pd.DataFrame, zones: pd.DataFrame, quick: bool
) -> str:
    rows = []
    mismatch = 0
    checked = 0
    for name in ("X0_base", "X2_anticipado"):
        c = cfgs[name]
        seeds = kpis[kpis.scenario.eq(name)].seed.to_numpy()
        if quick:
            seeds = seeds[:20]
        edges = [b.start_min for b in c.active_profile] + [c.active_profile[-1].end_min]
        probs_bins = np.array([b.prob for b in c.active_profile])
        groups = list(c.groups)
        probs_g = np.array([c.groups[g].share for g in groups])
        bins, grp, zon = [], [], []
        for s in seeds:
            sps = generate_spectators(c, RngStreams(int(s)))
            t = np.array([sp.t_arrival for sp in sps])
            bins.append(np.histogram(t, bins=edges)[0])
            g = pd.Series([sp.group for sp in sps]).value_counts()
            grp.append([g.get(x, 0) for x in groups])
            z = pd.Series([sp.zone for sp in sps]).value_counts()
            zon.append([z.get(x, 0) for x in c.zones])
            ref = zones[zones.scenario.eq(name) & zones.seed.eq(s)].set_index("zone").n_spectators
            checked += 1
            mismatch += int(any(ref[x] != z.get(x, 0) for x in c.zones))
        n = len(seeds)
        for label, counts, probs in (
            ("Perfil de llegadas (%d franjas)" % len(probs_bins), np.array(bins), probs_bins),
            ("Grupos 88/10/2 %", np.array(grp), probs_g),
        ):
            dev, chi2, p, rej = chi2_summary(counts, probs)
            rows.append(
                [
                    f"{label} · {name}",
                    str(n),
                    fmt(dev * 100, 3),
                    f"{fmt(chi2, 2)} (gl {len(probs) - 1})",
                    fmt(p, 3),
                    fmt(rej, 1),
                ]
            )
    # Zonas: directamente de zones.csv (todas las réplicas de los 19 escenarios).
    for name in ("X0_base", "all"):
        z = zones if name == "all" else zones[zones.scenario.eq(name)]
        counts = z.pivot_table(
            index=["scenario", "seed"],
            columns="zone",
            values="n_spectators",
        ).to_numpy()
        dev, chi2, p, rej = chi2_summary(counts, np.full(4, 0.25))
        label = "Macrozonas 25 % · " + ("19 escenarios" if name == "all" else name)
        rows.append(
            [
                label,
                str(len(counts)),
                fmt(dev * 100, 3),
                f"{fmt(chi2, 2)} (gl 3)",
                fmt(p, 3),
                fmt(rej, 1),
            ]
        )
    head = [
        "Reparto",
        "Réplicas",
        "Máx. desviación (p. p.)",
        "χ² agregado",
        "p agregado",
        f"% réplicas con p < {fmt(ALPHA, 2)}",
    ]
    note = (
        "\n\nEspectadores regenerados con las semillas de `results/final`: "
        f"{checked} réplicas, {mismatch} con recuento por zona distinto de `zones.csv`."
    )
    return table(head, rows) + note


# ----------------------------------------------------------------------------- 3


def section_conservation(audit: pd.DataFrame, kpis: pd.DataFrame) -> str:
    a = audit.merge(kpis[["scenario", "seed", "n_spectators"]], on=["scenario", "seed"])
    alarm = a.alarm_triggered.astype(bool)
    ordinary = ~alarm
    ok_ord = (
        a.n_entered.eq(a.n_spectators)
        & a.n_seated.eq(a.n_spectators)
        & a.n_exited.eq(a.n_spectators)
        & a.n_unfinished.eq(0)
    )[ordinary]
    ok_alarm = (a.n_safe + a.n_abandoned).eq(a.n_spectators)[alarm] & a.n_unfinished[alarm].eq(0)
    rows = [
        [
            "Sin alarma: generados = entran = se sientan = salen, sin pendientes",
            str(int(ordinary.sum())),
            str(int(ok_ord.sum())),
        ],
        [
            "Con alarma (X7): a salvo + abandonan = generados, sin pendientes",
            str(int(alarm.sum())),
            str(int(ok_alarm.sum())),
        ],
        [
            "Con alarma (X7): no sentados al sonar (en vomitorio o conflicto), a salvo",
            str(int(alarm.sum())),
            f"{int((a.n_seated < a.n_spectators)[alarm].sum())} réplicas con 1 sin sentar",
        ],
    ]
    return table(["Comprobación", "Réplicas", "Cumplen"], rows)


def section_crn(kpis: pd.DataFrame) -> str:
    k = kpis.set_index(["scenario", "seed"])
    x0 = k.loc["X0_base"]
    rows = []
    for name in SAME_ENTRY_AS_X0:
        other = k.loc[name]
        common = x0.index.intersection(other.index)
        same = (x0.loc[common, ENTRY_KPIS] == other.loc[common, ENTRY_KPIS]).all(axis=1)
        rows.append([f"{name} = X0 en KPIs de entrada", str(len(common)), str(int(same.sum()))])
    for name in SAME_I2_AS_X0:
        other = k.loc[name]
        common = x0.index.intersection(other.index)
        same = x0.loc[common, "n_read_failures"] == other.loc[common, "n_read_failures"]
        rows.append([f"{name} = X0 en nº de fallos I2", str(len(common)), str(int(same.sum()))])
    t1 = table(["Números comunes (D17, D21, D26)", "Semillas comunes", "Idénticas"], rows)
    rows = []
    for alt, ref, kpi in PAIRS:
        a, b = k.loc[alt, kpi], k.loc[ref, kpi]
        common = a.index.intersection(b.index)
        a, b = a.loc[common], b.loc[common]
        var_ind = a.var(ddof=1) + b.var(ddof=1)
        var_pair = (a - b).var(ddof=1)
        rows.append(
            [
                f"{alt} − {ref}",
                str(len(common)),
                fmt(a.corr(b), 3),
                fmt(var_pair / var_ind * 100, 1),
                fmt(math.sqrt(var_ind / var_pair), 2),
            ]
        )
    t2 = table(
        [
            "Diferencia de espera media",
            "Parejas",
            "Correlación",
            "Var. emparejada / independiente (%)",
            "Factor de estrechamiento del IC",
        ],
        rows,
    )
    return t1 + "\n\n" + t2


def section_reproduce(cfgs: dict[str, Config], kpis: pd.DataFrame) -> str:
    rows = []
    for name, replica in REPRODUCE:
        c = cfgs[name]
        ref = kpis[kpis.scenario.eq(name) & kpis.replica.eq(replica)].iloc[0]
        df = run_replica(c, int(ref.seed))
        got = compute_kpis(df, c)
        diff = max(
            abs(float(got[col]) - float(ref[col]))
            for col in KPI_COLUMNS
            if not (pd.isna(got[col]) and pd.isna(ref[col]))
        )
        rate = cap.busy_rate_per_turnstile(df, c)
        rows.append(
            [
                f"{name}, réplica {replica} (semilla {int(ref.seed)})",
                f"{diff:.1e}".replace(".", ","),
                fmt(rate, 2) if not math.isnan(rate) else "sin cola ≥ 5 min",
                fmt(cap.capacity_per_turnstile_min(c), 2),
            ]
        )
    return table(
        [
            "Réplica rehecha",
            "Máx. diferencia de KPI frente a kpis.csv",
            "Ritmo por torno con cola (pers/min)",
            "Capacidad teórica",
        ],
        rows,
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--quick",
        action="store_true",
        help="20 semillas para las entradas y sin rehacer réplicas",
    )
    args = ap.parse_args(argv)
    kpis = pd.read_csv(FINAL / "kpis.csv")
    audit = pd.read_csv(FINAL / "audit.csv")
    zones = pd.read_csv(FINAL / "zones.csv")
    cfgs = configs()
    print(f"results/final: {len(kpis)} réplicas, {kpis.scenario.nunique()} escenarios\n")
    print("## Capacidad\n")
    print(section_capacity(cfgs, kpis, audit), "\n")
    print("## ρ frente a la espera\n")
    t, df = section_rho(cfgs, kpis)
    print(t, "\n")
    distinct = df.drop_duplicates(subset=["rho", "wait"])
    rs = stats.spearmanr(distinct.rho, distinct.wait)
    n_distinct = len(distinct)
    print(f"Spearman ρ–espera ({n_distinct} entradas distintas): {fmt(float(rs.statistic))}\n")
    print("## Cierre I4\n")
    print(section_closure(cfgs, audit), "\n")
    print("## Entradas aleatorias\n")
    print(section_inputs(cfgs, kpis, zones, args.quick), "\n")
    print("## Conservación\n")
    print(section_conservation(audit, kpis), "\n")
    print("## Números comunes\n")
    print(section_crn(kpis), "\n")
    if not args.quick:
        print("## Reproducibilidad\n")
        print(section_reproduce(cfgs, kpis), "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

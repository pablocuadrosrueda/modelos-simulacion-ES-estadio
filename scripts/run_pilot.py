"""T5.1: piloto X0–X7, auditoría y análisis entre réplicas.

Uso: python scripts/run_pilot.py --reps 10 --output results/pilot
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from dataclasses import asdict, replace
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

import pandas as pd

from sanmames.analysis import compare_with_baseline, required_replications, summarize
from sanmames.config import EXPERIMENTS_DIR, Config, load_experiment
from sanmames.experiments import DEFAULT_BASE_SEED, replica_seed
from sanmames.metrics import ID_COLUMNS, KPI_COLUMNS, compute_kpis
from sanmames.runner import run_replica

ROOT = Path(__file__).resolve().parents[1]
GROUP_KPIS = ["wait_mean_priority_min", "wait_mean_rest_min", "group_wait_diff_min"]


def group_kpis(df: pd.DataFrame, config: Config, groups: tuple[str, ...]) -> dict:
    """Mismos colectivos para P4; solo reclasifica métricas, no cambia el recorrido."""
    indicators = compute_kpis(df, replace(config, priority_groups=groups))
    return {name: indicators[name] for name in GROUP_KPIS}


def audit_replica(df: pd.DataFrame, config: Config) -> tuple[dict, list[dict]]:
    """Comprueba identidad y terminación; registra reparto sin asumirlo exacto."""
    if len(df) != config.n_spectators or df.id.nunique() != config.n_spectators:
        raise ValueError(f"{config.name}: pérdida o duplicación de espectadores")
    terminal = (
        df.t_exit.notna().astype(int)
        + df.t_safe.notna().astype(int)
        + df.abandoned.eq(True).astype(int)
    )
    if config.emergency.enabled and df.attrs["alarm_triggered"]:
        terminal += (df.t_arrival > config.emergency.alarm_min).astype(int)
    if terminal.gt(1).any():
        raise ValueError(f"{config.name}: estados terminales incompatibles")
    unfinished = int(terminal.eq(0).sum())
    if unfinished:
        raise ValueError(f"{config.name}: {unfinished} espectadores pendientes al terminar")
    audit = {
        "n_entered": int(df.t_end_control.notna().sum()),
        "n_seated": int(df.t_seated.notna().sum()),
        "n_exited": int(df.t_exit.notna().sum()),
        "n_safe": int(df.t_safe.notna().sum()),
        "n_abandoned": int(df.abandoned.eq(True).sum()),
        "n_unfinished": unfinished,
        "stop_time_min": df.attrs["stop_time_min"],
        "alarm_triggered": df.attrs["alarm_triggered"],
    }
    zones = [
        {
            "zone": zone,
            "n_spectators": int(df.zone.eq(zone).sum()),
            "share_pct": float(df.zone.eq(zone).mean() * 100),
        }
        for zone in config.zones
    ]
    return audit, zones


def write_analysis(kpis: pd.DataFrame, output: Path) -> None:
    """IC del 95 %, contrastes pertinentes y precisión relativa de la espera."""
    summary = summarize(kpis)
    summary.to_csv(output / "summary.csv", index=False)
    comparisons = []
    references = {
        "X1": "X0_base",
        "X2": "X0_base",
        "X3": "X0_base",
        "X4": "X0_base",
        "X5": "X5_6acomodadores",
        "X6": "X6_sin_redireccion",
        "X7": "X7_todas_salidas",
    }
    for experiment, reference in references.items():
        selected = kpis.loc[kpis.experiment.eq(experiment) | kpis.scenario.eq(reference)]
        if reference in set(selected.scenario) and selected.scenario.nunique() > 1:
            table = compare_with_baseline(selected, baseline=reference)
            if experiment == "X3" and (output / "groups.csv").exists():
                groups = pd.read_csv(output / "groups.csv")
                paired = compare_with_baseline(groups, baseline=reference).set_index("scenario")
                for name in GROUP_KPIS:
                    for suffix in ["mean", "halfwidth", "n"]:
                        column = f"{name}_{suffix}"
                        table[column] = table.scenario.map(paired[column])
            table.insert(0, "experiment", experiment)
            comparisons.append(table)
    if comparisons:
        pd.concat(comparisons, ignore_index=True).to_csv(output / "comparisons.csv", index=False)
    precision = []
    for scenario, group in kpis.groupby("scenario", sort=False):
        row = summary.loc[summary.scenario.eq(scenario)].iloc[0]
        mean, halfwidth = row.wait_mean_min_mean, row.wait_mean_min_halfwidth
        try:
            required = required_replications(group.wait_mean_min)
            note = "estimación con t del piloto; comprobar al ampliar"
        except ValueError as exc:
            required, note = None, str(exc)
        precision.append(
            {
                "scenario": scenario,
                "n_pilot": int(row.wait_mean_min_n),
                "wait_mean_min": mean,
                "halfwidth_95_min": halfwidth,
                "relative_halfwidth_pct": 100 * halfwidth / abs(mean) if mean else None,
                "estimated_total_reps": required,
                "note": note,
            }
        )
    pd.DataFrame(precision).to_csv(output / "precision.csv", index=False)


def run_pilot(
    output: Path,
    n_reps: int = 10,
    base_seed: int = DEFAULT_BASE_SEED,
    experiment_dir: Path = EXPERIMENTS_DIR,
) -> pd.DataFrame:
    """Ejecuta el lote y guarda cada réplica; no sobrescribe resultados previos."""
    if isinstance(n_reps, bool) or not isinstance(n_reps, int) or n_reps < 2:
        raise ValueError("El piloto necesita al menos dos réplicas")
    if isinstance(base_seed, bool) or not isinstance(base_seed, int) or base_seed < 0:
        raise ValueError("La semilla debe ser un entero no negativo")
    paths = sorted(experiment_dir.glob("X[0-7]_*.json"))
    configs = [
        (path, experiment.experiment, cfg)
        for path in paths
        for experiment in [load_experiment(path)]
        for cfg in experiment.configs
    ]
    names = [cfg.name for _, _, cfg in configs]
    if not names or len(set(names)) != len(names):
        raise ValueError("Faltan escenarios o hay nombres de escenario duplicados")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"{output} ya contiene resultados; elige otra carpeta")
    output.mkdir(parents=True, exist_ok=True)
    sources = sorted((ROOT / "src/sanmames").glob("*.py")) + [
        Path(__file__).resolve(),
        ROOT / "configs/base.json",
    ]
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "python": platform.python_version(),
        "versions": {name: version(name) for name in ["simpy", "numpy", "pandas", "scipy"]},
        "n_reps": n_reps,
        "base_seed": base_seed,
        "completed": False,
        "confidence_level": 0.95,
        "relative_halfwidth_target": 0.05,
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources
        },
        "scenarios": [{"experiment": exp, "config": asdict(cfg)} for _, exp, cfg in configs],
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    p4_groups = next((cfg.priority_groups for _, exp, cfg in configs if exp == "X3"), ())
    manifest["analysis_group_cohort"] = list(p4_groups)
    rows, audits, zone_rows, group_rows = [], [], [], []
    for _, experiment, cfg in configs:
        for replica in range(n_reps):
            seed = replica_seed(base_seed, replica)
            start = perf_counter()
            df = run_replica(cfg, seed)
            audit, zones = audit_replica(df, cfg)
            identifiers = {
                "experiment": experiment,
                "scenario": cfg.name,
                "replica": replica,
                "seed": seed,
            }
            rows.append({**identifiers, **compute_kpis(df, cfg)})
            if p4_groups and experiment in ("X0", "X3"):
                group_rows.append({**identifiers, **group_kpis(df, cfg, p4_groups)})
                pd.DataFrame(group_rows).to_csv(output / "groups.csv", index=False)
            audits.append({**identifiers, **audit, "elapsed_s": perf_counter() - start})
            zone_rows.extend({**identifiers, **zone} for zone in zones)
            kpis = pd.DataFrame(rows, columns=ID_COLUMNS + KPI_COLUMNS)
            kpis.to_csv(output / "kpis.csv", index=False)
            pd.DataFrame(audits).to_csv(output / "audit.csv", index=False)
            pd.DataFrame(zone_rows).to_csv(output / "zones.csv", index=False)
            print(
                f"[{len(rows)}/{len(configs) * n_reps}] {cfg.name} seed={seed} "
                f"{audits[-1]['elapsed_s']:.2f} s",
                flush=True,
            )
    write_analysis(kpis, output)
    manifest["completed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return kpis


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reps", type=int, default=10)
    parser.add_argument("--seed", type=int, default=DEFAULT_BASE_SEED)
    parser.add_argument("--output", type=Path, default=ROOT / "results/pilot")
    args = parser.parse_args(argv)
    try:
        run_pilot(args.output, args.reps, args.seed)
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

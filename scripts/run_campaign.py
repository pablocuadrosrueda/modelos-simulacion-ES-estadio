"""T5.3: piloto actualizado, réplicas definitivas y S1 con reanudación.

Uso: python scripts/run_campaign.py --output results/final --workers 4
Para continuar: añadir --resume. --pilot-only calcula solo el piloto actualizado.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing
import platform
import subprocess
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

import pandas as pd
from run_pilot import audit_replica, group_kpis, write_analysis

from sanmames.analysis import confidence_interval, required_replications
from sanmames.config import EXPERIMENTS_DIR, load_experiment
from sanmames.experiments import DEFAULT_BASE_SEED, replica_seed
from sanmames.metrics import ID_COLUMNS, KPI_COLUMNS, compute_kpis
from sanmames.runner import run_replica

ROOT = Path(__file__).resolve().parents[1]


def _json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def _simulate(task: tuple) -> dict:
    experiment, cfg, replica, seed, cohort = task
    start = perf_counter()
    df = run_replica(cfg, seed)
    audit, zones = audit_replica(df, cfg)
    incidents = df.attrs["incidents"]
    conflicts = incidents.loc[incidents.kind.eq("I1")]
    durations = (conflicts.t_end - conflicts.t_start).dropna()
    audit.update(
        last_seated_min=float(df.t_seated.max()),
        conflict_duration_mean_min=float(durations.mean()),
        conflict_duration_p95_min=float(durations.quantile(0.95)),
        conflict_duration_max_min=float(durations.max()),
    )
    closure = cfg.incidents.gate_closure
    affected = (
        df.loc[
            df.zone.eq(closure.zone)
            & df.gate.eq(closure.gate)
            & df.t_arrival.ge(closure.start_min)
            & df.t_arrival.lt(closure.start_min + closure.duration_min)
        ]
        if closure.enabled
        else df.iloc[:0]
    )
    audit.update(
        closure_arrivals=len(affected),
        closure_redirected=int(affected.gate_used.ne(affected.gate).sum()),
        closure_wait_mean_min=float((affected.t_start_control - affected.t_arrival).mean()),
    )
    kpis = compute_kpis(df, cfg)
    groups = group_kpis(df, cfg, cohort) if cohort and experiment in ("X0", "X3") else None
    audit["elapsed_s"] = perf_counter() - start
    return {
        "experiment": experiment,
        "scenario": cfg.name,
        "replica": replica,
        "seed": seed,
        "kpis": kpis,
        "audit": audit,
        "zones": zones,
        "groups": groups,
    }


def _tables(records: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    kpis, audits, zones, groups = [], [], [], []
    for _, record in sorted(records.items()):
        ids = {name: record[name] for name in ID_COLUMNS}
        kpis.append({**ids, **record["kpis"]})
        audits.append({**ids, **record["audit"]})
        zones.extend({**ids, **zone} for zone in record["zones"])
        if record["groups"] is not None:
            groups.append({**ids, **record["groups"]})
    return (
        pd.DataFrame(kpis, columns=ID_COLUMNS + KPI_COLUMNS),
        pd.DataFrame(audits),
        pd.DataFrame(zones),
        pd.DataFrame(groups),
    )


def _export(records: dict, output: Path) -> pd.DataFrame:
    output.mkdir(parents=True, exist_ok=True)
    kpis, audits, zones, groups = _tables(records)
    for name, frame in [("kpis", kpis), ("audit", audits), ("zones", zones)]:
        frame.to_csv(output / f"{name}.csv", index=False)
    if not groups.empty:
        groups.to_csv(output / "groups.csv", index=False)
    write_analysis(kpis, output)
    precision = pd.read_csv(output / "precision.csv").rename(columns={"n_pilot": "n_valid"})
    precision["precision_met"] = precision.relative_halfwidth_pct.le(5) | (
        precision.wait_mean_min.eq(0) & precision.halfwidth_95_min.eq(0)
    )
    precision.to_csv(output / "precision.csv", index=False)
    return kpis


def plan_replicas(kpis: pd.DataFrame, minimum: int) -> dict[str, int]:
    """Tamaño por escenario; amplía si el IC observado aún no cumple el 5 %."""
    targets = {}
    for scenario, group in kpis.groupby("scenario", sort=True):
        values = group.wait_mean_min.dropna()
        mean, halfwidth = confidence_interval(values)
        estimate = required_replications(values)
        met = math.isfinite(halfwidth) and halfwidth <= 0.05 * abs(mean)
        targets[scenario] = max(minimum, len(values) if met else max(len(values) + 10, estimate))
    return targets


def _run_batch(tasks: list[tuple], records: dict, output: Path, workers: int, label: str) -> None:
    checkpoints = output / "checkpoints"
    checkpoints.mkdir(exist_ok=True)
    count = 0

    def save(record):
        nonlocal count
        key = (record["scenario"], record["replica"])
        if key in records:
            raise ValueError(f"Réplica duplicada: {key}")
        _json(checkpoints / f"{key[0]}-{key[1]:06d}.json", record)
        records[key] = record
        count += 1
        if count == 1 or count % 25 == 0 or count == len(tasks):
            print(
                f"[{label}] nuevas {count}/{len(tasks)}; guardadas {len(records)}; "
                f"última {key[0]} seed={record['seed']}",
                flush=True,
            )

    if workers == 1:
        for task in tasks:
            save(_simulate(task))
        return
    # spawn también en macOS/Linux: el mismo mecanismo usado por Windows.
    with ProcessPoolExecutor(
        max_workers=workers, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        iterator = iter(tasks)
        pending = {
            pool.submit(_simulate, task)
            for task in [next(iterator, None) for _ in range(workers)]
            if task is not None
        }
        while pending:
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                save(future.result())
                task = next(iterator, None)
                if task is not None:
                    pending.add(pool.submit(_simulate, task))


def run_campaign(
    output: Path,
    *,
    workers: int = 1,
    resume: bool = False,
    pilot_only: bool = False,
    pilot_reps: int = 10,
    minimum: int = 30,
    base_seed: int = DEFAULT_BASE_SEED,
    experiment_dir: Path = EXPERIMENTS_DIR,
) -> pd.DataFrame:
    if pilot_reps < 2 or minimum < pilot_reps or workers < 1 or base_seed < 0:
        raise ValueError("Exige piloto >=2, mínimo >=piloto, workers >=1 y semilla >=0")
    configs = [
        (exp.experiment, cfg)
        for path in sorted(experiment_dir.glob("*.json"))
        for exp in [load_experiment(path)]
        if exp.experiment in {f"X{i}" for i in range(8)} | {"S1"}
        for cfg in exp.configs
    ]
    names = [cfg.name for _, cfg in configs]
    if not names or len(names) != len(set(names)):
        raise ValueError("No hay escenarios o existen nombres duplicados")
    cohort = next((cfg.priority_groups for exp, cfg in configs if exp == "X3"), ())
    sources = sorted((ROOT / "src/sanmames").glob("*.py")) + [
        Path(__file__).resolve(),
        ROOT / "scripts/run_pilot.py",
        ROOT / "configs/base.json",
    ]
    provenance = {
        "python": platform.python_version(),
        "versions": {name: version(name) for name in ["simpy", "numpy", "pandas", "scipy"]},
        "source_sha256": {
            p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sources
        },
        "scenarios": [{"experiment": exp, "config": cfg.raw} for exp, cfg in configs],
        "base_seed": base_seed,
        "pilot_reps": pilot_reps,
        "minimum_reps": minimum,
        "confidence_level": 0.95,
        "relative_halfwidth_target": 0.05,
        "analysis_group_cohort": list(cohort),
    }
    fingerprint = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()
    manifest_path = output / "manifest.json"
    if resume:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["fingerprint"] != fingerprint:
            raise ValueError("No se puede reanudar: han cambiado código, versiones, configs o plan")
    else:
        if output.exists() and any(output.iterdir()):
            raise ValueError(f"{output} ya contiene datos; usa --resume o una carpeta nueva")
        output.mkdir(parents=True, exist_ok=True)
        manifest = {
            **provenance,
            "fingerprint": fingerprint,
            "completed": False,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "history": [],
        }
        _json(manifest_path, manifest)
    records = {}
    for path in sorted((output / "checkpoints").glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        key = (record["scenario"], record["replica"])
        if (
            key in records
            or key[0] not in names
            or record["seed"] != replica_seed(base_seed, key[1])
        ):
            raise ValueError(f"Checkpoint incoherente: {path}")
        records[key] = record

    def tasks_for(targets):
        return [
            (exp, cfg, rep, replica_seed(base_seed, rep), cohort)
            for exp, cfg in configs
            for rep in range(targets[cfg.name])
            if (cfg.name, rep) not in records
        ]

    start = perf_counter()
    pilot_targets = dict.fromkeys(names, pilot_reps)
    tasks = tasks_for(pilot_targets)
    if tasks:
        _run_batch(tasks, records, output, workers, "piloto")
    pilot_records = {key: record for key, record in records.items() if key[1] < pilot_reps}
    pilot = _export(pilot_records, output / "pilot")
    manifest["pilot_completed"] = True
    targets = plan_replicas(pilot, minimum)
    manifest["pilot_targets"] = targets
    _json(manifest_path, manifest)
    if pilot_only:
        print(f"Piloto completo: {len(pilot)} filas. Objetivos: {targets}", flush=True)
        return pilot
    iteration = 0
    while True:
        iteration += 1
        if records:
            current = _tables(records)[0]
            targets = plan_replicas(current, minimum)
        tasks = tasks_for(targets)
        manifest["targets"] = targets
        manifest["completed"] = False
        _json(manifest_path, manifest)
        if not tasks:
            break
        print(
            f"Ampliación {iteration}: {len(tasks)} réplicas nuevas. Objetivos: {targets}",
            flush=True,
        )
        before = perf_counter()
        _run_batch(tasks, records, output, workers, f"definitivas {iteration}")
        manifest["history"].append(
            {
                "iteration": len(manifest["history"]) + 1,
                "new_replicas": len(tasks),
                "elapsed_s": perf_counter() - before,
                "targets": targets,
            }
        )
        _export(records, output)
        _json(manifest_path, manifest)
    result = _export(records, output)
    manifest.update(
        completed=True,
        final_counts=result.groupby("scenario").size().to_dict(),
        updated_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    manifest["execution_wall_s"] = manifest.get("execution_wall_s", 0) + perf_counter() - start
    _json(manifest_path, manifest)
    print(
        f"Campaña terminada: {len(result)} réplicas; todos los IC cumplen la precisión.", flush=True
    )
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results/final")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--pilot-only", action="store_true")
    parser.add_argument("--pilot-reps", type=int, default=10)
    parser.add_argument("--min-reps", type=int, default=30)
    parser.add_argument("--seed", type=int, default=DEFAULT_BASE_SEED)
    parser.add_argument("--experiment-dir", type=Path, default=EXPERIMENTS_DIR)
    args = parser.parse_args(argv)
    try:
        run_campaign(
            args.output,
            workers=args.workers,
            resume=args.resume,
            pilot_only=args.pilot_only,
            pilot_reps=args.pilot_reps,
            minimum=args.min_reps,
            base_seed=args.seed,
            experiment_dir=args.experiment_dir,
        )
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

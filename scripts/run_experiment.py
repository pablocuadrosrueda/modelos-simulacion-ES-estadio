"""CLI: ejecuta un experimento y guarda la tabla de KPIs por réplica.

Uso:
    python scripts/run_experiment.py X0 --reps 10
    python scripts/run_experiment.py X1_2tornos --reps 30 --seed 20261105
    python scripts/run_experiment.py --list
"""

from __future__ import annotations

import argparse
import sys

from sanmames.experiments import (
    DEFAULT_BASE_SEED,
    RESULTS_DIR,
    find_experiment_file,
    list_experiments,
    run_experiment,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("name", nargs="?", help="experimento (stem o prefijo único, p. ej. X0)")
    parser.add_argument("--reps", type=int, default=10, help="réplicas por escenario")
    parser.add_argument("--seed", type=int, default=DEFAULT_BASE_SEED, help="semilla base")
    parser.add_argument("--list", action="store_true", help="lista los experimentos")
    args = parser.parse_args(argv)

    if args.list or not args.name:
        print("\n".join(list_experiments()))
        return 0
    if args.reps < 1:
        parser.error("--reps debe ser >= 1")

    path = find_experiment_file(args.name)
    try:
        kpis = run_experiment(path.stem, args.reps, base_seed=args.seed)
    except NotImplementedError as exc:
        print(f"Aún no implementado: {exc}. Ver docs/TAREAS.md.", file=sys.stderr)
        return 2
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / f"{path.stem}_kpis.csv"
    kpis.to_csv(out, index=False)
    print(f"KPIs guardados en {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Comprueba que un PR deja la documentación de contexto al día (AGENTS.md, reglas 6 y 7).

Reglas, sobre los ficheros que cambia la rama respecto a la base:

1. Si cambia código, tests o configs: deben cambiar ``docs/ESTADO.md`` y ``docs/TAREAS.md``.
2. Si cambia un contrato compartido (``entities.py``, ``config.py``, ``rng.py``,
   ``configs/base.json``, ``docs/CONTRATOS.md``): debe cambiar ``docs/AVISOS.md`` o
   ``docs/DECISIONES.md``.

Uso: ``python scripts/check_pr_docs.py --base origin/main``. Sale con 1 si falla.
Un PR de solo documentación o de infraestructura (``.github/``, ``Makefile``...) no
dispara ninguna regla.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

CODE_PREFIXES = ("src/", "tests/", "configs/")
CONTRACT_FILES = {
    "src/sanmames/entities.py",
    "src/sanmames/config.py",
    "src/sanmames/rng.py",
    "configs/base.json",
    "docs/CONTRATOS.md",
}
STATE_DOCS = ("docs/ESTADO.md", "docs/TAREAS.md")
NOTICE_DOCS = ("docs/AVISOS.md", "docs/DECISIONES.md")


def check(changed: list[str]) -> list[str]:
    """Devuelve la lista de problemas (vacía si todo está en orden)."""
    files = set(changed)
    problems: list[str] = []
    if any(f.startswith(CODE_PREFIXES) for f in files):
        missing = [d for d in STATE_DOCS if d not in files]
        if missing:
            problems.append(
                "El PR cambia código, tests o configs pero no actualiza: " + ", ".join(missing)
            )
    touched = sorted(files & CONTRACT_FILES)
    if touched and not any(d in files for d in NOTICE_DOCS):
        problems.append(
            "El PR cambia un contrato compartido ("
            + ", ".join(touched)
            + ") sin añadir un aviso en docs/AVISOS.md ni una decisión en docs/DECISIONES.md"
        )
    return problems


def changed_files(base: str) -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="origin/main", help="rama base (por defecto origin/main)")
    args = parser.parse_args()
    problems = check(changed_files(args.base))
    for p in problems:
        print(f"ERROR: {p}")
    if problems:
        print("\nVer AGENTS.md (reglas 6 y 7) y docs/AVISOS.md.")
        return 1
    print("Documentación de contexto al día.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

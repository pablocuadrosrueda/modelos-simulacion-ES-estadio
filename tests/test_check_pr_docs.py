"""Comprobación de documentación de un PR (scripts/check_pr_docs.py)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "check_pr_docs", Path(__file__).parent.parent / "scripts" / "check_pr_docs.py"
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)
check = mod.check

STATE = ["docs/ESTADO.md", "docs/TAREAS.md"]


def test_docs_only_pr_is_fine() -> None:
    assert check(["README.md", "docs/ESPECIFICACION.md"]) == []
    assert check([".github/workflows/ci.yml", "Makefile"]) == []


def test_code_without_state_docs_fails() -> None:
    assert len(check(["src/sanmames/entry.py"])) == 1
    assert len(check(["src/sanmames/entry.py", "docs/ESTADO.md"])) == 1
    assert check(["src/sanmames/entry.py", *STATE]) == []


def test_tests_and_configs_also_count_as_code() -> None:
    assert check(["tests/test_entry.py"]) != []
    assert check(["configs/experiments/X1_2tornos.json"]) != []


def test_contract_change_needs_notice() -> None:
    changed = ["src/sanmames/entities.py", *STATE]
    assert len(check(changed)) == 1
    assert check([*changed, "docs/AVISOS.md"]) == []
    assert check([*changed, "docs/DECISIONES.md"]) == []


def test_both_rules_can_fail_together() -> None:
    assert len(check(["src/sanmames/rng.py"])) == 2

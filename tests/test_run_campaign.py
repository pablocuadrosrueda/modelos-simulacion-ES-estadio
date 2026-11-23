"""T5.3: tamaño, checkpoints y reanudación real con procesos spawn."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from conftest import MINI_OVERRIDES
from sanmames.config import load_experiment

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def campaign(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("run_campaign", ROOT / "scripts/run_campaign.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_plan_uses_precision_and_minimum(campaign):
    frame = pd.DataFrame(
        {"scenario": ["variable"] * 3 + ["stable"] * 3, "wait_mean_min": [8, 10, 12, 0, 0, 0]}
    )
    assert campaign.plan_replicas(frame, 30) == {"stable": 30, "variable": 297}


def test_x5_nine_keeps_conflicts_and_x6_uses_peak():
    cases = [
        load_experiment(ROOT / f"configs/experiments/X5_{n}acomodadores.json").configs[0]
        for n in [3, 6, 9]
    ]
    assert [cfg.stewards_per_zone for cfg in cases] == [3, 6, 9]
    originals = []
    for cfg in cases:
        raw = dict(cfg.raw)
        raw.pop("name")
        raw.pop("stewards_per_zone")
        originals.append(raw)
        assert cfg.incidents.seat_conflict.prob == 0.01
    assert originals[0] == originals[1] == originals[2]
    for stem in ["sin_redireccion", "con_redireccion"]:
        cfg = load_experiment(ROOT / f"configs/experiments/X6_{stem}.json").configs[0]
        assert cfg.incidents.gate_closure.start_min == -30
        assert cfg.incidents.gate_closure.duration_min == 10


def test_spawn_resume_and_reject_changed_config(tmp_path):
    configs = tmp_path / "configs"
    configs.mkdir()
    for name, exp in [("X0_base", "X0"), ("X1_test", "X1")]:
        (configs / f"{name}.json").write_text(
            json.dumps(
                {
                    "experiment": exp,
                    "label": name,
                    "question": "P1",
                    "overrides": {**MINI_OVERRIDES, "name": name, "n_spectators": 8},
                }
            ),
            encoding="utf-8",
        )
    output = tmp_path / "final"
    cmd = [
        sys.executable,
        str(ROOT / "scripts/run_campaign.py"),
        "--output",
        str(output),
        "--experiment-dir",
        str(configs),
        "--workers",
        "2",
        "--pilot-reps",
        "2",
        "--min-reps",
        "3",
        "--seed",
        "100",
    ]
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"}
    pilot = subprocess.run(cmd + ["--pilot-only"], capture_output=True, text=True, env=env)
    assert pilot.returncode == 0, pilot.stderr
    original = {p.name: p.read_bytes() for p in (output / "checkpoints").glob("*.json")}
    assert len(original) == 4
    completed = subprocess.run(cmd + ["--resume"], capture_output=True, text=True, env=env)
    assert completed.returncode == 0, completed.stderr
    result = pd.read_csv(output / "kpis.csv")
    assert len(result) == 6
    assert not result.duplicated(["scenario", "seed"]).any()
    assert result.groupby("scenario").seed.apply(list).tolist() == [[100, 101, 102]] * 2
    assert all(
        (output / "checkpoints" / name).read_bytes() == data for name, data in original.items()
    )
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["completed"] is True
    assert pd.read_csv(output / "precision.csv").precision_met.all()
    path = configs / "X0_base.json"
    changed = json.loads(path.read_text(encoding="utf-8"))
    changed["overrides"]["n_spectators"] = 9
    path.write_text(json.dumps(changed), encoding="utf-8")
    rejected = subprocess.run(cmd + ["--resume"], capture_output=True, text=True, env=env)
    assert rejected.returncode == 2
    assert "No se puede reanudar" in rejected.stderr

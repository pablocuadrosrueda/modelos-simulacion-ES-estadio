"""T5.1: lote reproducible pequeño, conservación y salidas estadísticas."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from conftest import MINI_OVERRIDES
from sanmames.config import load_config
from sanmames.entities import SPECTATOR_COLUMNS


@pytest.fixture
def pilot():
    path = Path(__file__).resolve().parents[1] / "scripts/run_pilot.py"
    spec = importlib.util.spec_from_file_location("run_pilot", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_real_small_pilot_exports_common_seeds_and_audit(pilot, tmp_path):
    configs = tmp_path / "configs"
    configs.mkdir()
    for name, exp, extra in [
        ("X0_base", "X0", {}),
        ("X1_4tornos", "X1", {"turnstiles_per_gate": 4}),
    ]:
        (configs / f"{name}.json").write_text(
            json.dumps(
                {
                    "experiment": exp,
                    "label": name,
                    "question": "P1",
                    "overrides": {**MINI_OVERRIDES, "n_spectators": 12, "name": name, **extra},
                }
            )
        )
    output = tmp_path / "pilot"
    result = pilot.run_pilot(output, 2, 100, configs)
    assert result.seed.tolist() == [100, 101, 100, 101]
    assert result.replica.tolist() == [0, 1, 0, 1]
    assert result.n_entered.eq(12).all()
    assert result.exit_time_min.notna().all()
    audit = pd.read_csv(output / "audit.csv")
    assert audit.n_unfinished.eq(0).all() and audit.n_exited.eq(12).all()
    assert audit.elapsed_s.gt(0).all()
    zones = pd.read_csv(output / "zones.csv")
    assert zones.share_pct.eq(100).all()
    summary = pd.read_csv(output / "summary.csv")
    assert summary.wait_mean_min_n.eq(2).all()
    comparison = pd.read_csv(output / "comparisons.csv")
    assert comparison.baseline.tolist() == ["X0_base"]
    assert comparison.wait_mean_min_n.tolist() == [2]
    assert len(pd.read_csv(output / "precision.csv")) == 2
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["completed"] is True
    assert manifest["base_seed"] == 100 and manifest["n_reps"] == 2
    assert len(manifest["scenarios"]) == 2
    assert "src/sanmames/runner.py" in manifest["source_sha256"]
    with pytest.raises(ValueError, match="ya contiene"):
        pilot.run_pilot(output, 2, 100, configs)


def test_audit_rejects_loss_duplicate_ids_pending_and_incompatible_states(pilot):
    cfg = load_config(overrides={**MINI_OVERRIDES, "n_spectators": 2})
    df = pd.DataFrame({"id": [0, 1], "t_exit": [110, 111], "abandoned": [False, False]}).reindex(
        columns=SPECTATOR_COLUMNS
    )
    df.attrs.update(alarm_triggered=False, stop_time_min=111)
    with pytest.raises(ValueError, match="pérdida"):
        pilot.audit_replica(df.iloc[:1], cfg)
    duplicate = df.copy()
    duplicate["id"] = 0
    with pytest.raises(ValueError, match="duplicación"):
        pilot.audit_replica(duplicate, cfg)
    pending = df.copy()
    pending.loc[0, "t_exit"] = float("nan")
    with pytest.raises(ValueError, match="pendientes"):
        pilot.audit_replica(pending, cfg)
    df.loc[0, "t_safe"] = 50
    with pytest.raises(ValueError, match="incompatibles"):
        pilot.audit_replica(df, cfg)


@pytest.mark.parametrize(("reps", "seed"), [(1, 0), (True, 0), (2, -1), (2, True)])
def test_invalid_execution_arguments(pilot, tmp_path, reps, seed):
    with pytest.raises(ValueError):
        pilot.run_pilot(tmp_path / "pilot", reps, seed)
    assert not (tmp_path / "pilot").exists()

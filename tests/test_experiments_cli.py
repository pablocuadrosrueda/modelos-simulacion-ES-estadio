"""Resolución de nombres de experimento (experiments.py) y CLI."""

from __future__ import annotations

import json
import runpy
from pathlib import Path

import pandas as pd
import pytest

from conftest import MINI_OVERRIDES
from sanmames import experiments
from sanmames.config import REPO_ROOT, deep_merge
from sanmames.experiments import (
    find_experiment_file,
    list_experiments,
    replica_seed,
    run_experiment,
)
from sanmames.metrics import ID_COLUMNS, KPI_COLUMNS


@pytest.fixture
def paired_experiment(tmp_path: Path) -> Path:
    overrides = deep_merge(
        MINI_OVERRIDES,
        {
            "n_spectators": 60,
            "gates_per_zone": 1,
            "arrival_profile": "burst",
            "arrival_profiles": {"burst": [[-1, 0, 1.0]]},
        },
    )
    data = {
        "experiment": "test_pair",
        "label": "Uno y cuatro tornos",
        "question": "Verificación de semillas comunes",
        "variants": [
            {"name": "one", "overrides": deep_merge(overrides, {"turnstiles_per_gate": 1})},
            {"name": "four", "overrides": deep_merge(overrides, {"turnstiles_per_gate": 4})},
        ],
    }
    path = tmp_path / "pair.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture
def cli_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    namespace = runpy.run_path(str(REPO_ROOT / "scripts" / "run_experiment.py"))
    main = namespace["main"]
    monkeypatch.setitem(main.__globals__, "RESULTS_DIR", tmp_path / "results")
    return main


def test_find_by_prefix_and_stem() -> None:
    assert find_experiment_file("X0").stem == "X0_base"
    assert find_experiment_file("X1_2tornos").stem == "X1_2tornos"


def test_ambiguous_prefix() -> None:
    with pytest.raises(ValueError):
        find_experiment_file("X1")


def test_missing() -> None:
    with pytest.raises(FileNotFoundError):
        find_experiment_file("X99")


def test_list_and_seeds() -> None:
    assert "S1_sensibilidad" in list_experiments()
    assert replica_seed(100, 0) == 100 and replica_seed(100, 3) == 103


def test_find_external_path(paired_experiment: Path) -> None:
    assert find_experiment_file(str(paired_experiment)) == paired_experiment


def test_find_filename_with_extension() -> None:
    assert find_experiment_file("X0_base.json").stem == "X0_base"


def test_find_missing_explicit_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="No existe"):
        find_experiment_file(str(tmp_path / "missing.json"))


def test_experiment_rows_seeds_and_real_metrics(paired_experiment: Path) -> None:
    df = run_experiment(str(paired_experiment), n_reps=3, base_seed=100)
    assert list(df.columns) == ID_COLUMNS + KPI_COLUMNS
    assert df["experiment"].tolist() == ["test_pair"] * 6
    assert df["scenario"].tolist() == ["one"] * 3 + ["four"] * 3
    assert df["replica"].tolist() == [0, 1, 2] * 2
    assert df["seed"].tolist() == [100, 101, 102] * 2
    assert (df["n_spectators"] == 60).all()
    assert (df["n_entered"] == 60).all()
    assert df["wait_mean_min"].notna().all()
    assert (
        df.loc[df.scenario == "one", "wait_mean_min"].mean()
        > df.loc[df.scenario == "four", "wait_mean_min"].mean()
    )
    assert df["exit_time_min"].notna().all()
    assert df["evac_time_min"].isna().all()


def test_experiment_reproducible(paired_experiment: Path) -> None:
    first = run_experiment(str(paired_experiment), 2, base_seed=8)
    second = run_experiment(str(paired_experiment), 2, base_seed=8)
    pd.testing.assert_frame_equal(first, second)


def test_common_random_inputs_across_variants(
    paired_experiment: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    samples = []
    real_run = experiments.run_replica

    def record(config, seed):
        df = real_run(config, seed)
        samples.append(df[["id", "t_arrival", "service_s", "speed_mps", "distance_m"]].copy())
        return df

    monkeypatch.setattr(experiments, "run_replica", record)
    run_experiment(str(paired_experiment), 2, base_seed=8)
    pd.testing.assert_frame_equal(samples[0], samples[2])
    pd.testing.assert_frame_equal(samples[1], samples[3])
    assert not samples[0]["t_arrival"].equals(samples[1]["t_arrival"])


@pytest.mark.parametrize("n_reps", [0, -1, True, 1.5])
def test_invalid_replication_count(n_reps) -> None:
    with pytest.raises(ValueError, match="n_reps"):
        run_experiment("configs/dev/i1_mini.json", n_reps)


@pytest.mark.parametrize("seed", [-1, True, 1.5])
def test_invalid_base_seed(seed) -> None:
    with pytest.raises(ValueError, match="base_seed"):
        run_experiment("configs/dev/i1_mini.json", 1, base_seed=seed)


def test_cli_writes_csv(cli_main, paired_experiment: Path, tmp_path: Path, capsys) -> None:
    assert cli_main([str(paired_experiment), "--reps", "2", "--seed", "10"]) == 0
    out = tmp_path / "results" / "pair_kpis.csv"
    df = pd.read_csv(out)
    expected = run_experiment(str(paired_experiment), 2, base_seed=10)
    pd.testing.assert_frame_equal(df, expected)
    assert "KPIs guardados" in capsys.readouterr().out


def test_cli_lists_experiments(cli_main, capsys) -> None:
    assert cli_main(["--list"]) == 0
    assert "X0_base" in capsys.readouterr().out


@pytest.mark.parametrize("args", [["--reps", "0"], ["--seed", "-1"]])
def test_cli_invalid_arguments(cli_main, args, tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        cli_main(["configs/dev/i1_mini.json", *args])
    assert exc.value.code == 2
    assert not (tmp_path / "results").exists()


def test_cli_missing_file(cli_main, capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        cli_main(["missing.json"])
    assert exc.value.code == 2
    assert "no encontrado" in capsys.readouterr().err


def test_cli_base_scenario_supports_all_incidents(cli_main, tmp_path: Path) -> None:
    assert cli_main(["X0", "--reps", "1"]) == 0
    df = pd.read_csv(tmp_path / "results" / "X0_base_kpis.csv")
    assert df.loc[0, "n_spectators"] == df.loc[0, "n_entered"] == 48775
    assert df.loc[0, "n_read_failures"] > 0
    assert df.loc[0, "exit_time_min"] > 0
    assert pd.isna(df.loc[0, "evac_time_min"])

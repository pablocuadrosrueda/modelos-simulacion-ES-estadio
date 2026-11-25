"""T6.1: unidades, colectivos comparables, emparejamiento y exportación real."""

import hashlib
import importlib.util
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def plots(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("plot_results", ROOT / "scripts/plot_results.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def final_data(plots):
    return plots.load_data(ROOT / "results/final")


def test_pairs_align_seeds_and_drop_unshared(plots):
    frame = pd.DataFrame(
        {
            "scenario": ["X0_base", "X0_base", "other", "other", "other"],
            "seed": [1, 2, 2, 3, 1],
            "value": [10, 20, 22, 99, 11],
        }
    )
    assert sorted(plots.sample({"groups": frame}, "groups", "other", "value", paired=True)) == [
        1,
        2,
    ]


def test_rejects_incomplete_campaign_before_export(plots, tmp_path):
    (tmp_path / "manifest.json").write_text('{"completed": false}')
    output = tmp_path / "figures"
    with pytest.raises(ValueError, match="completa"):
        plots.generate(tmp_path, output)
    assert not output.exists()
    with pytest.raises(SystemExit) as exc:
        plots.main(["--data", str(tmp_path), "--output", str(output)])
    assert exc.value.code == 2


@pytest.mark.parametrize("table", ["groups", "audit"])
def test_rejects_misaligned_auxiliary_tables(plots, tmp_path, table):
    for name in plots.SOURCES:
        source = ROOT / "results/final" / name
        (tmp_path / name).write_bytes(source.read_bytes())
    path = tmp_path / f"{table}.csv"
    frame = pd.read_csv(path)
    frame.loc[0, "seed"] = -1
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError, match="Identidades"):
        plots.load_data(tmp_path)


def test_units_cohorts_and_distinct_conflict_indicators(plots, final_data):
    specs = {s[0]: s for s in plots.figure_specs(final_data)}
    for name in ("P1", "P4", "P6"):
        fig, rows = plots.draw_figure(final_data, specs[name])
        plt.close(fig)
        if name == "P1":
            util = next(r for r in rows if r["metric"] == "turnstile_util")
            actual = final_data["kpis"].query("scenario == 'X0_base'").turnstile_util.mean()
            assert util["mean"] == pytest.approx(100 * actual)
        elif name == "P4":
            assert all(r["source"] == "groups" for r in rows)
            delta = next(r for r in rows if r["paired"])
            assert delta["n"] == 180
            assert delta["mean"] == pytest.approx(0.0248, abs=0.00005)
        else:
            duration = next(r for r in rows if r["metric"] == "conflict_duration_mean_min")
            delay = next(r for r in rows if r["metric"] == "conflict_delay_s")
            assert duration["mean"] == pytest.approx(44.6004, abs=0.00005)
            assert duration["unit"] == "min"
            assert delay["mean"] == pytest.approx(291.726, abs=0.0005)
            assert delay["unit"] == "s/persona"


def test_evacuation_counts_include_reference_boundary(plots, final_data):
    spec = next(s for s in plots.figure_specs(final_data) if s[0] == "P8")
    frame = final_data["kpis"].copy()
    for scenario in ("X7_todas_salidas", "X7_salida_bloqueada"):
        indices = frame.index[frame.scenario.eq(scenario)]
        frame.loc[indices, "evac_time_min"] = 9
        frame.loc[indices[:2], "evac_time_min"] = [8, 7]
    final_data["kpis"] = frame
    fig, rows = plots.draw_figure(final_data, spec)
    plt.close(fig)
    counts = [r for r in rows if r["successes"] is not None]
    assert len(counts) == 2
    assert all(r["successes"] == 2 and r["halfwidth"] is None for r in counts)
    assert all(r["mean"] == pytest.approx(100 * 2 / 180) for r in counts)


def test_exports_all_figures_with_exact_source_and_output_hashes(plots, tmp_path):
    paths = plots.generate(ROOT / "results/final", tmp_path)
    assert len(paths) == 18
    assert {p.stem for p in paths} == {f"P{i}" for i in range(1, 9)} | {"S1"}
    assert all(p.stat().st_size > 1000 for p in paths)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    for name, digest in manifest["inputs"].items():
        assert hashlib.sha256((ROOT / "results/final" / name).read_bytes()).hexdigest() == digest
    for name, digest in manifest["outputs"].items():
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == digest
    stats = pd.read_csv(tmp_path / "statistics.csv")
    assert np.isfinite(stats["mean"]).all()
    counts = stats.query("figure == 'P8' and successes.notna()")
    assert counts.successes.tolist() == [163, 0]
    assert counts.n.tolist() == [180, 180]
    assert counts.halfwidth.isna().all()
    assert plt.get_fignums() == []

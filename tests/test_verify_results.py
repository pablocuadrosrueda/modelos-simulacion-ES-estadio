"""T6.2 C: detectar tablas incoherentes, sin volver a simular toda la campaña."""

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def verifier(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "verify_results", ROOT / "scripts/verify_results.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def campaign(verifier, tmp_path):
    for name in [f"{table}.csv" for table in verifier.FILES] + ["manifest.json"]:
        shutil.copyfile(ROOT / "results/final" / name, tmp_path / name)
    return tmp_path


def test_final_campaign_verifies_and_inputs_are_unchanged(verifier, campaign):
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in campaign.iterdir()}
    result = verifier.verify(campaign)
    assert result["replicas"] == 2965 and result["scenarios"] == 19
    assert result["replays"] == []
    assert result["inputs"] == before
    assert before == {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in campaign.iterdir()
    }
    output = campaign / "informe.md"
    assert verifier.main(["--data", str(campaign), "--output", str(output)]) == 0
    report = output.read_text(encoding="utf-8")
    assert "No ejecutada" in report
    assert "Pendiente de A y B" in report


@pytest.mark.parametrize(
    ("table", "column", "value", "message"),
    [
        ("audit", "n_exited", 0, "conservación ordinaria"),
        ("audit", "stop_time_min", 110, "reloj de salida"),
        ("zones", "share_pct", 101, "porcentajes de zona"),
        ("summary", "wait_mean_min_mean", 999, "summary: valores distintos"),
        ("comparisons", "wait_mean_min_mean", 999, "comparisons: valores distintos"),
        ("precision", "relative_halfwidth_pct", 0, "Precisión: relative"),
        ("kpis", "late_pct", 101, "Rango inválido"),
        ("kpis", "exit_time_min", float("nan"), "falta P5"),
    ],
)
def test_rejects_corruption(verifier, campaign, table, column, value, message):
    path = campaign / f"{table}.csv"
    frame = pd.read_csv(path)
    # Comparisons no contiene una fila de X0; las otras tablas sí.
    index = frame.index[frame.scenario.eq("X0_base")][0] if table != "comparisons" else 0
    frame.loc[index, column] = value
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError, match=message):
        verifier.verify(campaign)


def test_rejects_duplicate_cohorts(verifier, campaign):
    path = campaign / "groups.csv"
    frame = pd.read_csv(path)
    frame.iloc[0] = frame.iloc[1]
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError, match="Colectivos P4: identificadores duplicados"):
        verifier.verify(campaign)


def test_reordering_rows_does_not_change_pairing(verifier, campaign):
    for name in verifier.FILES:
        path = campaign / f"{name}.csv"
        frame = pd.read_csv(path)
        frame.iloc[::-1].to_csv(path, index=False)
    assert verifier.verify(campaign)["replicas"] == 2965


def test_bad_replay_is_rejected_instead_of_reporting_success(verifier, campaign, monkeypatch):
    from sanmames.entities import SPECTATOR_COLUMNS

    # Este test comprueba el rechazo de una réplica mal repetida, no la huella del
    # código: se fijan las huellas del manifiesto para que un cambio posterior en
    # un módulo que no simula (p. ej. capacity.py, T6.2 de A) no lo enmascare.
    manifest = json.loads((campaign / "manifest.json").read_text(encoding="utf-8"))
    digests = {k.replace("\\", "/"): v for k, v in manifest["source_sha256"].items()}
    monkeypatch.setattr(
        verifier, "model_digest", lambda path: digests[path.relative_to(ROOT).as_posix()]
    )
    monkeypatch.setattr(
        verifier, "run_replica", lambda cfg, seed: pd.DataFrame(columns=SPECTATOR_COLUMNS)
    )
    with pytest.raises(ValueError, match="identidades del runner"):
        verifier.verify(campaign, replay=True)


def test_failure_preserves_previous_report(verifier, campaign):
    (campaign / "manifest.json").write_text('{"completed":false}', encoding="utf-8")
    output = campaign / "informe.md"
    output.write_text("Informe anterior", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        verifier.main(["--data", str(campaign), "--output", str(output)])
    assert exc.value.code == 2
    assert output.read_text(encoding="utf-8") == "Informe anterior"


def test_model_digest_ignores_crlf_but_detects_code_changes(verifier, tmp_path):
    source = tmp_path / "source.py"
    source.write_bytes(b"x = 1\ny = 2\n")
    expected = verifier.model_digest(source)
    source.write_bytes(b"x = 1\r\ny = 2\r\n")
    assert verifier.model_digest(source) == expected
    source.write_bytes(b"x = 3\r\ny = 2\r\n")
    assert verifier.model_digest(source) != expected

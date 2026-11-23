"""KPIs de entrada (T1.5), con tiempos en minutos y resultados calculados a mano."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from sanmames.config import Config, load_config
from sanmames.entities import INCIDENT_COLUMNS, SPECTATOR_COLUMNS
from sanmames.metrics import KPI_COLUMNS, compute_kpis, queue_length_max


@pytest.fixture
def metrics_config() -> Config:
    return load_config(
        overrides={
            "n_spectators": 4,
            "zones": ["A"],
            "zone_share": [1.0],
            "gates_per_zone": 2,
            "turnstiles_per_gate": 1,
        }
    )


@pytest.fixture
def entry_df() -> pd.DataFrame:
    # Esperas: 0, 2, 10, 0. Accesos: 2, 4, 21, 2.
    # Tres llegan antes del inicio; uno de ellos se sienta después.
    return pd.DataFrame(
        {
            "zone": ["A", "A", "A", "A"],
            "gate": [1, 1, 1, 2],
            "gate_used": [1, 1, 1, 2],
            "t_arrival": [-20.0, -20.0, -20.0, 0.0],
            "t_start_control": [-20.0, -18.0, -10.0, 0.0],
            "t_end_control": [-19.0, -17.0, -9.0, 1.0],
            "t_seated": [-18.0, -16.0, 1.0, 2.0],
        }
    ).reindex(columns=SPECTATOR_COLUMNS)


@pytest.mark.parametrize(
    ("starts", "ends", "expected"),
    [
        ([], [], 0),
        ([0, 1, 2], [4, 3, 5], 3),
        ([0, 2], [2, 4], 1),  # [inicio, fin): no se solapan en t=2.
        ([0, 0, 0], [0, 0, 0], 0),
        ([0, 1, 1, 1], [1, 1, 1, 2], 1),  # Esperas nulas en un empate.
        ([2, 0, 1], [5, 4, 3], 3),  # No requiere ordenar las filas.
        ([math.nan, 1], [5, 3], 1),
        ([0, 1, 2], [math.nan, math.nan, 3], 3),
        ([math.nan], [math.nan], 0),
    ],
)
def test_queue_length_max(starts: list, ends: list, expected: int) -> None:
    assert queue_length_max(pd.Series(starts, dtype=float), pd.Series(ends, dtype=float)) == (
        expected
    )


def test_queue_pairs_rows_by_position() -> None:
    starts = pd.Series([0, 1], index=[10, 20])
    ends = pd.Series([2, 3], index=[20, 10])
    assert queue_length_max(starts, ends) == 2


def test_queue_rejects_negative_duration() -> None:
    with pytest.raises(ValueError, match="preceder"):
        queue_length_max(pd.Series([2.0]), pd.Series([1.0]))


@pytest.mark.parametrize("roundoff", [-1e-14, 1e-14])
def test_queue_ignores_roundoff_in_zero_wait(roundoff: float) -> None:
    assert queue_length_max(pd.Series([-20.0]), pd.Series([-20.0 + roundoff])) == 0


def test_zero_wait_metrics_despite_roundoff(entry_df: pd.DataFrame, metrics_config: Config) -> None:
    entry_df["t_start_control"] = entry_df["t_arrival"] - 1e-14
    entry_df["t_end_control"] = entry_df["t_arrival"] + 1
    entry_df["t_seated"] = entry_df["t_arrival"] + 2
    kpis = compute_kpis(entry_df, metrics_config)
    assert kpis["queue_max_gate"] == 0
    assert kpis["wait_mean_min"] == kpis["wait_p95_min"] == 0


def test_queue_rejects_different_lengths() -> None:
    with pytest.raises(ValueError):
        queue_length_max(pd.Series([0.0, 1.0]), pd.Series([2.0]))


def test_entry_kpis_by_hand(entry_df: pd.DataFrame, metrics_config: Config) -> None:
    kpis = compute_kpis(entry_df, metrics_config)
    assert list(kpis) == KPI_COLUMNS
    assert kpis["n_spectators"] == kpis["n_entered"] == 4
    assert kpis["wait_mean_min"] == pytest.approx(3.0)
    assert kpis["wait_p95_min"] == pytest.approx(8.8)
    # La espera de exactamente 10 minutos no cumple "menos de 10".
    assert kpis["pct_wait_lt_10"] == pytest.approx(75.0)
    assert kpis["queue_max_gate"] == 2
    assert kpis["access_mean_min"] == pytest.approx(7.25)
    assert kpis["late_pct"] == pytest.approx(100 / 3)


def test_utilization_uses_nominal_capacity_and_opening(
    entry_df: pd.DataFrame, metrics_config: Config
) -> None:
    kpis = compute_kpis(entry_df, metrics_config)
    # Cuatro minutos ocupados; dos tornos, incluso estando uno ocioso;
    # apertura en -90 y último fin de control en +1: ventana de 91 minutos.
    assert kpis["turnstile_util"] == pytest.approx(4 / (2 * 91))


def test_queue_max_separates_zones_and_gates(base_config: Config) -> None:
    df = pd.DataFrame(
        {
            "zone": ["A", "A", "A", "B", "B"],
            "gate": [1, 1, 2, 1, 1],
            "t_arrival": [-20.0] * 5,
            "t_start_control": [-19.0] * 5,
            "t_end_control": [-18.0] * 5,
            "t_seated": [-17.0] * 5,
        }
    ).reindex(columns=SPECTATOR_COLUMNS)
    assert compute_kpis(df, base_config)["queue_max_gate"] == 2


def test_future_kpis_remain_nan(entry_df: pd.DataFrame, metrics_config: Config) -> None:
    kpis = compute_kpis(entry_df, metrics_config)
    future = KPI_COLUMNS[KPI_COLUMNS.index("wait_mean_priority_min") :]
    assert all(math.isnan(kpis[name]) for name in future)


def test_empty_replica(metrics_config: Config) -> None:
    kpis = compute_kpis(pd.DataFrame(columns=SPECTATOR_COLUMNS), metrics_config)
    for name in ("n_spectators", "n_entered", "queue_max_gate"):
        assert kpis[name] == 0
    assert all(
        math.isnan(value)
        for name, value in kpis.items()
        if name not in {"n_spectators", "n_entered", "queue_max_gate"}
    )


def test_pending_events_are_not_zero_waits(entry_df: pd.DataFrame, metrics_config: Config) -> None:
    entry_df.loc[2, ["t_start_control", "t_end_control", "t_seated"]] = math.nan
    kpis = compute_kpis(entry_df, metrics_config)
    assert kpis["n_spectators"] == 4
    assert kpis["n_entered"] == 3
    assert kpis["wait_mean_min"] == pytest.approx(2 / 3)
    assert kpis["pct_wait_lt_10"] == 100
    assert kpis["access_mean_min"] == pytest.approx(8 / 3)
    assert kpis["queue_max_gate"] == 2  # Incluye a quien sigue esperando.


def test_no_completed_controls(entry_df: pd.DataFrame, metrics_config: Config) -> None:
    entry_df.loc[:, ["t_start_control", "t_end_control", "t_seated"]] = math.nan
    kpis = compute_kpis(entry_df, metrics_config)
    assert kpis["n_entered"] == 0
    assert kpis["queue_max_gate"] == 3
    for name in ("wait_mean_min", "wait_p95_min", "pct_wait_lt_10", "access_mean_min"):
        assert math.isnan(kpis[name])
    assert math.isnan(kpis["turnstile_util"])


def test_wait_observed_before_control_finishes(
    entry_df: pd.DataFrame, metrics_config: Config
) -> None:
    entry_df.loc[2, ["t_end_control", "t_seated"]] = math.nan
    kpis = compute_kpis(entry_df, metrics_config)
    assert kpis["n_entered"] == 3
    assert kpis["wait_mean_min"] == pytest.approx(3.0)
    assert kpis["access_mean_min"] == pytest.approx(8 / 3)


def test_late_boundaries(entry_df: pd.DataFrame, metrics_config: Config) -> None:
    entry_df["t_arrival"] = [-1.0, -1.0, 0.0, 1.0]
    entry_df["t_start_control"] = entry_df["t_arrival"]
    entry_df["t_end_control"] = entry_df["t_arrival"] + 0.1
    entry_df["t_seated"] = [0.0, 0.1, 1.0, 2.0]
    assert compute_kpis(entry_df, metrics_config)["late_pct"] == 50


def test_no_arrivals_before_kickoff(entry_df: pd.DataFrame, metrics_config: Config) -> None:
    entry_df["t_arrival"] = [0.0, 1.0, 2.0, 3.0]
    entry_df["t_start_control"] = entry_df["t_arrival"]
    entry_df["t_end_control"] = entry_df["t_arrival"] + 1
    entry_df["t_seated"] = entry_df["t_arrival"] + 2
    assert math.isnan(compute_kpis(entry_df, metrics_config)["late_pct"])


def test_input_is_not_modified(entry_df: pd.DataFrame, metrics_config: Config) -> None:
    entry_df.attrs["seed"] = 123
    entry_df.attrs["incidents"] = pd.DataFrame(columns=INCIDENT_COLUMNS)
    original = entry_df.copy(deep=True)
    compute_kpis(entry_df, metrics_config)
    pd.testing.assert_frame_equal(entry_df, original)
    assert entry_df.attrs["seed"] == original.attrs["seed"]
    pd.testing.assert_frame_equal(entry_df.attrs["incidents"], original.attrs["incidents"])

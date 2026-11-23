"""Estadística entre réplicas: valores de tabla t y diferencias emparejadas a mano."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from sanmames.analysis import (
    compare_with_baseline,
    confidence_interval,
    required_replications,
    summarize,
)
from sanmames.metrics import KPI_COLUMNS


@pytest.fixture
def paired_kpis() -> pd.DataFrame:
    # Las filas de la alternativa se desordenan: emparejar por posición daría
    # diferencias falsas, mientras que por semilla todas son -3 minutos.
    return pd.DataFrame(
        {
            "scenario": ["X0_base"] * 3 + ["improved"] * 3,
            "seed": [1, 2, 3, 3, 1, 2],
            "replica": [0, 1, 2, 0, 1, 2],
            "wait_mean_min": [10.0, 20.0, 30.0, 27.0, 7.0, 17.0],
        }
    )


def test_confidence_interval_against_t_table() -> None:
    # n=5, media=3, s²=2.5 y t(0.975,4)=2.776445105.
    mean, halfwidth = confidence_interval([1, 2, 3, 4, 5])
    assert mean == 3
    assert halfwidth == pytest.approx(1.9632431615)


def test_interval_for_constant_sample() -> None:
    assert confidence_interval([4, 4, 4]) == (4, 0)


def test_interval_ignores_missing_kpis() -> None:
    assert confidence_interval([1, math.nan, 2, 3, 4, 5]) == confidence_interval([1, 2, 3, 4, 5])


def test_interval_with_one_replica_does_not_claim_zero_uncertainty() -> None:
    mean, halfwidth = confidence_interval([math.nan, 4])
    assert mean == 4
    assert math.isnan(halfwidth)


def test_interval_without_observations() -> None:
    assert all(math.isnan(value) for value in confidence_interval([math.nan]))
    assert all(math.isnan(value) for value in confidence_interval([]))


def test_higher_confidence_widens_interval() -> None:
    values = [1, 2, 3, 4, 5]
    assert confidence_interval(values, 0.99)[1] > confidence_interval(values, 0.95)[1]


@pytest.mark.parametrize("level", [0, 1, -0.1, 1.1, math.nan])
def test_invalid_confidence_level(level: float) -> None:
    with pytest.raises(ValueError, match="level"):
        confidence_interval([1, 2], level)


@pytest.mark.parametrize("values", [[math.inf, 1], [-math.inf, 1], [[1, 2]]])
def test_invalid_observations(values) -> None:
    with pytest.raises(ValueError):
        confidence_interval(values)


@pytest.mark.parametrize("values", [[8, 10, 12], [-8, -10, -12]])
def test_required_replications_from_pilot(values: list[float]) -> None:
    # n=3, s=2, abs(media)=10, h=1, t(0.975,2)=4.30265273.
    # ceil((4.30265273 * 2 / 1)^2) = 75 réplicas totales.
    assert required_replications(values, rel_halfwidth=0.1) == 75


def test_required_replications_keep_existing_pilot() -> None:
    assert required_replications([10, 10, 10]) == 3
    assert required_replications([0, 0, 0]) == 3
    assert required_replications([8, 10, 12], rel_halfwidth=10) == 3


def test_required_replications_ignore_nan() -> None:
    assert required_replications([8, math.nan, 10, 12], rel_halfwidth=0.1) == 75


def test_zero_mean_with_variability_needs_absolute_precision() -> None:
    with pytest.raises(ValueError, match="Media cero"):
        required_replications([-1, 0, 1])


@pytest.mark.parametrize("values", [[], [1], [math.nan, 1]])
def test_pilot_needs_two_valid_replicas(values: list[float]) -> None:
    with pytest.raises(ValueError, match="dos réplicas"):
        required_replications(values)


@pytest.mark.parametrize("precision", [0, -0.1, math.inf, math.nan])
def test_invalid_relative_precision(precision: float) -> None:
    with pytest.raises(ValueError, match="rel_halfwidth"):
        required_replications([1, 2, 3], rel_halfwidth=precision)


def test_summarize_per_scenario() -> None:
    df = pd.DataFrame(
        {
            "scenario": ["base"] * 5 + ["other"] * 3,
            "seed": [1, 2, 3, 4, 5, 1, 2, 3],
            "wait_mean_min": [1, 2, 3, 4, 5, 2, 2, 2],
        }
    )
    result = summarize(df).set_index("scenario")
    assert result.loc["base", "wait_mean_min_mean"] == 3
    assert result.loc["base", "wait_mean_min_halfwidth"] == pytest.approx(1.9632431615)
    assert result.loc["base", "wait_mean_min_n"] == 5
    assert result.loc["other", "wait_mean_min_mean"] == 2
    assert result.loc["other", "wait_mean_min_halfwidth"] == 0
    assert result.loc["other", "wait_mean_min_n"] == 3
    assert result["evac_time_min_mean"].isna().all()
    assert (result["evac_time_min_n"] == 0).all()


def test_summary_schema_for_empty_input() -> None:
    result = summarize(pd.DataFrame(columns=["scenario"]))
    expected = ["scenario"] + [
        f"{name}_{suffix}" for name in KPI_COLUMNS for suffix in ("mean", "halfwidth", "n")
    ]
    assert list(result.columns) == expected
    assert result.empty


def test_comparison_pairs_by_seed_and_preserves_direction(paired_kpis: pd.DataFrame) -> None:
    result = compare_with_baseline(paired_kpis)
    assert result["scenario"].tolist() == ["improved"]
    assert result.loc[0, "baseline"] == "X0_base"
    assert result.loc[0, "wait_mean_min_mean"] == -3
    assert result.loc[0, "wait_mean_min_halfwidth"] == 0
    assert result.loc[0, "wait_mean_min_n"] == 3


def test_comparison_uses_only_common_seeds(paired_kpis: pd.DataFrame) -> None:
    paired_kpis.loc[3, "seed"] = 999
    result = compare_with_baseline(paired_kpis)
    assert result.loc[0, "wait_mean_min_mean"] == -3
    assert result.loc[0, "wait_mean_min_n"] == 2


def test_comparison_requires_both_values_in_pair(paired_kpis: pd.DataFrame) -> None:
    paired_kpis.loc[3, "wait_mean_min"] = math.nan  # Alternativa, semilla 3.
    paired_kpis.loc[1, "wait_mean_min"] = math.nan  # Base, semilla 2.
    result = compare_with_baseline(paired_kpis)
    assert result.loc[0, "wait_mean_min_mean"] == -3
    assert result.loc[0, "wait_mean_min_n"] == 1
    assert math.isnan(result.loc[0, "wait_mean_min_halfwidth"])


def test_comparison_without_common_seeds(paired_kpis: pd.DataFrame) -> None:
    paired_kpis.loc[3:, "seed"] += 100
    result = compare_with_baseline(paired_kpis)
    assert result.loc[0, "wait_mean_min_n"] == 0
    assert math.isnan(result.loc[0, "wait_mean_min_mean"])


def test_comparison_with_only_baseline(paired_kpis: pd.DataFrame) -> None:
    assert compare_with_baseline(paired_kpis.iloc[:3]).empty


def test_missing_baseline(paired_kpis: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="base no encontrado"):
        compare_with_baseline(paired_kpis, baseline="missing")


@pytest.mark.parametrize("operation", [summarize, compare_with_baseline])
def test_duplicate_seed_is_not_an_independent_replica(operation, paired_kpis: pd.DataFrame) -> None:
    df = pd.concat([paired_kpis, paired_kpis.iloc[:1]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicadas"):
        operation(df)


def test_missing_pairing_key(paired_kpis: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="identificativas"):
        compare_with_baseline(paired_kpis.drop(columns="seed"))


@pytest.mark.parametrize("name", ["scenario", "seed"])
def test_null_identifiers(name: str, paired_kpis: pd.DataFrame) -> None:
    paired_kpis.loc[0, name] = None
    with pytest.raises(ValueError, match=name):
        compare_with_baseline(paired_kpis)


def test_comparison_rejects_infinite_inputs(paired_kpis: pd.DataFrame) -> None:
    paired_kpis.loc[0, "wait_mean_min"] = np.inf
    with pytest.raises(ValueError, match="infinitos"):
        compare_with_baseline(paired_kpis)


def test_analysis_does_not_modify_input(paired_kpis: pd.DataFrame) -> None:
    original = paired_kpis.copy(deep=True)
    summarize(paired_kpis)
    compare_with_baseline(paired_kpis)
    pd.testing.assert_frame_equal(paired_kpis, original)

"""Resolución de nombres de experimento (experiments.py) y CLI."""

from __future__ import annotations

import pytest

from sanmames.experiments import find_experiment_file, list_experiments, replica_seed


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

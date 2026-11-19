"""Fixtures compartidas."""

from __future__ import annotations

import pytest

from sanmames.config import Config, load_config

# Escenario pequeño para tests rápidos: una macrozona, sin incidencias.
MINI_OVERRIDES = {
    "name": "test_mini",
    "n_spectators": 600,
    "zones": ["A"],
    "zone_share": [1.0],
    "gates_per_zone": 2,
    "incidents": {
        "seat_conflict": {"enabled": False},
        "read_failure": {"enabled": False},
        "turnstile_failure": {"enabled": False},
        "gate_closure": {"enabled": False},
    },
}


@pytest.fixture
def base_config() -> Config:
    return load_config()


@pytest.fixture
def mini_config() -> Config:
    return load_config(overrides=MINI_OVERRIDES)

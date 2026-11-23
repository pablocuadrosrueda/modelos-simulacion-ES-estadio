"""T2.8: indicadores por grupo, conflictos y cola de la puerta realmente usada."""

from __future__ import annotations

import math
from dataclasses import replace

import pandas as pd
import pytest

from conftest import MINI_OVERRIDES
from sanmames import runner
from sanmames.config import Config, deep_merge, load_config
from sanmames.entities import INCIDENT_COLUMNS, SPECTATOR_COLUMNS
from sanmames.metrics import compute_kpis


def frame(rows: list[dict], incidents: list[dict] | None = None) -> pd.DataFrame:
    df = pd.DataFrame(rows).reindex(columns=SPECTATOR_COLUMNS)
    df.attrs["incidents"] = pd.DataFrame(incidents or [], columns=INCIDENT_COLUMNS)
    return df


def test_groups_defined_by_config_even_under_fifo(mini_config: Config) -> None:
    df = frame(
        [
            {
                "zone": "A",
                "gate": 1,
                "gate_used": 1,
                "group": "elderly",
                "t_arrival": 0,
                "t_start_control": 2,
            },
            {
                "zone": "A",
                "gate": 1,
                "gate_used": 1,
                "group": "standard",
                "t_arrival": 0,
                "t_start_control": 6,
            },
            {
                "zone": "A",
                "gate": 1,
                "gate_used": 1,
                "group": "elderly",
                "t_arrival": 0,
                "t_start_control": math.nan,
            },
        ]
    )
    cfg = replace(mini_config, priority_groups=("elderly",))
    kpis = compute_kpis(df, cfg)
    assert kpis["wait_mean_priority_min"] == 2
    assert kpis["wait_mean_rest_min"] == 6
    assert kpis["group_wait_diff_min"] == -4


def test_no_priority_group_gives_nan_difference(mini_config: Config) -> None:
    df = frame(
        [
            {
                "zone": "A",
                "gate": 1,
                "gate_used": 1,
                "group": "standard",
                "t_arrival": 0,
                "t_start_control": 3,
            }
        ]
    )
    kpis = compute_kpis(df, mini_config)
    assert math.isnan(kpis["wait_mean_priority_min"])
    assert kpis["wait_mean_rest_min"] == 3
    assert math.isnan(kpis["group_wait_diff_min"])


def test_queue_uses_actual_gate_and_ignores_not_arrived(mini_config: Config) -> None:
    df = frame(
        [
            {"zone": "A", "gate": 1, "gate_used": 1, "t_arrival": 0, "t_start_control": 2},
            {"zone": "A", "gate": 1, "gate_used": 2, "t_arrival": 0, "t_start_control": 2},
            {"zone": "A", "gate": 2, "gate_used": -1, "t_arrival": 10},
        ]
    )
    assert compute_kpis(df, mini_config)["queue_max_gate"] == 1


def test_conflict_delay_uses_overlap_and_excludes_conflicting_spectator(
    mini_config: Config,
) -> None:
    def row(block, start, end, conflict=False, zone="A"):
        return {
            "zone": zone,
            "block": block,
            "gate": 1,
            "gate_used": 1,
            "t_arrival": -10,
            "t_start_control": -9,
            "t_end_control": -8,
            "t_vomitory": start,
            "t_seated": end,
            "conflict": conflict,
        }

    df = frame(
        [
            row(1, 1, 4),  # Solapa I1 de [2,5): 180 s.
            row(1, 5, 6),  # Empieza en el fin de I1: 60 s, sin exposición.
            row(2, 1, 2),  # Otro bloque: 60 s.
            row(1, 1, 2, zone="B"),  # Misma numeración, otra zona: 60 s.
            row(1, 2, 100, conflict=True),  # El causante no entra en el contraste.
        ],
        [
            {
                "kind": "I1",
                "zone": "A",
                "resource": "A-B1",
                "t_start": 2,
                "t_end": 5,
                "spectator_id": 4,
            }
        ],
    )
    assert compute_kpis(df, mini_config)["conflict_delay_s"] == 120


def test_incident_counts_and_missing_comparison_population(mini_config: Config) -> None:
    df = frame(
        [],
        [
            {"kind": "I1", "t_start": 0},
            {"kind": "I2", "t_start": 1},
            {"kind": "I3", "t_start": 2},
            {"kind": "I3", "t_start": 200},
            {"kind": "I4", "t_start": 3},
        ],
    )
    kpis = compute_kpis(df, mini_config)
    assert kpis["n_conflicts"] == 1
    assert kpis["n_read_failures"] == 1
    assert kpis["n_turnstile_failures"] == 2  # Todas las registradas, sin filtro temporal oculto.
    assert math.isnan(kpis["conflict_delay_s"])


def test_incident_integration_and_capacities(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = load_config(
        overrides=deep_merge(
            MINI_OVERRIDES,
            {
                "n_spectators": 20,
                "gates_per_zone": 1,
                "turnstiles_per_gate": 2,
                "vomitory_capacity": 2,
                "stewards_per_zone": 1,
                "arrival_profile": "burst",
                "arrival_profiles": {"burst": [[-1, 0, 1.0]]},
                "queue_discipline": "priority",
                "priority_groups": ["elderly"],
                "incidents": {
                    "seat_conflict": {
                        "enabled": True,
                        "prob": 1.0,
                        "resolution_min": {"low": 0.1, "mode": 0.1, "high": 0.1},
                    },
                    "turnstile_failure": {
                        "enabled": True,
                        "mtbf_min": 0.05,
                        "repair_min": {"low": 0.01, "high": 0.01},
                    },
                    "gate_closure": {"enabled": True, "start_min": -1, "duration_min": 0.2},
                },
            },
        )
    )
    contexts = []
    original_env = runner.simpy.Environment
    original_build = runner.build_entry_resources
    peaks = {"entry": 0, "vomitory": 0, "steward": 0}

    class ObservedEnvironment(original_env):
        def step(self):
            super().step()
            if not contexts:
                return
            ctx = contexts[0]
            for label, resources in (
                ("entry", ctx.entry.turnstiles),
                ("vomitory", ctx.stadium.vomitories),
                ("steward", ctx.stadium.stewards),
            ):
                for resource in resources.values():
                    assert resource.count <= resource.capacity
                    peaks[label] = max(peaks[label], resource.count)

    def capture(ctx):
        contexts.append(ctx)
        return original_build(ctx)

    monkeypatch.setattr(runner.simpy, "Environment", ObservedEnvironment)
    monkeypatch.setattr(runner, "build_entry_resources", capture)
    df = runner.run_replica(cfg, seed=7)
    assert df["t_seated"].notna().all()
    assert (df["t_start_control"] >= -0.8 - 1e-9).all()
    kpis = compute_kpis(df, cfg)
    assert kpis["n_conflicts"] == 20
    assert kpis["n_turnstile_failures"] > 0
    assert set(df.attrs["incidents"]["kind"]) == {"I1", "I3", "I4"}
    assert peaks == {"entry": 2, "vomitory": 2, "steward": 1}

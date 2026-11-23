"""Carga y validación de configuraciones (config.py)."""

from __future__ import annotations

import math

import pytest

from sanmames.config import (
    BASE_CONFIG_PATH,
    EXPERIMENTS_DIR,
    ArrivalBin,
    Config,
    ConfigError,
    deep_merge,
    load_config,
    load_experiment,
)

EXPERIMENT_FILES = sorted(EXPERIMENTS_DIR.glob("*.json"))


def test_base_loads_with_memoria_values(base_config: Config) -> None:
    c = base_config
    assert c.n_spectators == 48775
    assert c.zones == ("A", "B", "C", "D")
    assert c.n_gates == 24
    assert c.n_turnstiles == 72
    assert c.vomitory_capacity == 8
    assert c.exit_rate_per_exit_min == pytest.approx(264)
    assert (c.t_open_min, c.t_start_min, c.t_end_min) == (-90, 0, 105)
    assert c.service_time_s.mean == pytest.approx(4)
    assert c.incidents.seat_conflict.prob == pytest.approx(0.005)
    assert c.incidents.read_failure.prob == pytest.approx(0.03)
    assert c.incidents.turnstile_failure.mtbf_min == 240
    assert not c.incidents.gate_closure.enabled
    assert not c.emergency.enabled
    assert c.tier_of_block(5) == "lower" and c.tier_of_block(6) == "upper"
    assert isinstance(c.active_profile[0], ArrivalBin)


def test_there_are_experiment_files() -> None:
    stems = {p.stem for p in EXPERIMENT_FILES}
    for code in ("X0", "X1", "X2", "X3", "X4", "X5", "X6", "X7", "S1"):
        assert any(s.startswith(code + "_") for s in stems), code


@pytest.mark.parametrize("path", EXPERIMENT_FILES, ids=lambda p: p.stem)
def test_every_experiment_loads(path) -> None:
    exp = load_experiment(path)
    assert exp.configs
    names = [c.name for c in exp.configs]
    assert len(set(names)) == len(names)
    for cfg in exp.configs:
        assert isinstance(cfg, Config)


def test_experiments_change_expected_factor(base_config: Config) -> None:
    by_stem = {p.stem: load_experiment(p).configs[0] for p in EXPERIMENT_FILES}
    assert by_stem["X0_base"].name == "X0_base"
    assert by_stem["X1_2tornos"].turnstiles_per_gate == 2
    assert by_stem["X1_4tornos"].turnstiles_per_gate == 4
    assert by_stem["X2_anticipado"].arrival_profile == "anticipated"
    assert by_stem["X3_prioridad"].queue_discipline == "priority"
    assert by_stem["X4_escalonada"].exit_policy == "staggered"
    x5 = by_stem["X5_3acomodadores"]
    assert x5.stewards_per_zone == 3
    assert x5.incidents.seat_conflict.prob == pytest.approx(0.01)
    # la fusión profunda conserva los hermanos no tocados
    base_res = base_config.incidents.seat_conflict.resolution_min
    assert x5.incidents.seat_conflict.resolution_min == base_res
    assert by_stem["X6_sin_redireccion"].incidents.gate_closure.enabled
    assert not by_stem["X6_sin_redireccion"].redirect_on_gate_closure
    assert by_stem["X7_salida_bloqueada"].emergency.blocked_exit
    assert by_stem["X7_todas_salidas"].emergency.enabled


def test_s1_variants() -> None:
    exp = load_experiment(EXPERIMENTS_DIR / "S1_sensibilidad.json")
    assert len(exp.configs) == 6
    vel = next(c for c in exp.configs if c.name == "S1_vel_-15")
    assert vel.speed_mps.mean == pytest.approx(1.45 * 0.85)
    assert vel.speed_mps.sd == pytest.approx(0.23)  # resto intacto


def _all_configs() -> list[Config]:
    cfgs = [load_config()]
    for p in EXPERIMENT_FILES:
        cfgs.extend(load_experiment(p).configs)
    return cfgs


@pytest.mark.parametrize("cfg", _all_configs(), ids=lambda c: c.name)
def test_arrival_profiles_sum_to_one(cfg: Config) -> None:
    for name, bins in cfg.arrival_profiles.items():
        assert math.isclose(sum(b.prob for b in bins), 1.0, abs_tol=1e-9), name


def test_anticipated_profile_matches_memoria(base_config: Config) -> None:
    base = [b.prob for b in base_config.arrival_profiles["base"]]
    ant = [b.prob for b in base_config.arrival_profiles["anticipated"]]
    moved = 0.30 * (base[4] + base[5])  # 30 % de los últimos 30 min
    assert ant[2] + ant[3] == pytest.approx(base[2] + base[3] + moved)
    assert ant[4] + ant[5] == pytest.approx(base[4] + base[5] - moved)


def test_unknown_key_raises() -> None:
    with pytest.raises(ConfigError, match="desconocidas"):
        load_config(overrides={"tornos": 3})


def test_unknown_nested_key_raises() -> None:
    with pytest.raises(ConfigError, match="desconocidas"):
        load_config(overrides={"incidents": {"seat_conflict": {"probability": 0.1}}})


def test_wrong_type_raises() -> None:
    with pytest.raises(ConfigError):
        load_config(overrides={"turnstiles_per_gate": 2.5})


@pytest.mark.parametrize(
    "overrides",
    [
        {"zone_share": [0.5, 0.5, 0.5, 0.5]},
        {"groups": {"standard": {"share": 0.5}}},
        {"arrival_profile": "inexistente"},
        {"arrival_profiles": {"base": [[-90, 0, 0.5], [0, 30, 0.4]]}},
        {"queue_discipline": "lifo"},
        {"priority_groups": ["vip"]},
        {"service_time_s": {"low": 5, "mode": 4, "high": 6}},
        {"incidents": {"gate_closure": {"gate": 7}}},
    ],
)
def test_semantic_validation(overrides) -> None:
    with pytest.raises(ConfigError):
        load_config(overrides=overrides)


def test_deep_merge_does_not_mutate() -> None:
    base = {"a": {"b": 1, "c": 2}, "l": [1, 2]}
    out = deep_merge(base, {"a": {"b": 9}, "l": [3]})
    assert out == {"a": {"b": 9, "c": 2}, "l": [3]}
    assert base == {"a": {"b": 1, "c": 2}, "l": [1, 2]}


def test_mini_config_single_zone(mini_config: Config) -> None:
    assert mini_config.zones == ("A",)
    assert mini_config.n_spectators == 600


def test_raw_keeps_merged_dict() -> None:
    cfg = load_config(BASE_CONFIG_PATH, {"turnstiles_per_gate": 4})
    assert cfg.raw["turnstiles_per_gate"] == 4


def test_gate_closure_starts_in_peak_hour(base_config: Config) -> None:
    """D31: P7 habla de un cierre «en hora punta»; el cierre debe caer en la franja más cargada."""
    gc = base_config.incidents.gate_closure
    profile = base_config.active_profile

    def density(b: ArrivalBin) -> float:
        return b.prob / (b.end_min - b.start_min)

    first = next(b for b in profile if b.start_min <= gc.start_min < b.end_min)
    assert density(first) == pytest.approx(max(density(b) for b in profile))
    assert gc.start_min == -30 and gc.duration_min == 10
    # el cierre termina antes de que acabe la punta
    assert gc.start_min + gc.duration_min <= max(
        b.end_min for b in profile if density(b) == pytest.approx(max(map(density, profile)))
    )

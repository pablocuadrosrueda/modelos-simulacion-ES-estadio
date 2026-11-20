"""Generación de espectadores y llegadas (arrivals.py, T1.1)."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest
from scipy.stats import chisquare

from sanmames.arrivals import (
    generate_spectators,
    sample_arrival_times,
    sample_service_times,
    sample_truncated_normal,
)
from sanmames.config import Config, TruncNormal, load_config
from sanmames.entities import Spectator
from sanmames.rng import RngStreams

N_BIG = 48_775
ALPHA = 0.001  # nivel de los contrastes: un fallo espurio cada 1000 ejecuciones


@pytest.fixture(scope="module")
def spectators() -> tuple[Config, list[Spectator]]:
    cfg = load_config()
    return cfg, generate_spectators(cfg, RngStreams(20261105))


# -- sample_arrival_times ---------------------------------------------------


@pytest.mark.parametrize("profile_name", ["base", "anticipated"])
def test_arrival_profile_reproduced_chi2(base_config: Config, profile_name: str) -> None:
    profile = base_config.arrival_profiles[profile_name]
    t = sample_arrival_times(profile, N_BIG, RngStreams(1)["arrivals"])
    edges = [profile[0].start_min] + [b.end_min for b in profile]
    observed, _ = np.histogram(t, bins=edges)
    expected = np.array([b.prob for b in profile]) * N_BIG
    assert observed.sum() == N_BIG
    assert chisquare(observed, expected).pvalue > ALPHA


def test_arrival_times_within_profile_and_uniform_in_bin(base_config: Config) -> None:
    profile = base_config.active_profile
    t = sample_arrival_times(profile, N_BIG, RngStreams(2)["arrivals"])
    assert t.min() >= profile[0].start_min
    assert t.max() < profile[-1].end_min
    # Dentro de la franja punta (-30, -15) el instante es uniforme: 3 subintervalos de 5 min.
    peak = t[(t >= -30) & (t < -15)]
    observed, _ = np.histogram(peak, bins=[-30, -25, -20, -15])
    assert chisquare(observed).pvalue > ALPHA


def test_arrival_times_deterministic(base_config: Config) -> None:
    a = sample_arrival_times(base_config.active_profile, 100, RngStreams(3)["arrivals"])
    b = sample_arrival_times(base_config.active_profile, 100, RngStreams(3)["arrivals"])
    np.testing.assert_array_equal(a, b)


# -- sample_truncated_normal ------------------------------------------------


def test_truncated_normal_respects_range_and_mean(base_config: Config) -> None:
    p = base_config.speed_mps
    x = sample_truncated_normal(p, N_BIG, RngStreams(4)["speed"])
    assert x.shape == (N_BIG,)
    assert x.min() >= p.min and x.max() <= p.max
    # Truncado casi simétrico y lejano (±3 sd): media y sd próximas a las nominales.
    assert abs(x.mean() - p.mean) < 0.01
    assert abs(x.std() - p.sd) < 0.01


def test_truncated_normal_tight_range() -> None:
    p = TruncNormal(mean=1.0, sd=1.0, min=0.9, max=1.1)
    x = sample_truncated_normal(p, 10_000, RngStreams(5)["speed"])
    assert x.min() >= 0.9 and x.max() <= 1.1
    assert 0.995 < x.mean() < 1.005


def test_truncated_normal_zero_sd() -> None:
    p = TruncNormal(mean=1.45, sd=0.0, min=0.6, max=2.2)
    np.testing.assert_array_equal(sample_truncated_normal(p, 5, RngStreams(6)["speed"]), 1.45)


# -- generate_spectators ----------------------------------------------------


def test_generate_count_ids_and_order(spectators: tuple[Config, list[Spectator]]) -> None:
    cfg, sps = spectators
    assert len(sps) == cfg.n_spectators
    assert [s.id for s in sps] == list(range(cfg.n_spectators))
    t = [s.t_arrival for s in sps]
    assert t == sorted(t)


def test_generate_only_initial_attributes(spectators: tuple[Config, list[Spectator]]) -> None:
    _, sps = spectators
    defaults = Spectator(0, "A", 1, 1, "lower", "standard", 1.0, 100.0, 0.0, 4.0)
    sim_fields = [f.name for f in dataclasses.fields(Spectator)][10:]
    for f in sim_fields:
        d = getattr(defaults, f)
        for s in sps[:200]:
            v = getattr(s, f)
            assert v == d or (isinstance(d, float) and np.isnan(v) and np.isnan(d))


def test_zone_share_matches(spectators: tuple[Config, list[Spectator]]) -> None:
    cfg, sps = spectators
    zones = [s.zone for s in sps]
    observed = [zones.count(z) for z in cfg.zones]
    expected = np.array(cfg.zone_share) * len(sps)
    assert chisquare(observed, expected).pvalue > ALPHA


def test_uneven_zone_share() -> None:
    cfg = load_config(overrides={"n_spectators": 20_000, "zone_share": [0.4, 0.3, 0.2, 0.1]})
    zones = [s.zone for s in generate_spectators(cfg, RngStreams(8))]
    observed = [zones.count(z) for z in cfg.zones]
    assert chisquare(observed, np.array(cfg.zone_share) * 20_000).pvalue > ALPHA


def test_gates_and_blocks_uniform(spectators: tuple[Config, list[Spectator]]) -> None:
    cfg, sps = spectators
    gates = np.bincount([s.gate for s in sps], minlength=cfg.gates_per_zone + 1)
    blocks = np.bincount([s.block for s in sps], minlength=cfg.blocks_per_zone + 1)
    assert gates[0] == 0 and len(gates) == cfg.gates_per_zone + 1
    assert blocks[0] == 0 and len(blocks) == cfg.blocks_per_zone + 1
    assert chisquare(gates[1:]).pvalue > ALPHA
    assert chisquare(blocks[1:]).pvalue > ALPHA


def test_tier_follows_block(spectators: tuple[Config, list[Spectator]]) -> None:
    cfg, sps = spectators
    for s in sps:
        assert s.tier == ("lower" if s.block in cfg.lower_tier_blocks else "upper")


def test_group_share_matches(spectators: tuple[Config, list[Spectator]]) -> None:
    cfg, sps = spectators
    groups = [s.group for s in sps]
    names = list(cfg.groups)
    assert set(groups) <= set(names)
    observed = [groups.count(g) for g in names]
    expected = np.array([cfg.groups[g].share for g in names]) * len(sps)
    assert chisquare(observed, expected).pvalue > ALPHA


def test_speed_and_distance_ranges(spectators: tuple[Config, list[Spectator]]) -> None:
    cfg, sps = spectators
    sp = cfg.speed_mps
    for s in sps:
        f = cfg.groups[s.group].speed_factor
        assert sp.min * f - 1e-12 <= s.speed_mps <= sp.max * f + 1e-12
        assert cfg.distance_m.low <= s.distance_m <= cfg.distance_m.high
    std = np.array([s.speed_mps for s in sps if s.group == "standard"])
    assert abs(std.mean() - sp.mean) < 0.01
    d = np.array([s.distance_m for s in sps])
    assert abs(d.mean() - cfg.distance_m.mean) < 1.0


def test_service_times_range_and_mean(spectators: tuple[Config, list[Spectator]]) -> None:
    cfg, sps = spectators
    st = cfg.service_time_s
    x = np.array([s.service_s for s in sps])
    assert x.min() >= st.low and x.max() <= st.high
    assert abs(x.mean() - st.mean) < 0.03


def test_service_times_degenerate_and_count() -> None:
    cfg = load_config(overrides={"service_time_s": {"low": 4, "mode": 4, "high": 4}})
    rng = RngStreams(1)["service"]
    assert set(sample_service_times(cfg.service_time_s, 50, rng)) == {4.0}
    # consume exactamente n números del flujo (alineación de números aleatorios comunes)
    a, b = RngStreams(2)["service"], RngStreams(2)["service"]
    sample_service_times(load_config().service_time_s, 100, a)
    b.triangular(2, 4, 6, size=100)
    assert a.random() == b.random()


def _initial(sps: list[Spectator]) -> list[tuple]:
    """Atributos iniciales (los NaN de los campos de simulación impiden usar ``==``)."""
    return [dataclasses.astuple(s)[:10] for s in sps]


def test_generate_deterministic(mini_config: Config) -> None:
    a = generate_spectators(mini_config, RngStreams(11))
    b = generate_spectators(mini_config, RngStreams(11))
    c = generate_spectators(mini_config, RngStreams(12))
    assert _initial(a) == _initial(b)
    assert _initial(a) != _initial(c)


def test_profile_change_keeps_other_attributes(base_config: Config) -> None:
    """Números aleatorios comunes: cambiar el perfil solo cambia las llegadas."""
    x2 = load_config(overrides={"arrival_profile": "anticipated"})
    a = generate_spectators(base_config, RngStreams(13))
    b = generate_spectators(x2, RngStreams(13))
    for sa, sb in zip(a, b, strict=True):
        assert (sa.zone, sa.gate, sa.block, sa.group, sa.speed_mps, sa.distance_m) == (
            sb.zone,
            sb.gate,
            sb.block,
            sb.group,
            sb.speed_mps,
            sb.distance_m,
        )
    assert [s.t_arrival for s in a] != [s.t_arrival for s in b]

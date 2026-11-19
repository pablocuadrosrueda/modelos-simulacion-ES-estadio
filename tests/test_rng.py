"""Flujos aleatorios independientes (rng.py)."""

from __future__ import annotations

import numpy as np
import pytest

from sanmames.rng import STREAM_NAMES, RngStreams


def test_same_seed_reproduces() -> None:
    a, b = RngStreams(42), RngStreams(42)
    for name in STREAM_NAMES:
        np.testing.assert_array_equal(a[name].random(10), b[name].random(10))


def test_different_seeds_differ() -> None:
    a, b = RngStreams(1)["service"].random(10), RngStreams(2)["service"].random(10)
    assert not np.array_equal(a, b)


def test_streams_differ_from_each_other() -> None:
    r = RngStreams(7)
    draws = {name: tuple(r[name].random(5)) for name in STREAM_NAMES}
    assert len(set(draws.values())) == len(STREAM_NAMES)


def test_consuming_one_stream_does_not_affect_others() -> None:
    a, b = RngStreams(123), RngStreams(123)
    a["service"].random(10_000)  # consumo extra solo en 'service'
    np.testing.assert_array_equal(a["arrivals"].random(20), b["arrivals"].random(20))


def test_independent_of_request_order() -> None:
    a, b = RngStreams(5), RngStreams(5)
    a["arrivals"]
    x_a = a["reaction"].random(5)
    x_b = b["reaction"].random(5)  # pedido sin tocar antes 'arrivals'
    np.testing.assert_array_equal(x_a, x_b)


def test_generator_is_cached() -> None:
    r = RngStreams(0)
    assert r["speed"] is r["speed"]
    assert r.get("speed") is r["speed"]


def test_stream_index_is_stable() -> None:
    # Cambiar esta lista cambia todos los resultados: solo añadir al final.
    assert STREAM_NAMES[:6] == ("arrivals", "assignment", "group", "speed", "distance", "service")
    ss = RngStreams.seed_sequence(99, "service")
    assert ss.spawn_key == (5,)
    np.testing.assert_array_equal(
        RngStreams(99)["service"].random(3),
        np.random.default_rng(np.random.SeedSequence(99).spawn(6)[5]).random(3),
    )


def test_streams_look_uncorrelated() -> None:
    r = RngStreams(2026)
    x, y = r["service"].random(5000), r["speed"].random(5000)
    assert abs(np.corrcoef(x, y)[0, 1]) < 0.05


def test_unknown_stream_raises() -> None:
    with pytest.raises(KeyError):
        RngStreams(0)["no_existe"]


@pytest.mark.parametrize("seed", [-1, 1.5, "3", True])
def test_invalid_seed(seed) -> None:
    with pytest.raises(ValueError):
        RngStreams(seed)

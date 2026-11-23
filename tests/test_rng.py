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


# -- substream (generadores por recurso, D21) ---------------------------------


def test_substream_reproducible_and_order_free() -> None:
    a = RngStreams(5)
    first = a.substream("turnstile_failure", "A", 1, 2).random(4)
    a.substream("turnstile_failure", "B", 3, 1).random(10)  # otro torno antes
    again = a.substream("turnstile_failure", "A", 1, 2).random(4)
    other = RngStreams(5).substream("turnstile_failure", "A", 1, 2).random(4)
    np.testing.assert_array_equal(first, again)
    np.testing.assert_array_equal(first, other)


def test_substream_depends_on_seed_name_and_key() -> None:
    ref = RngStreams(5).substream("turnstile_failure", "A", 1, 2).random(4)
    for gen in (
        RngStreams(6).substream("turnstile_failure", "A", 1, 2),
        RngStreams(5).substream("gate_choice", "A", 1, 2),
        RngStreams(5).substream("turnstile_failure", "A", 1, 3),
        RngStreams(5).substream("turnstile_failure", "B", 1, 2),
        RngStreams(5).substream("turnstile_failure", "A", 2, 1),
    ):
        assert not np.array_equal(gen.random(4), ref)


def test_substream_does_not_touch_parent_stream() -> None:
    a, b = RngStreams(5), RngStreams(5)
    a.substream("turnstile_failure", "A", 1, 1).random(100)
    name = "turnstile_failure"
    np.testing.assert_array_equal(a[name].random(4), b[name].random(4))


def test_substream_key_encoding_is_unambiguous() -> None:
    r = RngStreams(5)
    pairs = [(("A", 1), ("A1",)), ((1, 2), (12,)), (("1",), (1,)), (("A",), ("\x00A",))]
    for k1, k2 in pairs:
        assert not np.array_equal(
            r.substream("turnstile_failure", *k1).random(4),
            r.substream("turnstile_failure", *k2).random(4),
        )


@pytest.mark.parametrize("bad", [-1, 1.5, True, None])
def test_substream_rejects_bad_keys(bad: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        RngStreams(5).substream("turnstile_failure", "A", bad)  # type: ignore[arg-type]


def test_substream_unknown_stream() -> None:
    with pytest.raises(KeyError):
        RngStreams(5).substream("nope", "A")

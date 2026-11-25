"""T6.2 (A) · Verificación y validación de la entrada y la capacidad.

1. Modelo fluido de ``sanmames.capacity`` (casos a mano).
2. Contraste con los datos definitivos de ``results/final`` (solo lectura; no se
   regeneran): ρ frente a la espera, cierre I4, componentes de la capacidad,
   repartos, conservación y números comunes.
3. Casos límite con simulación en una macrozona (N/4, misma carga por puerta que
   el estadio completo): cola que crece a ritmo ρ − 1 y cierre en t = −30 (D31).
   La réplica completa que reproduce ``kpis.csv`` solo con ``RUN_SLOW=1``.

Casos ya cubiertos en otros ficheros (no se duplican): muchos tornos → espera ≈ 0
(``test_capacity.py::test_many_turnstiles_no_queue``,
``test_verificacion_entrada.py::test_many_turnstiles_remove_entry_wait``), orden
2/3/4 tornos (``test_capacity.py::test_capacity_ordering_2_3_4_turnstiles``),
conservación por transición (``test_conservacion.py``) y reproducibilidad con
semillas comunes (``test_experiments_cli.py``).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from sanmames import capacity as cap
from sanmames.config import EXPERIMENTS_DIR, Config, deep_merge, load_config, load_experiment
from sanmames.metrics import KPI_COLUMNS, compute_kpis
from sanmames.runner import run_replica

FINAL = Path(__file__).resolve().parents[1] / "results" / "final"
SEED = 20261105
ONE_ZONE = {"zones": ["A"], "zone_share": [1.0], "n_spectators": 12194}


def scenario(name: str) -> Config:
    for path in sorted(EXPERIMENTS_DIR.glob("*.json")):
        for c in load_experiment(path).configs:
            if c.name == name:
                return c
    raise KeyError(name)


# =============================================================================
# 1 · Modelo fluido
# =============================================================================

GRID = np.arange(0.0, 60.0 + 1e-9, 0.01)


def test_fluid_no_queue_below_capacity() -> None:
    queue, wait = cap.fluid_waits(GRID, np.full(len(GRID), 9.0), np.full(len(GRID), 10.0))
    assert queue.max() == pytest.approx(0.0, abs=1e-9)
    assert wait.max() == pytest.approx(0.0, abs=0.011)


def test_fluid_wait_grows_at_rho_minus_one() -> None:
    lam = np.where(GRID < 30, 12.0, 0.0)
    _, wait = cap.fluid_waits(GRID, lam, np.full(len(GRID), 10.0))
    # Quien llega en t espera (λ/μ − 1)·t mientras dura la sobrecarga.
    for t in (10.0, 20.0, 29.0):
        assert wait[int(t / 0.01)] == pytest.approx(0.2 * t, abs=0.02)


def test_fluid_closed_server_waits_until_reopening() -> None:
    mu = np.where((GRID >= 10) & (GRID < 20), 0.0, 10.0)
    _, wait = cap.fluid_waits(GRID, np.full(len(GRID), 5.0), mu)
    assert wait[int(10 / 0.01)] == pytest.approx(10.0, abs=0.02)  # llega al cerrar
    # Al final del cierre: 50 en cola, se vacía a 10 − 5 = 5/min: 10 min más.
    assert wait[int(19.99 / 0.01)] == pytest.approx(5.0, abs=0.05)


def test_fluid_unfinished_queue_is_infinite() -> None:
    _, wait = cap.fluid_waits(GRID, np.full(len(GRID), 20.0), np.full(len(GRID), 10.0))
    assert np.isinf(wait[-100:]).all()


@pytest.mark.parametrize("name", ["X0_base", "X1_4tornos", "X2_anticipado"])
def test_fluid_entry_wait_zero_below_capacity(name: str) -> None:
    assert cap.traffic_intensity(scenario(name)) < 1
    assert cap.fluid_entry_wait(scenario(name))["wait_max_min"] == pytest.approx(0, abs=0.02)


def test_fluid_entry_wait_two_turnstiles() -> None:
    cfg = scenario("X1_2tornos")
    rho = cap.traffic_intensity(cfg)
    fluid = cap.fluid_entry_wait(cfg)
    # La punta ρ > 1 dura dos franjas de 15 min: la espera llega a (ρ − 1)·30.
    assert fluid["wait_max_min"] == pytest.approx((rho - 1) * 30, rel=0.01)
    assert 3.5 < fluid["wait_mean_min"] < 4.1


def test_fluid_closure_wait() -> None:
    cfg = scenario("X6_sin_redireccion")
    gc = cfg.incidents.gate_closure
    rho = cap.traffic_intensity(cfg)
    # Sin redirección: (duración − s) + ρ·s con s uniforme en el cierre.
    expected = gc.duration_min * (1 - (1 - rho) / 2)
    assert cap.fluid_closure_wait(cfg, redirect=False) == pytest.approx(expected, rel=0.01)
    # Con redirección: las 5 puertas restantes reciben 6/5 de su caudal.
    others = cfg.gates_per_zone - 1
    growth = rho * (others + 1) / others - 1
    assert cap.fluid_closure_wait(cfg, redirect=True) == pytest.approx(
        growth * gc.duration_min / 2, rel=0.02
    )


# =============================================================================
# 2 · Contraste con results/final (solo lectura)
# =============================================================================


@pytest.fixture(scope="module")
def final() -> dict[str, pd.DataFrame]:
    if not (FINAL / "kpis.csv").exists():
        pytest.skip("results/final no disponible")
    return {n: pd.read_csv(FINAL / f"{n}.csv") for n in ("kpis", "audit", "zones")}


def _mean(final: dict[str, pd.DataFrame], name: str, col: str, table: str = "kpis") -> float:
    t = final[table]
    return float(t.loc[t.scenario.eq(name), col].mean())


def test_final_wait_tracks_rho(final: dict[str, pd.DataFrame]) -> None:
    names = [
        "X1_4tornos",
        "S1_serv_-25",
        "X2_anticipado",
        "S1_N_-10",
        "X0_base",
        "S1_N_+10",
        "S1_serv_+25",
        "X1_2tornos",
    ]
    rho = [cap.traffic_intensity(scenario(n)) for n in names]
    wait = [_mean(final, n, "wait_mean_min") for n in names]
    assert rho == sorted(rho)
    assert wait == sorted(wait)  # la espera crece con ρ
    assert stats.spearmanr(rho, wait).statistic == pytest.approx(1.0)
    for n, r, w in zip(names, rho, wait, strict=True):
        if r < 0.85:
            assert w < 0.1, n  # ρ << 1: espera de segundos


@pytest.mark.parametrize("name", ["X1_2tornos", "S1_serv_+25"])
def test_final_saturated_wait_matches_fluid(final: dict[str, pd.DataFrame], name: str) -> None:
    cfg = scenario(name)
    assert cap.traffic_intensity(cfg) > 1.1
    fluid = cap.fluid_entry_wait(cfg)
    # El fluido ignora la variabilidad: queda algo por debajo, pero a menos de 10 %.
    assert _mean(final, name, "wait_mean_min") == pytest.approx(fluid["wait_mean_min"], rel=0.10)
    assert _mean(final, name, "wait_mean_min") > fluid["wait_mean_min"]


def test_final_two_turnstiles_p95_reaches_fluid_peak(final: dict[str, pd.DataFrame]) -> None:
    fluid = cap.fluid_entry_wait(scenario("X1_2tornos"))
    assert _mean(final, "X1_2tornos", "wait_p95_min") == pytest.approx(
        fluid["wait_max_min"], rel=0.05
    )


@pytest.mark.parametrize(
    "name, redirect, rel",
    [("X6_sin_redireccion", False, 0.03), ("X6_con_redireccion", True, 0.12)],
)
def test_final_closure_matches_fluid(
    final: dict[str, pd.DataFrame], name: str, redirect: bool, rel: float
) -> None:
    observed = _mean(final, name, "closure_wait_mean_min", "audit")
    assert observed == pytest.approx(
        cap.fluid_closure_wait(scenario(name), redirect=redirect),
        rel=rel,
    )


def test_final_capacity_components(final: dict[str, pd.DataFrame]) -> None:
    cfg = scenario("X0_base")
    k = final["kpis"][final["kpis"].scenario.eq("X0_base")]
    a = final["audit"][final["audit"].scenario.eq("X0_base")]
    # I2: proporción de relecturas = prob (E[S] = 4,3 s).
    rate = k.n_read_failures.sum() / k.n_spectators.sum()
    assert rate == pytest.approx(cfg.incidents.read_failure.prob, rel=0.01)
    # I3: averías por réplica = 72·T/(mtbf + reparación media) (disponibilidad 97,4 %).
    tf = cfg.incidents.turnstile_failure
    window = a.stop_time_min - cfg.t_open_min
    expected = cfg.n_turnstiles * window / (tf.mtbf_min + tf.repair_min.mean)
    assert k.n_turnstile_failures.mean() == pytest.approx(expected.mean(), rel=0.05)


def test_final_zone_shares(final: dict[str, pd.DataFrame]) -> None:
    z = final["zones"]
    counts = z.pivot_table(index=["scenario", "seed"], columns="zone", values="n_spectators")
    total = counts.to_numpy().sum(axis=0)
    assert stats.chisquare(total).pvalue > 0.001
    assert np.abs(total / total.sum() - 0.25).max() < 0.001


def test_final_conservation(final: dict[str, pd.DataFrame]) -> None:
    n = final["kpis"][["scenario", "seed", "n_spectators"]]
    a = final["audit"].merge(n, on=["scenario", "seed"])
    assert len(a) == len(final["audit"]) == 2965
    assert a.n_unfinished.eq(0).all()
    ordinary = a[~a.alarm_triggered.astype(bool)]
    for col in ("n_entered", "n_seated", "n_exited"):
        assert ordinary[col].eq(ordinary.n_spectators).all(), col
    alarm = a[a.alarm_triggered.astype(bool)]
    assert len(alarm) == 360
    assert (alarm.n_safe + alarm.n_abandoned).eq(alarm.n_spectators).all()


@pytest.mark.parametrize(
    "name",
    ["X4_escalonada", "X5_3acomodadores", "X7_salida_bloqueada", "S1_vel_-15", "S1_vel_+15"],
)
def test_final_common_random_numbers_same_entry(final: dict[str, pd.DataFrame], name: str) -> None:
    cols = ["wait_mean_min", "wait_p95_min", "queue_max_gate", "n_read_failures"]
    k = final["kpis"].set_index(["scenario", "seed"])
    x0, other = k.loc["X0_base"], k.loc[name]
    common = x0.index.intersection(other.index)
    assert len(common) >= 30
    pd.testing.assert_frame_equal(x0.loc[common, cols], other.loc[common, cols])


@pytest.mark.skipif(not os.environ.get("RUN_SLOW"), reason="lento: RUN_SLOW=1")
def test_final_replica_is_reproduced(final: dict[str, pd.DataFrame]) -> None:
    cfg = scenario("X1_2tornos")
    ref = final["kpis"].query("scenario == 'X1_2tornos' and replica == 0").iloc[0]
    got = compute_kpis(run_replica(cfg, int(ref.seed)), cfg)
    for col in KPI_COLUMNS:
        if pd.isna(ref[col]):
            assert pd.isna(got[col]), col
        else:
            assert float(got[col]) == pytest.approx(float(ref[col]), rel=1e-12, abs=1e-12), col


# =============================================================================
# 3 · Casos límite con simulación (una macrozona)
# =============================================================================


def zone_cfg(**overrides: Any) -> Config:
    return load_config(overrides=deep_merge(ONE_ZONE, overrides))


def peak_wait_slope(df: pd.DataFrame, start: float, end: float) -> float:
    """Pendiente (min de espera por min de reloj) de la espera según el instante de llegada."""
    d = df[(df.t_arrival >= start) & (df.t_arrival < end)]
    wait = d.t_start_control - d.t_arrival
    return float(np.polyfit(d.t_arrival, wait, 1)[0])


def test_queue_grows_at_rho_minus_one_with_two_turnstiles() -> None:
    """ρ ≈ 1,40: en la punta (−30 a 0) la espera crece sin cota a ritmo ρ − 1."""
    cfg = zone_cfg(turnstiles_per_gate=2)
    rho = cap.traffic_intensity(cfg)
    df = run_replica(cfg, SEED)
    slope = peak_wait_slope(df, -30, 0)
    assert slope == pytest.approx(rho - 1, rel=0.15)
    late_peak = df[(df.t_arrival >= -5) & (df.t_arrival < 0)]
    assert (late_peak.t_start_control - late_peak.t_arrival).mean() > 0.8 * (rho - 1) * 27.5


def test_queue_stays_flat_with_four_turnstiles() -> None:
    """ρ ≈ 0,70: en la misma punta la espera no tiene tendencia y es de segundos."""
    cfg = zone_cfg(turnstiles_per_gate=4)
    df = run_replica(cfg, SEED)
    assert abs(peak_wait_slope(df, -30, 0)) < 0.005
    peak = df[(df.t_arrival >= -30) & (df.t_arrival < 0)]
    assert (peak.t_start_control - peak.t_arrival).mean() < 0.1


@pytest.fixture(scope="module")
def closure_waits() -> dict[bool, float]:
    """Espera media de quien llega a A-1 durante el cierre de X6 (t = −30, D31)."""
    out = {}
    for redirect in (False, True):
        cfg = zone_cfg(
            redirect_on_gate_closure=redirect, incidents={"gate_closure": {"enabled": True}}
        )
        gc = cfg.incidents.gate_closure
        assert gc.start_min == -30
        df = run_replica(cfg, SEED)
        hit = df[
            df.gate.eq(gc.gate)
            & df.t_arrival.ge(gc.start_min)
            & df.t_arrival.lt(gc.start_min + gc.duration_min)
        ]
        assert len(hit) > 300
        if redirect:
            assert hit.gate_used.ne(gc.gate).all()
        out[redirect] = float((hit.t_start_control - hit.t_arrival).mean())
    return out


def test_closure_without_redirect_costs_almost_the_whole_closure(
    closure_waits: dict[bool, float],
) -> None:
    cfg = zone_cfg(redirect_on_gate_closure=False, incidents={"gate_closure": {"enabled": True}})
    assert closure_waits[False] == pytest.approx(
        cap.fluid_closure_wait(cfg, redirect=False),
        rel=0.1,
    )
    assert closure_waits[False] > 0.8 * cfg.incidents.gate_closure.duration_min


def test_closure_with_redirect_is_small(closure_waits: dict[bool, float]) -> None:
    assert closure_waits[True] < 1.5
    assert closure_waits[False] > 5 * closure_waits[True]

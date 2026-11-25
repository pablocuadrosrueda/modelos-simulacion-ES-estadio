"""T6.2, rol C: audita tablas finales y reproduce una réplica por escenario."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from report_campaign import build_report
from run_pilot import audit_replica, write_analysis

from sanmames.config import load_config
from sanmames.entities import SPECTATOR_COLUMNS
from sanmames.metrics import ID_COLUMNS, KPI_COLUMNS, compute_kpis
from sanmames.runner import run_replica

ROOT = Path(__file__).resolve().parents[1]
FILES = ("kpis", "audit", "zones", "groups", "summary", "comparisons", "precision")
KEYS = ["scenario", "seed"]


def model_digest(path: Path) -> str:
    """Huella del código con LF: Git en Windows puede convertir LF a CRLF."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def aligned(left, right, keys, label):
    """Rechaza pérdidas/duplicados antes de alinear, incluso si se compensan en tamaño."""
    require(
        not left.duplicated(keys).any() and not right.duplicated(keys).any(),
        f"{label}: identificadores duplicados",
    )
    left = left.set_index(keys).sort_index()
    right = right.set_index(keys).sort_index()
    require(left.index.equals(right.index), f"{label}: identidades distintas")
    return left, right


def same_numbers(left, right, label):
    require(
        np.allclose(
            np.asarray(left, dtype=float),
            np.asarray(right, dtype=float),
            rtol=1e-9,
            atol=1e-8,
            equal_nan=True,
        ),
        f"{label}: valores distintos",
    )


def verify(directory: Path, *, replay=False) -> dict:
    """Falla ante inconsistencias; no escribe ni modifica los resultados de T5.3."""
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    frames = {name: pd.read_csv(directory / f"{name}.csv") for name in FILES}
    kpis, audit = frames["kpis"], frames["audit"]
    require(list(kpis.columns) == ID_COLUMNS + KPI_COLUMNS, "Esquema de KPIs incompatible")
    build_report(directory)  # Terminación, semillas, tamaños y precisión D34.
    configs = {item["config"]["name"]: item["config"] for item in manifest["scenarios"]}
    require(set(kpis.scenario) == set(configs), "Escenarios distintos de las configs resueltas")
    checks = [f"Esquema, semillas y precisión: {len(kpis)} réplicas, {len(configs)} escenarios."]
    a, k = aligned(audit, kpis, KEYS, "Auditoría")
    require(not np.isinf(k[KPI_COLUMNS].to_numpy(dtype=float)).any(), "KPIs infinitos")
    for column in ("experiment", "replica"):
        require(a[column].equals(k[column]), f"Auditoría: {column} distinto")
    same_numbers(a.n_entered, k.n_entered, "Controles terminados")
    for column in (
        "n_spectators",
        "n_entered",
        "n_conflicts",
        "n_read_failures",
        "n_turnstile_failures",
        "queue_max_gate",
        "exit_queue_max",
        "n_abandoned",
    ):
        values = k[column].dropna()
        require(
            np.isfinite(values).all() and values.ge(0).all() and values.eq(np.floor(values)).all(),
            f"Recuento inválido: {column}",
        )
    for column in ("pct_wait_lt_10", "late_pct", "evac_pct_ref", "turnstile_util"):
        values = k[column].dropna()
        maximum = 1 if column == "turnstile_util" else 100
        require(values.between(-1e-9, maximum + 1e-9).all(), f"Rango inválido: {column}")
    for column in ("wait_mean_min", "wait_p95_min", "access_mean_min"):
        require(
            k[column].notna().all() and np.isfinite(k[column]).all() and k[column].ge(-1e-9).all(),
            f"Tiempo inválido: {column}",
        )
    require(k.access_mean_min.ge(k.wait_mean_min - 1e-9).all(), "Acceso menor que espera")
    for scenario, cfg in configs.items():
        part = a.loc[scenario]
        metrics = k.loc[scenario]
        n = cfg["n_spectators"]
        require(metrics.n_spectators.eq(n).all(), f"{scenario}: N distinto de config")
        counters = part[
            ["n_entered", "n_seated", "n_exited", "n_safe", "n_abandoned", "n_unfinished"]
        ]
        require(
            np.isfinite(counters).all().all()
            and counters.ge(0).all().all()
            and counters.le(n).all().all()
            and counters.eq(np.floor(counters)).all().all(),
            f"{scenario}: recuentos de auditoría inválidos",
        )
        require(part.n_seated.le(part.n_entered).all(), f"{scenario}: más sentados que entrados")
        require(metrics.queue_max_gate.le(n).all(), f"{scenario}: cola mayor que N")
        require(
            part.stop_time_min.between(
                cfg["t_open_min"], cfg["t_open_min"] + cfg["max_sim_hours"] * 60 + 1e-9
            ).all(),
            f"{scenario}: fin fuera del horizonte",
        )
        emergency = cfg["emergency"]["enabled"]
        require(part.alarm_triggered.eq(emergency).all(), f"{scenario}: alarma incompatible")
        if emergency:
            # En esta campaña todas las llegadas son anteriores a la alarma.
            profile = cfg["arrival_profiles"][cfg["arrival_profile"]]
            require(
                max(interval[1] for interval in profile) <= cfg["emergency"]["alarm_min"],
                f"{scenario}: faltaría contar las no llegadas en audit.csv",
            )
            require(
                (part.n_exited + part.n_safe + part.n_abandoned).eq(n).all(),
                f"{scenario}: conservación de poblaciones terminales",
            )
            require(
                (part.n_exited + part.n_safe).eq(part.n_entered).all(),
                f"{scenario}: evacuables distintos de entrados",
            )
            same_numbers(part.n_abandoned, metrics.n_abandoned, f"{scenario}: abandonos")
            require(
                metrics[["exit_time_min", "exit_queue_max"]].isna().all().all(),
                f"{scenario}: P5 no aplica tras alarma",
            )
            require(
                metrics[["evac_time_min", "evac_pct_ref"]].notna().all().all(),
                f"{scenario}: falta P8",
            )
            same_numbers(
                part.stop_time_min,
                metrics.evac_time_min + cfg["emergency"]["alarm_min"],
                f"{scenario}: reloj de evacuación",
            )
        else:
            require(
                part[["n_entered", "n_seated", "n_exited"]].eq(n).all().all()
                and part[["n_safe", "n_abandoned"]].eq(0).all().all(),
                f"{scenario}: conservación ordinaria",
            )
            require(
                metrics[["evac_time_min", "evac_pct_ref", "n_abandoned"]].isna().all().all(),
                f"{scenario}: P8 no aplica sin alarma",
            )
            require(
                metrics[["exit_time_min", "exit_queue_max"]].notna().all().all(),
                f"{scenario}: falta P5",
            )
            same_numbers(
                part.stop_time_min,
                metrics.exit_time_min + cfg["t_end_min"],
                f"{scenario}: reloj de salida",
            )
    checks += ["Recuentos, rangos, unidades, conservación terminal y reloj: correctos."]
    z = frames["zones"]
    require(not z.duplicated(KEYS + ["zone"]).any(), "Zonas duplicadas")
    totals = []
    for scenario, cfg in configs.items():
        part = z[z.scenario.eq(scenario)]
        require(set(part.zone) == set(cfg["zones"]), f"{scenario}: zonas distintas")
        require(
            part.groupby("seed").size().eq(len(cfg["zones"])).all(),
            f"{scenario}: zonas ausentes en una réplica",
        )
        require(
            part.n_spectators.ge(0).all()
            and part.n_spectators.eq(np.floor(part.n_spectators)).all(),
            f"{scenario}: reparto inválido",
        )
        same_numbers(
            part.share_pct,
            part.n_spectators * 100 / cfg["n_spectators"],
            f"{scenario}: porcentajes de zona",
        )
        totals.append(part.groupby(KEYS, as_index=False).n_spectators.sum())
    total, expected = aligned(pd.concat(totals), kpis, KEYS, "Reparto")
    same_numbers(total.n_spectators, expected.n_spectators, "Suma de zonas")
    require(set(z.scenario) == set(configs), "Escenarios extra en zonas")
    cohorts, _ = aligned(
        frames["groups"],
        kpis[kpis.scenario.isin(["X0_base", "X3_prioridad"])],
        KEYS,
        "Colectivos P4",
    )
    require(
        cohorts[["wait_mean_priority_min", "wait_mean_rest_min"]].notna().all().all(),
        "Colectivos incompletos",
    )
    same_numbers(
        cohorts.group_wait_diff_min,
        cohorts.wait_mean_priority_min - cohorts.wait_mean_rest_min,
        "Diferencia P4",
    )
    checks += [f"Reparto: {len(z)} filas; colectivos comparables P4: {len(cohorts)} réplicas."]
    with tempfile.TemporaryDirectory(prefix="sanmames-verificacion-") as temp:
        output = Path(temp)
        frames["groups"].to_csv(output / "groups.csv", index=False)
        write_analysis(kpis, output)
        for name, keys in [
            ("summary", ["scenario"]),
            ("comparisons", ["experiment", "scenario", "baseline"]),
        ]:
            actual, expected = aligned(
                frames[name], pd.read_csv(output / f"{name}.csv"), keys, name
            )
            require(list(actual.columns) == list(expected.columns), f"{name}: columnas distintas")
            same_numbers(actual, expected, name)
        actual, expected = aligned(
            frames["precision"], pd.read_csv(output / "precision.csv"), ["scenario"], "Precisión"
        )
        same_numbers(actual.n_valid, expected.n_pilot, "n de precisión")
        for col in (
            "wait_mean_min",
            "halfwidth_95_min",
            "relative_halfwidth_pct",
            "estimated_total_reps",
        ):
            same_numbers(actual[col], expected[col], f"Precisión: {col}")
    checks += ["Resúmenes, 15 contrastes emparejados y precisión recalculados desde las réplicas."]
    # Cambios posteriores a la entrada no deben alterar sus números comunes.
    for scenario in (
        "X4_escalonada",
        "X5_3acomodadores",
        "X5_6acomodadores",
        "X5_9acomodadores",
        "X7_todas_salidas",
        "X7_salida_bloqueada",
        "S1_vel_+15",
        "S1_vel_-15",
    ):
        pairs = pd.concat(
            [
                k.loc[scenario, "wait_mean_min"].rename("case"),
                k.loc["X0_base", "wait_mean_min"].rename("base"),
            ],
            axis=1,
        ).dropna()
        require(len(pairs) > 0, f"Sin semillas comunes: {scenario}")
        same_numbers(pairs["case"], pairs["base"], f"Números comunes entrada: {scenario}")
    for scenario in ("X5_3acomodadores", "X5_9acomodadores"):
        same_numbers(
            k.loc[scenario, "n_conflicts"],
            k.loc["X5_6acomodadores", "n_conflicts"],
            f"Números comunes I1: {scenario}",
        )
    checks += ["Números comunes: entrada invariante en X4/X5/X7/velocidad; mismos I1 en X5."]
    replays = []
    if replay:
        for name, digest in manifest["source_sha256"].items():
            if name.startswith("src/"):
                require(
                    model_digest(ROOT / name) == digest,
                    f"Modelo distinto del cálculo original: {name}",
                )
        for scenario, raw in configs.items():
            row = kpis[kpis.scenario.eq(scenario)].sort_values("replica").iloc[0]
            cfg = load_config(overrides=raw)
            df = run_replica(cfg, int(row.seed))
            require(
                list(df.columns) == SPECTATOR_COLUMNS
                and set(df.id) == set(range(cfg.n_spectators)),
                f"{scenario}: identidades del runner",
            )
            replay_audit, _ = audit_replica(df, cfg)
            times = ["t_arrival", "t_start_control", "t_end_control", "t_vomitory", "t_seated"]
            for before, after in zip(times[:-1], times[1:], strict=True):
                observed = df[[before, after]].dropna()
                require(
                    observed[before].le(observed[after] + 1e-9).all(),
                    f"{scenario}: orden temporal {before}/{after}",
                )
            indicators = compute_kpis(df, cfg)
            same_numbers(
                [indicators[c] for c in KPI_COLUMNS], row[KPI_COLUMNS], f"Reproducción {scenario}"
            )
            for column, value in replay_audit.items():
                same_numbers(
                    [value],
                    [a.loc[(scenario, row.seed), column]],
                    f"Reproducción auditoría {scenario}/{column}",
                )
            replays.append(dict(scenario=scenario, seed=int(row.seed), n=len(df)))
            print(
                f"Reproducido {scenario}: {len(df)} identidades, {len(KPI_COLUMNS)} KPIs coinciden",
                flush=True,
            )
    inputs = {
        f"{name}.csv": hashlib.sha256((directory / f"{name}.csv").read_bytes()).hexdigest()
        for name in FILES
    }
    inputs["manifest.json"] = hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest()
    return dict(
        checks=checks,
        replicas=len(kpis),
        scenarios=len(configs),
        replays=replays,
        inputs=inputs,
        source_git_commit=manifest["git_commit"],
        python=platform.python_version(),
        verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )


def render_report(result: dict) -> str:
    lines = [
        "# T6.2 · Verificación del rol C",
        "",
        "**Alcance:** integración del runner, KPIs y consistencia de los resultados definitivos. "
        "No cierra la revisión de capacidad y supuestos de A y B.",
        "",
        f"Campaña: {result['replicas']} réplicas, {result['scenarios']} escenarios. "
        f"Código del cálculo original: `{result['source_git_commit']}`.",
        "",
        f"Verificador SHA-256: `{result['verifier_sha256']}`. Python {result['python']}.",
        "",
        "## Comprobaciones",
        "",
    ]
    lines += [f"- {check}" for check in result["checks"]]
    lines += [
        "",
        "La conservación de las 2.965 réplicas se comprueba con los recuentos agregados "
        "y la auditoría realizada durante T5.3. Los CSV no contienen las trayectorias individuales "
        "de toda la campaña; no permiten volver a demostrar cada transición por sí solos.",
        "",
        "## Reproducción desde las configs y semillas originales",
        "",
    ]
    if result["replays"]:
        lines += [
            "Código de `src/` coincidente por SHA-256 con T5.3, normalizando CRLF a LF "
            "para permitir la conversión de finales de línea de Git en Windows. "
            "Una réplica por escenario, comprobada individualmente: IDs 0..N−1 sin duplicados, "
            "terminación mediante `audit_replica`, orden de entrada/asiento, todos los KPIs "
            "y metadatos de auditoría coincidentes. Tolerancia numérica: rtol=1e-9, atol=1e-8 "
            "en unidades de cada indicador; tiempos ordenados con tolerancia 1e-9 min.",
            "",
            "| Escenario | Semilla | Espectadores |",
            "|---|---:|---:|",
        ]
        lines += [f"| {r['scenario']} | {r['seed']} | {r['n']} |" for r in result["replays"]]
    else:
        lines += [
            "No ejecutada en esta invocación. Usar `--replay` para añadir evidencia del runner."
        ]
    lines += [
        "",
        "## Evidencia existente y límites",
        "",
        "- Conservación en cada transición, salida ordinaria y truncamiento: "
        "`tests/test_conservacion.py`, `tests/test_orden_temporal.py`.",
        "- Alarma, abandonos, no llegadas, conflictos interrumpidos y evacuación incompleta: "
        "`tests/test_emergency_integration.py`.",
        "- KPIs con cálculos manuales, NaN, denominadores y unidades: "
        "`tests/test_metrics*.py`; IC y emparejamiento: `tests/test_analysis.py`.",
        "- Capacidad y referencias analíticas ya documentadas por A/B: "
        "[VERIFICACION.md](VERIFICACION.md), `tests/test_capacity.py`, "
        "`tests/test_exit.py` y `tests/test_emergency.py`.",
        "",
        "Esto aporta verificación interna y reproducibilidad. La validez externa sigue limitada "
        "por la falta de datos completos de colas y salidas (ESPECIFICACION §6). Se comparan "
        "escenarios; repetir la misma semilla no aporta una réplica estadística nueva.",
        "",
        "## Pendiente de A y B para cerrar T6.2",
        "",
        "- A: revisar la evidencia existente de carga con dos tornos (ρ>1), ritmo por torno "
        "frente a F2 y capacidad de entrada; confirmar su vigencia para la memoria.",
        "- B: revisar capacidad de vomitorios/acomodadores/salidas y referencias de evacuación; "
        "confirmar supuestos y límites de sus módulos.",
        "- Equipo: cerrar la validación conjunta. No hace falta repetir comprobaciones ya "
        "aportadas si sus responsables confirman que siguen vigentes.",
        "- T6.3: redactar la memoria usando T6.1 y la revisión conjunta de T6.2.",
        "",
        "## Reproducción",
        "",
        "```bash",
        ".venv/bin/python scripts/verify_results.py --replay",
        "# Solo consistencia de las tablas (sin simular):",
        ".venv/bin/python scripts/verify_results.py --output /tmp/verificacion_C.md",
        "```",
        "",
        "El comando no modifica `results/final`; escribe el informe solo si todas las "
        "comprobaciones pasan. La suite de tests se ejecuta aparte con `make check`.",
        "",
        "## Huellas SHA-256 de las entradas",
        "",
        "| Archivo | SHA-256 |",
        "|---|---|",
    ]
    lines += [f"| {name} | `{digest}` |" for name, digest in result["inputs"].items()]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "results/final")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/VERIFICACION_C_T6.2.md")
    parser.add_argument("--replay", action="store_true", help="Repite una réplica por escenario")
    args = parser.parse_args(argv)
    try:
        report = render_report(verify(args.data, replay=args.replay))
    except (ValueError, KeyError, FileNotFoundError) as exc:
        parser.error(str(exc))
    args.output.write_text(report, encoding="utf-8")
    print(f"Verificación C correcta: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

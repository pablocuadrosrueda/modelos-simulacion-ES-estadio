"""Informe revisable de T5.3; exige campaña completa y precisión verificada."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from sanmames.analysis import confidence_interval

ROOT = Path(__file__).resolve().parents[1]


def _number(value) -> str:
    return "—" if pd.isna(value) else f"{value:.3f}"


def _interval(values) -> str:
    mean, halfwidth = confidence_interval(values)
    return f"{_number(mean)} ± {_number(halfwidth)}"


def _table(headers: list[str], rows: list[list]) -> list[str]:
    return [
        "| " + " | ".join(headers) + " |",
        "|" + "---|" * len(headers),
        *["| " + " | ".join(map(str, row)) + " |" for row in rows],
        "",
    ]


def build_report(data: Path) -> str:
    manifest = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
    if not manifest["completed"]:
        raise ValueError("La campaña aún no está completa; no se publica un informe definitivo")
    kpis = pd.read_csv(data / "kpis.csv")
    audit = pd.read_csv(data / "audit.csv")
    precision = pd.read_csv(data / "precision.csv")
    if kpis.duplicated(["scenario", "seed"]).any() or audit.n_unfinished.ne(0).any():
        raise ValueError("Falló la auditoría de réplicas")
    configs = {item["config"]["name"]: item["config"] for item in manifest["scenarios"]}
    counts = kpis.groupby("scenario").size().to_dict()
    if counts != manifest["final_counts"] or not precision.precision_met.eq(True).all():
        raise ValueError("El tamaño o la precisión final no están verificados")
    for _, group in kpis.groupby("scenario"):
        if sorted(group.replica) != list(range(len(group))):
            raise ValueError("Hay índices de réplica ausentes")
        if not group.seed.eq(manifest["base_seed"] + group.replica).all():
            raise ValueError("Las semillas no corresponden a sus índices")
        mean, halfwidth = confidence_interval(group.wait_mean_min)
        if len(group) < manifest["minimum_reps"] or halfwidth > 0.05 * abs(mean) + 1e-12:
            raise ValueError("El IC de espera no alcanza el objetivo")
    lines = [
        "# Resultados T5.3 · X0–X7 y sensibilidad S1",
        "",
        f"**Campaña completada:** {len(kpis):,} réplicas de {len(counts)} escenarios, "
        "conservando identidad y terminación completa de todos los espectadores.",
        "",
        "Los IC del 95 % se expresan como media ± semianchura, usando una observación "
        "por réplica (t-Student). Las diferencias se emparejan por semilla. Los tamaños "
        "por escenario pueden diferir: se usan todas las parejas comunes disponibles.",
        "",
        "## Diseño y procedencia",
        "",
        "- X5: conflictos al 1 %, resolución Triangular(1,3,10) min, un conflicto por "
        "acomodador; comparación de 3, 6 y 9 por zona (D33). Se conserva la saturación.",
        "- X6: puerta A-1 cerrada en t=−30 durante diez minutos, con/sin redirección "
        "(D31). El antiguo piloto en +20 es histórico y no se mezcla con este.",
        "- S1: seis variantes de aforo, velocidad y servicio ya definidas en sus configs.",
        f"- Código de simulación/campaña: `{manifest['git_commit']}`. Python "
        f"{manifest['python']}. Configs resueltas, versiones y hashes: "
        "[manifest.json](../results/final/manifest.json).",
        "- [Datos finales](../results/final) y [piloto actualizado](../results/final/pilot). "
        "Las semillas son `base_seed + replica`; las del piloto no se cuentan dos veces.",
        "",
        "## Precisión alcanzada",
        "",
        "Mínimo de treinta réplicas por escenario en la campaña oficial. Se estimó n con "
        "el piloto de diez y se amplió hasta verificar que la semianchura del IC de la "
        "espera media no excede el 5 % de esa media (D34). Esto fija la precisión de la "
        "espera, no un objetivo independiente para cada uno de los demás indicadores.",
        "",
    ]
    lines += _table(
        [
            "Escenario",
            "n válido",
            "Espera media (min)",
            "Semianchura IC (min)",
            "Semianchura relativa (%)",
        ],
        [
            [
                r.scenario,
                int(r.n_valid),
                _number(r.wait_mean_min),
                _number(r.halfwidth_95_min),
                _number(r.relative_halfwidth_pct),
            ]
            for r in precision.itertuples()
        ],
    )
    lines += ["## Acceso · escenarios principales", ""]
    rows = []
    for scenario, group in kpis.loc[~kpis.experiment.eq("S1")].groupby("scenario", sort=True):
        rows.append(
            [
                scenario,
                len(group),
                _interval(group.wait_mean_min),
                _interval(group.wait_p95_min),
                _interval(group.pct_wait_lt_10),
                _interval(group.late_pct),
            ]
        )
    lines += _table(
        ["Escenario", "n", "Espera (min)", "P95 (min)", "Espera <10 min (%)", "Entrada tardía (%)"],
        rows,
    )
    comparison = (
        pd.read_csv(data / "comparisons.csv")
        if (data / "comparisons.csv").exists()
        else pd.DataFrame()
    )
    if not comparison.empty:
        lines += [
            "## Contrastes emparejados",
            "",
            "Diferencia = alternativa − referencia; una cifra negativa reduce el indicador. "
            "X1–X4 y S1 usan X0; X5 usa seis acomodadores; X6 usa sin redirección y X7, "
            "todas las salidas. Para P4 se usan los mismos colectivos en X0/X3 (D32), "
            "sin alterar los KPIs originales de `kpis.csv`.",
            "",
        ]
        metrics = {
            "X1": ["wait_mean_min"],
            "X2": ["wait_mean_min"],
            "X3": ["wait_mean_priority_min", "wait_mean_rest_min"],
            "X4": ["exit_time_min", "exit_queue_max"],
            "X5": ["conflict_delay_s"],
            "X6": ["wait_mean_min"],
            "X7": ["evac_time_min", "evac_pct_ref"],
            "S1": ["wait_mean_min"],
        }
        rows = []
        for _, row in comparison.iterrows():
            for metric in metrics[row.experiment]:
                rows.append(
                    [
                        row.scenario,
                        row.baseline,
                        metric,
                        f"{_number(row[metric + '_mean'])} ± {_number(row[metric + '_halfwidth'])}",
                        int(row[metric + "_n"]),
                    ]
                )
        lines += _table(
            [
                "Alternativa",
                "Referencia",
                "Indicador (unidad en su nombre)",
                "Diferencia, IC 95 %",
                "Parejas",
            ],
            rows,
        )
    if audit.experiment.eq("X5").any():
        lines += [
            "## P6 · Acomodadores",
            "",
            "La duración I1 medida incluye espera por acomodador y resolución. La resolución "
            "por sí sola tiene media teórica 4,667 min; el rango de 1 a 10 min no limita la "
            "duración total cuando hay cola. Nueve puede reducir mucho la espera sin eliminarla. "
            "El indicador `conflict_delay_s` mide el contraste en otros espectadores de D25; "
            "no debe confundirse con la duración del conflicto de su causante.",
            "",
        ]
        rows = [
            [
                name,
                len(g),
                _interval(g.conflict_duration_mean_min),
                _number(g.conflict_duration_p95_min.mean()),
                _number(g.conflict_duration_max_min.max()),
                _number(g.last_seated_min.max()),
            ]
            for name, g in audit.loc[audit.experiment.eq("X5")].groupby("scenario")
        ]
        lines += _table(
            [
                "Escenario",
                "n",
                "Duración media I1 (min), IC 95 %",
                "P95 I1 (min, media)",
                "Mayor I1 observado (min)",
                "Último asiento observado (t, min)",
            ],
            rows,
        )
    if audit.experiment.eq("X6").any():
        lines += [
            "## P7 · Cierre en hora punta",
            "",
            "Colectivo afectado: asignados a A-1 que llegan durante [−30,−20). "
            "Su espera no es la media global de todo el estadio. No se cambia la hipótesis "
            "D23 sobre quienes ya estaban en cola al cerrarse la puerta.",
            "",
        ]
        rows = [
            [
                name,
                len(g),
                _number(g.closure_arrivals.mean()),
                _number(g.closure_redirected.mean()),
                _interval(g.closure_wait_mean_min),
            ]
            for name, g in audit.loc[audit.experiment.eq("X6")].groupby("scenario")
        ]
        lines += _table(
            [
                "Escenario",
                "n",
                "Llegadas afectadas (media)",
                "Redirigidos (media)",
                "Espera de afectados (min), IC 95 %",
            ],
            rows,
        )
    if kpis.experiment.eq("X7").any():
        lines += [
            "## P8 · Evacuación",
            "",
            "Una media de vaciado menor que ocho minutos no implica que todos los partidos "
            "cumplan. Se informa también cuántas réplicas vacían por completo antes de ocho "
            "minutos y el porcentaje de personas a salvo a ese instante.",
            "",
        ]
        rows = [
            [
                name,
                len(g),
                _interval(g.evac_time_min),
                _interval(g.evac_pct_ref),
                f"{int(g.evac_time_min.le(configs[name]['emergency']['reference_min']).sum())}/{len(g)}",
                _number(g.evac_time_min.max()),
            ]
            for name, g in kpis.loc[kpis.experiment.eq("X7")].groupby("scenario")
        ]
        lines += _table(
            [
                "Escenario",
                "n",
                "Vaciado (min), IC 95 %",
                "Seguros a 8 min (%), IC 95 %",
                "Vaciado total ≤8 min",
                "Máximo vaciado (min)",
            ],
            rows,
        )
    if kpis.experiment.eq("S1").any():
        lines += [
            "## S1 · Sensibilidad",
            "",
            "Cada variante cambia un parámetro respecto a X0. S1 hereda salida ordinaria "
            "sin alarma: estos resultados no constituyen una sensibilidad de evacuación.",
            "",
        ]
        rows = [
            [
                name,
                len(g),
                _interval(g.wait_mean_min),
                _interval(g.access_mean_min),
                _interval(g.late_pct),
                _interval(g.exit_time_min),
            ]
            for name, g in kpis.loc[kpis.experiment.eq("S1")].groupby("scenario")
        ]
        lines += _table(
            ["Escenario", "n", "Espera (min)", "Acceso (min)", "Tardíos (%)", "Salida (min)"], rows
        )
    lines += [
        "## Alcance y siguiente paso",
        "",
        "Los resultados comparan escenarios del modelo de la Parte 1, ampliado según D31/D33. "
        "I3 cuenta todas las averías registradas, incluso después de la entrada (D25); no "
        "equivale al número de averías que afectaron a personas. La capacidad analítica y "
        "el rendimiento están en [VERIFICACION.md](VERIFICACION.md).",
        "",
        "Sigue T6.1 (gráficas P1–P8), T6.2 (verificación/validación conjunta) y T6.3 "
        "(memoria de resultados, justificando X6 en −30 y la variante de nueve en X5).",
        "",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "results/final")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/RESULTADOS_T5.3.md")
    args = parser.parse_args(argv)
    try:
        report = build_report(args.data)
    except ValueError as exc:
        parser.error(str(exc))
    args.output.write_text(report, encoding="utf-8")
    print(f"Informe guardado en {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

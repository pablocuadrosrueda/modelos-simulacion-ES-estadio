"""T6.1: figuras P1–P8 y S1 desde la campaña definitiva, sin simular."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator
from report_campaign import build_report

from sanmames.analysis import confidence_interval

ROOT = Path(__file__).resolve().parents[1]
BASE = "X0_base"
SOURCES = (
    "manifest.json",
    "kpis.csv",
    "audit.csv",
    "groups.csv",
    "precision.csv",
    "comparisons.csv",
)
COLORS = ("#236192", "#b85b16", "#34805b", "#8a538d", "#746020", "#666666")


def load_data(directory: Path) -> dict:
    """Reutiliza la auditoría T5.3 y exige las mismas identidades en tablas auxiliares."""
    build_report(directory)
    data = {name: pd.read_csv(directory / f"{name}.csv") for name in ("kpis", "audit", "groups")}
    data["manifest"] = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    keys = ["scenario", "seed"]
    for name in ("audit", "groups"):
        frame = data[name]
        expected = data["kpis"]
        if name == "groups":
            expected = expected[expected.scenario.isin([BASE, "X3_prioridad"])]
        if frame.duplicated(keys).any() or set(map(tuple, frame[keys].values)) != set(
            map(tuple, expected[keys].values)
        ):
            raise ValueError(f"Identidades incompatibles en {name}")
    return data


def sample(data: dict, source: str, scenario: str, metric: str, *, paired=False):
    """Una observación por réplica; diferencias con X0 por semilla, nunca por posición."""
    frame = data[source]
    values = frame.loc[frame.scenario.eq(scenario)].set_index("seed")[metric]
    if paired:
        baseline = frame.loc[frame.scenario.eq(BASE)].set_index("seed")[metric]
        pairs = pd.concat([values.rename("case"), baseline.rename("base")], axis=1).dropna()
        values = pairs["case"] - pairs["base"]
    return values.dropna().to_numpy(dtype=float)


def panel(source, metric, title, unit, cases, *, scale=1, paired=False, reference=None):
    return dict(
        source=source,
        metric=metric,
        title=title,
        unit=unit,
        cases=cases,
        scale=scale,
        paired=paired,
        reference=reference,
    )


def figure_specs(data: dict) -> list[tuple]:
    """Preguntas y unidades explícitas; referencias físicas de las configs resueltas."""
    base = [(BASE, "Actual")]
    turnstiles = [("X1_2tornos", "2 tornos"), (BASE, "3 tornos"), ("X1_4tornos", "4 tornos")]
    early = base + [("X2_anticipado", "Anticipada")]
    priority = [(BASE, "FIFO"), ("X3_prioridad", "Prioridad")]
    exits = base + [("X4_escalonada", "Escalonada")]
    stewards = [(f"X5_{n}acomodadores", f"{n} por zona") for n in (3, 6, 9)]
    closure = [("X6_sin_redireccion", "Sin redirección"), ("X6_con_redireccion", "Con redirección")]
    evacuation = [
        ("X7_todas_salidas", "Todas las salidas"),
        ("X7_salida_bloqueada", "Una bloqueada"),
    ]
    configs = {c["config"]["name"]: c["config"] for c in data["manifest"]["scenarios"]}
    reference = configs[evacuation[0][0]]["emergency"]["reference_min"]
    if any(configs[s]["emergency"]["reference_min"] != reference for s, _ in evacuation):
        raise ValueError("Las variantes de evacuación tienen referencias distintas")
    closure_config = configs[closure[0][0]]["incidents"]["gate_closure"]
    for s, _ in closure:
        if configs[s]["incidents"]["gate_closure"] != closure_config:
            raise ValueError("Las variantes de cierre deben compartir puerta y periodo")
    p = panel
    return [
        (
            "P1",
            "Operativa actual: acceso",
            [
                p("kpis", "wait_mean_min", "Espera media", "min", base),
                p("kpis", "queue_max_gate", "Máximo en una puerta", "personas esperando", base),
                p("kpis", "turnstile_util", "Utilización nominal de tornos", "%", base, scale=100),
                p("kpis", "late_pct", "Llegada antes de t=0, asiento después", "%", base),
            ],
            "Cola: máximo de una puerta por réplica. Utilización: desde apertura; "
            "no es carga punta.",
        ),
        (
            "P2",
            "Capacidad de acceso: tornos por puerta",
            [
                p("kpis", "wait_mean_min", "Espera media", "min", turnstiles),
                p("kpis", "wait_p95_min", "Percentil 95 de espera por réplica", "min", turnstiles),
                p(
                    "kpis",
                    "pct_wait_lt_10",
                    "Público que espera <10 min",
                    "%",
                    turnstiles,
                    reference=(95, "Objetivo 95 %"),
                ),
            ],
            "El IC del percentil describe su media entre partidos; el objetivo se "
            "evalúa sobre el % <10 min.",
        ),
        (
            "P3",
            "Adelantar las llegadas",
            [
                p("kpis", "wait_mean_min", "Espera media", "min", early),
                p("kpis", "late_pct", "Entrada tardía atribuible a colas", "%", early),
            ],
            "Entrada tardía: solo quienes llegan antes de t=0 y se sientan después.",
        ),
        (
            "P4",
            "Prioridad: beneficio y coste por colectivo",
            [
                p("groups", "wait_mean_priority_min", "Mayores y PMR: espera", "min", priority),
                p("groups", "wait_mean_rest_min", "Resto del público: espera", "min", priority),
                p(
                    "groups",
                    "wait_mean_rest_min",
                    "Cambio en el resto: prioridad − FIFO",
                    "min",
                    [("X3_prioridad", "Mismas semillas")],
                    paired=True,
                    reference=(0, "Sin cambio"),
                ),
            ],
            "Mismos colectivos en ambos escenarios (D32). Cambio emparejado por "
            "semilla; n = parejas comunes.",
        ),
        (
            "P5",
            "Salida escalonada: cola y tiempo total",
            [
                p("kpis", "exit_queue_max", "Máximo en una salida", "personas", exits),
                p("kpis", "exit_time_min", "Última salida − final del partido", "min", exits),
            ],
            "El máximo de salida incluye a quien cruza; no es la suma de las colas "
            "del estadio (D24).",
        ),
        (
            "P6",
            "Conflictos al 1 %: 3, 6 y 9 acomodadores",
            [
                p(
                    "audit",
                    "conflict_duration_mean_min",
                    "Duración I1: cola + resolución",
                    "min",
                    stewards,
                ),
                p("kpis", "conflict_delay_s", "Retraso al resto del bloque", "s/persona", stewards),
                p("kpis", "late_pct", "Entrada tardía por colas", "%", stewards),
            ],
            "Duración I1 y retraso del resto son indicadores distintos. Nueve "
            "mejora la cola; no demuestra un mínimo óptimo.",
        ),
        (
            "P7",
            f"Cierre en t={closure_config['start_min']:g} min: efecto de la redirección",
            [
                p(
                    "audit",
                    "closure_wait_mean_min",
                    "Espera del colectivo afectado",
                    "min",
                    closure,
                ),
                p("kpis", "wait_mean_min", "Espera media de todo el público", "min", closure),
                p("kpis", "queue_max_gate", "Máximo en una puerta", "personas esperando", closure),
            ],
            "Afectados: asignados a la puerta cerrada que llegan durante el "
            "cierre; no todo el estadio.",
        ),
        (
            "P8",
            "Evacuación: referencia temporal y cumplimiento",
            [
                p(
                    "kpis",
                    "evac_time_min",
                    "Tiempo hasta el último en zona segura",
                    "min",
                    evacuation,
                    reference=(reference, f"Referencia {reference:g} min"),
                ),
                p(
                    "kpis",
                    "evac_pct_ref",
                    f"Público seguro a los {reference:g} min",
                    "%",
                    evacuation,
                ),
                p(
                    "kpis",
                    "evac_time_min",
                    f"Partidos vaciados en ≤{reference:g} min",
                    "% de réplicas",
                    evacuation,
                    reference=(reference, "frequency"),
                ),
            ],
            "Último panel: frecuencia observada y conteo, sin IC. Media <8 min no "
            "implica cumplir en todos los partidos.",
        ),
        (
            "S1",
            "Sensibilidad: diferencias respecto a X0",
            [
                p(
                    "kpis",
                    metric,
                    title,
                    "min",
                    [(s, s.removeprefix("S1_")) for s in sorted(configs) if s.startswith("S1_")],
                    paired=True,
                    reference=(0, "Sin cambio"),
                )
                for metric, title in [
                    ("wait_mean_min", "Cambio de espera media"),
                    ("access_mean_min", "Cambio de tiempo de acceso"),
                    ("exit_time_min", "Cambio de tiempo de salida"),
                ]
            ],
            "Diferencias variante − X0 emparejadas por semilla. Sin alarma: no se "
            "infiere sensibilidad de evacuación.",
        ),
    ]


def draw_figure(data: dict, spec: tuple):
    """Devuelve figura y valores trazables; barras de error = IC t-Student del 95 %."""
    name, title, panels, note = spec
    rows, columns = (2, 2) if len(panels) == 4 else (1, len(panels))
    fig, axes = plt.subplots(
        rows, columns, figsize=(5.1 * columns, 4.8 if rows == 1 else 7.5), squeeze=False
    )
    records = []
    for ax, definition in zip(axes.flat, panels, strict=True):
        labels = []
        for y, (scenario, label) in enumerate(definition["cases"]):
            values = (
                sample(
                    data,
                    definition["source"],
                    scenario,
                    definition["metric"],
                    paired=definition["paired"],
                )
                * definition["scale"]
            )
            if len(values) < 2 or not np.isfinite(values).all():
                raise ValueError(
                    f"Muestra insuficiente o inválida: {name}/{scenario}/{definition['metric']}"
                )
            frequency = (
                definition["reference"] is not None and definition["reference"][1] == "frequency"
            )
            successes = (
                int(np.count_nonzero(values <= definition["reference"][0])) if frequency else None
            )
            mean, halfwidth = (
                (100 * successes / len(values), None) if frequency else confidence_interval(values)
            )
            labels.append(f"{label}\n(n={len(values)})")
            ax.errorbar(
                mean,
                y,
                xerr=halfwidth,
                fmt="o",
                capsize=4,
                color=COLORS[y % len(COLORS)],
                markersize=7,
            )
            digits = 5 if definition["metric"] == "evac_pct_ref" else 3
            text = (
                f"{successes}/{len(values)}"
                if frequency
                else f"{mean:.{digits}f} ± {halfwidth:.{digits}f}"
            )
            ax.annotate(
                text, (mean, y), xytext=(0, 12), textcoords="offset points", fontsize=9, ha="center"
            )
            records.append(
                dict(
                    figure=name,
                    panel=definition["title"],
                    source=definition["source"],
                    metric=definition["metric"],
                    scenario=scenario,
                    paired=definition["paired"],
                    unit=definition["unit"],
                    n=len(values),
                    mean=mean,
                    halfwidth=halfwidth,
                    successes=successes,
                )
            )
        ax.set_yticks(range(len(labels)), labels)
        ax.set_ylim(len(labels) - 0.5, -0.85)
        ax.margins(x=0.35)
        if definition["reference"] and not frequency:
            value, label = definition["reference"]
            ax.axvline(value, color="#666666", linestyle="--", linewidth=1, label=label)
            ax.legend(loc="lower right", fontsize=8)
        if frequency:
            ax.set_xlim(-10, 110)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.set_xlabel(definition["unit"])
        ax.set_title(definition["title"], fontsize=11, pad=22)
        ax.grid(axis="x", alpha=0.22)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"{name} · {title}", fontsize=15, y=0.98)
    fig.text(
        0.5,
        0.07,
        "Puntos: medias de réplicas; barras: IC 95 % de la media. n: réplicas por punto.",
        ha="center",
        fontsize=10,
    )
    fig.text(0.5, 0.02, note, ha="center", fontsize=9)
    fig.tight_layout(rect=(0.01, 0.13, 0.99, 0.89), w_pad=3)
    return fig, records


def generate(data_dir: Path, output: Path) -> list[Path]:
    """Exporta PNG 300 dpi, SVG, estadísticos y hashes de los datos que se han dibujado."""
    data = load_data(data_dir)
    specs = figure_specs(data)
    output.mkdir(parents=True, exist_ok=True)
    paths, records = [], []
    with plt.rc_context({"font.family": "DejaVu Sans", "svg.hashsalt": "sanmames-T6.1"}):
        for spec in specs:
            fig, rows = draw_figure(data, spec)
            try:
                for extension in ("png", "svg"):
                    path = output / f"{spec[0]}.{extension}"
                    metadata = {"Date": None} if extension == "svg" else {}
                    fig.savefig(path, dpi=300, metadata=metadata)
                    paths.append(path)
            finally:
                plt.close(fig)
            records.extend(rows)
    pd.DataFrame(records).to_csv(output / "statistics.csv", index=False)
    manifest = dict(
        source_git_commit=data["manifest"]["git_commit"],
        confidence_level=0.95,
        inputs={
            name: hashlib.sha256((data_dir / name).read_bytes()).hexdigest() for name in SOURCES
        },
        plot_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        matplotlib_version=matplotlib.__version__,
        outputs={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths + [output / "statistics.csv"]
        },
    )
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return paths


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "results/final")
    parser.add_argument("--output", type=Path, default=ROOT / "results/figures")
    args = parser.parse_args(argv)
    try:
        paths = generate(args.data, args.output)
    except (ValueError, KeyError, FileNotFoundError) as exc:
        parser.error(str(exc))
    print(f"Generados {len(paths)} archivos gráficos en {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

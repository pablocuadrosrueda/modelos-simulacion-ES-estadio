# Simulación del acceso, salida e incidencias en San Mamés

Proyecto de **Diseño de Modelos de Simulación** (Escuela Politécnica Superior de
Jaén, UJA, curso 2026/2027). Es un modelo de **simulación de eventos discretos**
en Python 3 + [SimPy](https://simpy.readthedocs.io/) de la entrada, permanencia,
salida e incidencias del público en un partido de máxima afluencia en el estadio
de San Mamés (Bilbao): 48.775 espectadores, 24 puertas y 72 tornos.

Con el modelo se compararán políticas de gestión (número de tornos, llegada
anticipada, prioridad para mayores y PMR, salida escalonada) y el impacto de
incidencias (conflictos por asiento, fallos de lectura, averías de torno, cierre
de puerta y evacuación de emergencia). La especificación completa está en
[`docs/Memoria_San_Mames-2.pdf`](docs/Memoria_San_Mames-2.pdf) (Parte 1) y su
resumen en [`docs/ESPECIFICACION.md`](docs/ESPECIFICACION.md).

## Integrantes

* Pablo Cuadros Rueda
* Pablo Pérez Molina
* José María Chamorro Bueno

## Estado actual

**Inc0 (esqueleto) completado.** Hay tooling, configuraciones de todos los
experimentos, carga y validación de configuración, generadores aleatorios por
fuente, contratos entre módulos y tests de esas piezas.
**La simulación todavía no está implementada.** Las funciones del modelo lanzan
`NotImplementedError`. Siguiente paso: Inc1 (rebanada vertical de la entrada).
El detalle está en [`docs/ESTADO.md`](docs/ESTADO.md).

## Estructura

```
.
├── AGENTS.md              # instrucciones para agentes y equipo (leer primero)
├── CLAUDE.md              # importa AGENTS.md
├── Makefile               # install / test / lint / format / run
├── pyproject.toml
├── configs/
│   ├── base.json          # escenario base X0 con todos los parámetros
│   └── experiments/       # X0–X7 y S1 como diff sobre base.json
├── docs/
│   ├── Memoria_San_Mames-2.pdf
│   ├── ESPECIFICACION.md  # destilado de la memoria
│   ├── CONTRATOS.md       # columnas, KPIs, firmas y convenciones
│   ├── TAREAS.md          # tablero por incrementos
│   ├── ESTADO.md          # dónde estamos y dudas abiertas
│   └── DECISIONES.md      # registro de decisiones
├── results/               # salidas (no versionadas)
├── scripts/
│   └── run_experiment.py  # CLI: experimento y número de réplicas
├── src/sanmames/          # paquete: config, rng, entities, arrivals, entry,
│                          # stadium, exit, emergency, incidents, metrics,
│                          # runner, analysis, experiments
└── tests/
```

## Instalación

Requiere Python ≥ 3.10.

```bash
make install    # crea el entorno virtual e instala el paquete (editable) + pytest y ruff
make test
make lint
```

El entorno se crea en `.venv/`. Si la ruta del repositorio contiene `:`,
`python -m venv` no puede crearlo ahí y se usa
`~/.venvs/modelos-simulacion-ES-estadio`. `make venv-path` muestra la ruta, y
`make install VENV=/otra/ruta` permite elegir otra.

## Uso

```bash
make run EXP=X0 REPS=10                              # equivale a:
python scripts/run_experiment.py X0 --reps 10         # (con el python del venv)
python scripts/run_experiment.py --list               # experimentos disponibles
```

El nombre del experimento puede ser el nombre completo del fichero
(`X1_2tornos`) o un prefijo que identifique un solo fichero (`X0`). Cuando la
simulación esté implementada, la tabla de KPIs por réplica se guardará en
`results/<experimento>_kpis.csv`. Hoy el comando informa de que aún no está
implementado.

Desde Python, la carga de configuración ya funciona:

```python
from sanmames.config import load_config, load_experiment
cfg = load_config(overrides={"turnstiles_per_gate": 4})
exp = load_experiment("configs/experiments/S1_sensibilidad.json")  # 6 variantes
```

## Trabajo en equipo con agentes

Somos tres personas y trabajamos en paralelo con dos sesiones de Claude Code y
una de Codex. Para no pisarnos:

* **Al empezar** cada sesión se leen [`AGENTS.md`](AGENTS.md),
  [`docs/ESTADO.md`](docs/ESTADO.md) y la tarea asignada en
  [`docs/TAREAS.md`](docs/TAREAS.md).
* **Un módulo, un responsable** (roles A, B y C; ver `AGENTS.md`).
* Las **interfaces compartidas** están en [`docs/CONTRATOS.md`](docs/CONTRATOS.md).
  Cambiarlas exige anotarlo en [`docs/DECISIONES.md`](docs/DECISIONES.md).
* Ramas `feat/<persona>-<tarea>`, commits pequeños, `make test` y `make lint`
  limpios antes de abrir un PR, y nunca push directo a `main`.
* Cada PR actualiza `docs/ESTADO.md` y `docs/TAREAS.md`.

## Documentación

Toda en [`docs/`](docs/): especificación, contratos, tareas, estado y decisiones.

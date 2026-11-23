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
**Inc1:** la rama T1.6 permite ejecutar la cadena llegada → entrada → asiento,
repetirla con semillas registradas y guardar KPIs en CSV. Runner (PR #6), métricas y ubicación ya fusionadas en `main`. Permanencia, salida,
incidencias y emergencia se implementan en los incrementos siguientes.
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
make hooks    # opcional: lint + tests automáticos antes de cada push
```

El entorno se crea en `.venv/`. Si la ruta del repositorio contiene `:`,
`python -m venv` no puede crearlo ahí y se usa
`~/.venvs/modelos-simulacion-ES-estadio`. `make venv-path` muestra la ruta, y
`make install VENV=/otra/ruta` permite elegir otra.

## Uso

```bash
make run EXP=configs/dev/i1_mini.json REPS=3
.venv/bin/python scripts/run_experiment.py configs/dev/i1_mini.json --reps 3 --seed 20261105
.venv/bin/python scripts/run_experiment.py --list
```

El nombre del experimento puede ser el nombre completo del fichero
(`X1_2tornos`), un prefijo que identifique un solo fichero (`X0`), o la ruta a
un JSON de experimento, también fuera de `configs/experiments`. La tabla se
guarda en `results/<nombre_del_fichero>_kpis.csv`, con una fila por escenario
y réplica y semilla `base_seed + replica`, común entre escenarios.

Para Inc1 utiliza `configs/dev/i1_mini.json`: las configuraciones X0–X7 y S1
requieren fases todavía pendientes. El runner rechaza incidencias/emergencia
activadas en lugar de ignorarlas. La API `run_experiment` devuelve la tabla;
la CLI es quien escribe el CSV.

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

Para comprobar la cadena completa con emergencia, desde el clon:

```bash
make check
make run EXP=configs/dev/i4_mini.json REPS=3
```

El CSV `results/i4_mini_kpis.csv` compara salidas abiertas y una bloqueada con
600 personas y semillas comunes, incluyendo I1–I4. Es una verificación pequeña;
los experimentos oficiales X0–X7 se ejecutan en T5.1. La réplica termina al salir
o evacuar todos, o al alcanzar el límite desde apertura. Los indicadores de
vaciado incompleto permanecen en NaN; ver `docs/CONTRATOS.md`.

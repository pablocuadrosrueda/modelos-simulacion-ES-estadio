# AGENTS.md — guía para agentes (Claude Code, Codex) y personas

## Al iniciar sesión (obligatorio)

1. Lee este fichero entero.
2. Lee [`docs/ESTADO.md`](docs/ESTADO.md) (dónde estamos) y
   [`docs/AVISOS.md`](docs/AVISOS.md) (cambios de otros roles que te afectan).
3. Lee tu tarea en [`docs/TAREAS.md`](docs/TAREAS.md) (ID, responsable, dependencias).
4. Si tocas una interfaz compartida, lee [`docs/CONTRATOS.md`](docs/CONTRATOS.md).
   Para dudas del modelo, [`docs/ESPECIFICACION.md`](docs/ESPECIFICACION.md)
   (destilado de `docs/Memoria_San_Mames-2.pdf`, que manda en caso de conflicto).

## Objetivo

Simulación de eventos discretos (Python 3 + SimPy) de la entrada, permanencia,
salida e incidencias del público en San Mamés (proyecto de Diseño de Modelos de
Simulación, UJA 2026/27). Cada réplica es un partido completo, de la apertura de
puertas (t = −90 min) a la salida del último espectador. Se comparan escenarios
X0–X7 y la sensibilidad S1 con números aleatorios comunes.

## Arquitectura

```
configs/base.json + configs/experiments/X*.json (diff)
        │  config.load_experiment
        ▼
     Config ──► runner.run_replica(config, seed)
                  │  E0: SimContext(env, rngs=RngStreams(seed), recursos)
                  │  arrivals.generate_spectators
                  │  por espectador: entry ─► stadium ─► (partido) ─► exit
                  │                                     └─► emergency (si alarma)
                  │  auxiliares: incidents (I1, I4), entry (I2, I3)
                  ▼
     DataFrame (1 fila/espectador, SPECTATOR_COLUMNS)
        │  metrics.compute_kpis
        ▼
     dict KPIs ──► experiments.run_experiment (n réplicas) ──► results/*.csv
                                                     │
                                                     ▼ analysis (IC, n, gráficas)
```

| Módulo (`src/sanmames/`) | Contenido | Responsable |
|---|---|---|
| `config.py` | Dataclasses y carga/validación de configs | A |
| `rng.py` | `RngStreams`: un generador por fuente de azar | A |
| `entities.py` | `Spectator`, `Incident`, columnas, reloj | A |
| `arrivals.py` | Generación de espectadores y llegadas (E0) | A |
| `entry.py` | Colas de puerta, tornos, I2, I3 (E1–E3) | A |
| `stadium.py` | Vomitorios, acomodadores, sentarse (E4) | B |
| `exit.py` | Salida ordinaria (E5, E6) | B |
| `emergency.py` | Evacuación (E7, E8) | B |
| `incidents.py` | I1 conflicto por asiento, I4 cierre de puerta | B |
| `metrics.py` | KPIs por réplica | C |
| `runner.py` | `SimContext`, `run_replica` (E0, E9) | C |
| `analysis.py` | IC, réplicas necesarias, comparación, gráficas | C |
| `experiments.py` | Réplicas por escenario, semillas comunes | C |
| `tests/` | Verificación | C (cada uno añade los de su módulo) |

A, B y C son los tres roles del equipo. Qué integrante (y qué sesión de agente)
lleva cada rol se anota en `docs/ESTADO.md` (sección «Reparto»).

## Reglas

1. **Un módulo = un responsable.** No edites módulos ajenos salvo bugs triviales
   (typo, import); en ese caso, menciónalo en el PR.
2. **Contratos estables.** No cambies firmas, columnas, unidades ni flujos de
   `rng.STREAM_NAMES` sin anotarlo en `docs/DECISIONES.md` y actualizar
   `docs/CONTRATOS.md` en el mismo PR.
3. **Tests antes de PR.** `make test` y `make lint` limpios. Cada función
   implementada lleva su test. Al implementar algo que hace pasar un test `xfail`,
   quita el marcador.
4. **Ramas** `feat/<persona>-<tarea>` (p. ej. `feat/a-T1.1-llegadas`), desde `main`
   actualizado. Nunca push directo a `main`; todo entra por PR.
5. **Commits pequeños** y con mensaje claro (qué y por qué).
6. **Todo PR actualiza** `docs/ESTADO.md` y el estado de su tarea en
   `docs/TAREAS.md`; si cambia algo que afecta a otro rol, añade un aviso en
   `docs/AVISOS.md` en el mismo PR.
7. **Azar solo con `RngStreams`.** Nada de `np.random.*` global ni `random`.
   Añadir un flujo = añadirlo **al final** de `STREAM_NAMES`.
8. **Parámetros solo en configs.** Ningún número del modelo en el código: si
   falta, se añade a `configs/base.json` + `Config` (y se anota en DECISIONES).
9. **Unidades:** reloj SimPy en segundos con t = 0 en el inicio del partido;
   resultados en minutos (ver CONTRATOS).
10. No inventes funcionalidad que la memoria no pide; si algo no está claro,
    anótalo como duda en `docs/ESTADO.md` en vez de decidir en silencio.

## Comandos

```bash
make install            # crea el venv e instala el paquete en editable + dev
make test               # pytest
make lint               # ruff check + ruff format --check
make format             # ruff --fix + format
make check              # lint + test (lo mismo que hace la CI)
make hooks              # activa el hook pre-push (lint + test antes de cada push)
make docs-check         # ¿están al día ESTADO/TAREAS/AVISOS respecto a origin/main?
make run EXP=X0 REPS=10 # ejecuta un experimento (cuando exista run_experiment)
make venv-path          # dónde está el venv
```

Si la ruta del repo contiene `:` (p. ej. `.../26:27/...`), `python -m venv` no
funciona allí y el Makefile usa `~/.venvs/modelos-simulacion-ES-estadio`. Se
puede forzar con `make install VENV=/otra/ruta`.

## Flujo de una tarea

1. `git switch main && git pull && git switch -c feat/<persona>-<tarea>`.
2. Marca la tarea como `en curso` en `docs/TAREAS.md`.
3. Implementa respetando contratos; tests del módulo.
4. `make test && make lint`.
5. Actualiza `docs/ESTADO.md` (qué se ha hecho, siguiente paso, dudas) y
   `docs/TAREAS.md` (`hecho`/`en revisión`).
6. PR a `main` describiendo cambios, contratos tocados y cómo se ha verificado.

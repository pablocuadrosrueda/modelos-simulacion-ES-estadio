# Tablero de tareas

Estados: `pendiente` · `en curso` · `en revisión` · `hecho` · `bloqueada`.
Responsables: **A** = Pablo Cuadros (config, rng, entities, arrivals, entry),
**B** = Pablo Pérez (stadium, exit, emergency, incidents I1/I4), **C** = Chema
(metrics, runner, analysis, experiments, tests). Rama:
`feat/<persona>-<ID>-<slug>` con persona = `cuadros`, `perez` o `chema`.

Al empezar una tarea, pásala a `en curso` en tu rama; al abrir el PR, a
`en revisión`; al fusionarse, a `hecho`. Los stubs del código citan el ID de su
tarea en el mensaje del `NotImplementedError`.

> Nomenclatura: **Inc1..Inc6** son incrementos de desarrollo; **I1..I4** son
> incidencias del modelo (memoria §3.2). Las tareas son **Tn.m** (n = incremento).

## Inc0 · Esqueleto — `hecho`

| ID | Tarea | Resp. | Estado | Depende de |
|---|---|---|---|---|
| T0.1 | Tooling (pyproject, Makefile, ruff, pytest), configs base y experimentos | — | hecho | — |
| T0.2 | `config.py` y `rng.py` implementados con tests | — | hecho | T0.1 |
| T0.3 | Contratos (entities, KPI_COLUMNS, stubs, CONTRATOS.md) | — | hecho | T0.2 |
| T0.4 | Documentación para agentes y README | — | hecho | T0.3 |
| T0.5 | Automatización: CI, plantilla de PR, hook pre-push, `check_pr_docs.py` | — | hecho | T0.4 |

## Inc1 · Rebanada vertical: una macrozona, entrada sin incidencias, CSV y KPIs de espera

Objetivo: `make run EXP=<mini> REPS=3` produce un CSV con KPIs de espera para
una sola macrozona sin incidencias (llegada → torno → asiento). Sin salida.

| ID | Tarea | Resp. | Estado | Depende de |
|---|---|---|---|---|
| T1.1 | `arrivals`: `sample_arrival_times`, `sample_truncated_normal`, `generate_spectators` (+ tests: perfil reproducido, repartos, rangos) | A | hecho | — |
| T1.2 | `entry`: `build_entry_resources`, `priority_of` (solo FIFO), `entry_process` sin incidencias usando `spectator.gate` (+ tests) | A | hecho | T1.1 |
| T1.3 | `stadium`: `build_stadium_resources`, `seating_process` sin conflictos, `is_late` (+ tests) | B | hecho | — (contrato `SimContext`) |
| T1.4 | `runner`: `run_replica` (E0, proceso por espectador entry→seating, E9 al sentarse el último), DataFrame con `SPECTATOR_COLUMNS`, `df.attrs`; config de desarrollo `configs/dev/i1_mini.json` (zona A, sin incidencias) | C | hecho | T1.2, T1.3 |
| T1.5 | `metrics`: `queue_length_max` y KPIs de entrada (`n_*`, `wait_*`, `pct_wait_lt_10`, `queue_max_gate`, `turnstile_util`, `access_mean_min`, `late_pct`); el resto NaN | C | hecho | contrato (T0.3) |
| T1.6 | `experiments.run_experiment` + CLI escribe `results/<exp>_kpis.csv` (aceptar también rutas de config fuera de `configs/experiments`) | C | hecho | T1.4, T1.5 |
| T1.7 | Quitar `xfail` de `test_orden_temporal`; conservación limitada a la entrada; caso límite (muchos tornos → espera ≈ 0) | C | hecho | T1.4 |

T1.1–T1.7 fusionadas en los PR #1, #2, #4, #6, #3, #9 y #10: **Inc1 completado**.
Inc1 completo: T1.1–T1.7 fusionadas en los PR #1, #2, #4, #6, #3, #9 y #10.

## Inc2 · Estadio completo e incidencias de entrada

| ID | Tarea | Resp. | Estado | Depende de |
|---|---|---|---|---|
| T2.1 | 4 macrozonas con N = 48.775; comprobar reparto 25 % y ritmo por torno ≈ 13,6 pers/min; medir tiempo de una réplica (D15) | A | hecho | Inc1 |
| T2.2 | I2 fallo de lectura en `entry_process` (+ registro con `log_incident`) | A | hecho | T2.6 (log_incident, ya en `main`) |
| T2.3 | I3 `turnstile_failure_process` con prioridad máxima, sin cortar servicios | A | hecho | Inc1 |
| T2.4 | Prioridad no expulsiva (X3) en `priority_of` | A | hecho | Inc1 |
| T2.5 | `log_incident`, I1 `has_seat_conflict` + `seat_conflict` con acomodadores (retiene plaza de vomitorio) | B | hecho | Inc1 |
| T2.6 | I4 `gate_closure_process` (cambia `gate_open`, dispara `reopen_event`) | B | hecho | T1.2 |
| T2.7 | `choose_gate` con redirección a la puerta con menos cola / espera a reapertura | A | hecho | T2.6 |
| T2.8 | KPIs P4/P6 e incidencias (`group_wait_diff_min`, `conflict_delay_s`, `n_conflicts`...); test de capacidad de recursos | C | hecho | T2.4, T2.5 |

## Inc3 · Salida ordinaria

| ID | Tarea | Resp. | Estado | Depende de |
|---|---|---|---|---|
| T3.1 | `exit`: recursos, `exit_pass_time_s`, `choose_exit`, `exit_process` (salida simultánea) | B | hecho | Inc1 |
| T3.2 | Salida escalonada (`release_time_min`, X4) | B | hecho | T3.1 |
| T3.3 | `runner`: encadenar asiento → permanencia → salida (E5, E6, E9); KPIs `exit_time_min`, `exit_queue_max`; contrastar con 7,7 min | C | hecho | T3.1 |
| T3.4 | `test_conservacion` completo sin `xfail` | C | hecho | T3.3 |

## Inc4 · Evacuación de emergencia

| ID | Tarea | Resp. | Estado | Depende de |
|---|---|---|---|---|
| T4.1 | `emergency`: `alarm_process` (cierra accesos, abandono de colas, salidas ×1,3) y `evacuation_process` (reacción, velocidad ×1,2) | B | hecho | Inc3 |
| T4.2 | Variante con salida bloqueada en `blocked_exit_zone` | B | hecho | T4.1 |
| T4.3 | `runner`: interrupción de los sentados con `Process.interrupt()`, E8; KPIs `evac_time_min`, `evac_pct_ref`, `n_abandoned`; contrastar con 5,9 / 7,1 min | C | hecho | T4.1 |

## Inc5 · Experimentos y estadística

| ID | Tarea | Resp. | Estado | Depende de |
|---|---|---|---|---|
| T5.1 | Ejecutar X0–X7 con 10 réplicas piloto y semillas comunes | C | hecho | Inc4 |
| T5.2 | `analysis`: `confidence_interval`, `required_replications`, `summarize`, `compare_with_baseline` (+ tests con datos sintéticos) | C | hecho | contrato (T0.3) |
| T5.3 | Réplicas definitivas con precisión verificada del 5 % y S1 | C | hecho | T5.1, T5.2 |
| T5.4 | Rendimiento: medir tiempo por réplica completa y optimizar los cuellos propios | A, B | hecho | T5.1 |

## Inc6 · Análisis, verificación y entrega

| ID | Tarea | Resp. | Estado | Depende de |
|---|---|---|---|---|
| T6.1 | Gráficas (matplotlib) por pregunta P1–P8 en `results/` | C | en revisión | T5.3 |
| T6.2 | Verificación/validación: casos límite (ρ > 1 con 2 tornos), ritmo por torno vs F2, capacidad | A, B, C | pendiente | T5.3 |
| T6.3 | Memoria Parte 2 (resultados y respuestas a P1–P8) | A, B, C | pendiente | T6.1, T6.2 |

## Prompts de arranque de Inc1

Cada persona abre su sesión de agente en su clon y pega el prompt de su rol.
El contexto está en el repo; los prompts solo fijan el alcance y los criterios.

### A · Pablo Cuadros (Claude Code) — T1.1 y T1.2

```
Eres el rol A. Lee AGENTS.md, docs/ESTADO.md, docs/AVISOS.md, docs/DECISIONES.md y docs/CONTRATOS.md.
Tu trabajo en Inc1 son las tareas T1.1 y T1.2 de docs/TAREAS.md, en la rama
feat/cuadros-T1.1-arrivals y después feat/cuadros-T1.2-entry.
- T1.1 (arrivals.py): sample_arrival_times, sample_truncated_normal y
  generate_spectators, usando solo RngStreams. Tests: el perfil por franjas se
  reproduce (chi-cuadrado o tolerancia), los repartos por zona y grupo cuadran, y
  velocidades y distancias respetan sus rangos.
- T1.2 (entry.py): build_entry_resources, priority_of (solo FIFO) y entry_process
  sin incidencias, usando spectator.gate. Tests: orden FIFO y capacidad de tornos.
No toques módulos de B ni de C salvo bugs triviales. Cada PR actualiza ESTADO.md y
TAREAS.md. Antes del PR: make test y make lint limpios.
```

### B · Pablo Pérez (Claude Code) — T1.3

```
Eres el rol B. Lee AGENTS.md, docs/ESTADO.md, docs/AVISOS.md, docs/DECISIONES.md y docs/CONTRATOS.md.
Tu trabajo en Inc1 es la tarea T1.3 de docs/TAREAS.md, en la rama
feat/perez-T1.3-stadium: build_stadium_resources, seating_process sin
conflictos e is_late en stadium.py. Respeta el contrato de SimContext y escribe en
el Spectator t_vomitory y t_seated. Tests: el vomitorio respeta su capacidad de 8
plazas, t_seated >= t_vomitory >= t_fin_control, e is_late solo marca a quien llega
con t < 0 y se sienta después de t = 0.
Mientras A y C avanzan, prepara los stubs de exit.py y emergency.py para Inc3 e
Inc4 sin implementarlos. Cada PR actualiza ESTADO.md y TAREAS.md; make test y
make lint limpios antes del PR.
```

### C · Chema (Codex) — T1.5, T1.4, T1.6 y T1.7

```
Eres el rol C. Lee AGENTS.md, docs/ESTADO.md, docs/AVISOS.md, docs/DECISIONES.md y docs/CONTRATOS.md.
Tu trabajo en Inc1, por este orden (docs/TAREAS.md):
1. T1.5 (metrics.py): queue_length_max y los KPIs de entrada; el resto, NaN.
   Aplica D12 para turnstile_util. Pruébalo con DataFrames sintéticos.
2. T1.4 (runner.py): run_replica (E0, un proceso por espectador entry→seating, E9
   al sentarse el último), con las columnas de SPECTATOR_COLUMNS y df.attrs.
   Crea configs/dev/i1_mini.json (solo la zona A, sin incidencias, N reducido).
   Depende de T1.2 y T1.3: usa stubs o espera a que lleguen a main.
3. T1.6: experiments.run_experiment y la CLI escriben results/<exp>_kpis.csv.
4. T1.7: quita el xfail de test_orden_temporal, conservación limitada a la entrada
   y un caso límite (muchos tornos → espera ≈ 0).
Rama feat/chema-T1.x-slug por tarea. Cada PR actualiza ESTADO.md y TAREAS.md;
make test y make lint limpios antes del PR.
```

Hito de Inc1: `make run EXP=<mini> REPS=3` escribe el CSV de KPIs.

T1.7 fusionada en PR #10; conservación completa T3.4 fusionada en PR #22.
T5.2 fusionada en PR #17: IC t-Student, estimación de réplicas y comparación
por semillas con el formato D29. Véase ESTADO para la verificación actual.

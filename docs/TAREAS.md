# Tablero de tareas

Estados: `pendiente` · `en curso` · `en revisión` · `hecho` · `bloqueada`.
Responsables: **A** (config, rng, entities, arrivals, entry), **B** (stadium,
exit, emergency, incidents I1/I4), **C** (metrics, runner, analysis,
experiments, tests). Rama: `feat/<persona>-<ID>-<slug>`.

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

## Inc1 · Rebanada vertical: una macrozona, entrada sin incidencias, CSV y KPIs de espera

Objetivo: `make run EXP=<mini> REPS=3` produce un CSV con KPIs de espera para
una sola macrozona sin incidencias (llegada → torno → asiento). Sin salida.

| ID | Tarea | Resp. | Estado | Depende de |
|---|---|---|---|---|
| T1.1 | `arrivals`: `sample_arrival_times`, `sample_truncated_normal`, `generate_spectators` (+ tests: perfil reproducido, repartos, rangos) | A | pendiente | — |
| T1.2 | `entry`: `build_entry_resources`, `priority_of` (solo FIFO), `entry_process` sin incidencias usando `spectator.gate` (+ tests) | A | pendiente | T1.1 |
| T1.3 | `stadium`: `build_stadium_resources`, `seating_process` sin conflictos, `is_late` (+ tests) | B | pendiente | — (contrato `SimContext`) |
| T1.4 | `runner`: `run_replica` (E0, proceso por espectador entry→seating, E9 al sentarse el último), DataFrame con `SPECTATOR_COLUMNS`, `df.attrs`; config de desarrollo `configs/dev/i1_mini.json` (zona A, sin incidencias) | C | pendiente | T1.2, T1.3 |
| T1.5 | `metrics`: `queue_length_max` y KPIs de entrada (`n_*`, `wait_*`, `pct_wait_lt_10`, `queue_max_gate`, `turnstile_util`, `access_mean_min`, `late_pct`); el resto NaN | C | pendiente | contrato (T0.3) |
| T1.6 | `experiments.run_experiment` + CLI escribe `results/<exp>_kpis.csv` (aceptar también rutas de config fuera de `configs/experiments`) | C | pendiente | T1.4, T1.5 |
| T1.7 | Quitar `xfail` de `test_orden_temporal`; conservación limitada a la entrada; caso límite (muchos tornos → espera ≈ 0) | C | pendiente | T1.4 |

## Inc2 · Estadio completo e incidencias de entrada

| ID | Tarea | Resp. | Estado | Depende de |
|---|---|---|---|---|
| T2.1 | 4 macrozonas con N = 48.775; comprobar reparto 25 % y ritmo por torno ≈ 13,6 pers/min; medir tiempo de una réplica (D15) | A | pendiente | Inc1 |
| T2.2 | I2 fallo de lectura en `entry_process` (+ registro con `log_incident`) | A | pendiente | T2.5 (log_incident) |
| T2.3 | I3 `turnstile_failure_process` con prioridad máxima, sin cortar servicios | A | pendiente | Inc1 |
| T2.4 | Prioridad no expulsiva (X3) en `priority_of` | A | pendiente | Inc1 |
| T2.5 | `log_incident`, I1 `has_seat_conflict` + `seat_conflict` con acomodadores (retiene plaza de vomitorio) | B | pendiente | Inc1 |
| T2.6 | I4 `gate_closure_process` (cambia `gate_open`, dispara `reopen_event`) | B | pendiente | T1.2 |
| T2.7 | `choose_gate` con redirección a la puerta con menos cola / espera a reapertura | A | pendiente | T2.6 |
| T2.8 | KPIs P4/P6 e incidencias (`group_wait_diff_min`, `conflict_delay_s`, `n_conflicts`...); test de capacidad de recursos | C | pendiente | T2.4, T2.5 |

## Inc3 · Salida ordinaria

| ID | Tarea | Resp. | Estado | Depende de |
|---|---|---|---|---|
| T3.1 | `exit`: recursos, `exit_pass_time_s`, `choose_exit`, `exit_process` (salida simultánea) | B | pendiente | Inc1 |
| T3.2 | Salida escalonada (`release_time_min`, X4) | B | pendiente | T3.1 |
| T3.3 | `runner`: encadenar asiento → permanencia → salida (E5, E6, E9); KPIs `exit_time_min`, `exit_queue_max`; contrastar con 7,7 min | C | pendiente | T3.1 |
| T3.4 | `test_conservacion` completo sin `xfail` | C | pendiente | T3.3 |

## Inc4 · Evacuación de emergencia

| ID | Tarea | Resp. | Estado | Depende de |
|---|---|---|---|---|
| T4.1 | `emergency`: `alarm_process` (cierra accesos, abandono de colas, salidas ×1,3) y `evacuation_process` (reacción, velocidad ×1,2) | B | pendiente | Inc3 |
| T4.2 | Variante con salida bloqueada en `blocked_exit_zone` | B | pendiente | T4.1 |
| T4.3 | `runner`: interrupción de los sentados con `Process.interrupt()`, E8; KPIs `evac_time_min`, `evac_pct_ref`, `n_abandoned`; contrastar con 5,9 / 7,1 min | C | pendiente | T4.1 |

## Inc5 · Experimentos y estadística

| ID | Tarea | Resp. | Estado | Depende de |
|---|---|---|---|---|
| T5.1 | Ejecutar X0–X7 con 10 réplicas piloto y semillas comunes | C | pendiente | Inc4 |
| T5.2 | `analysis`: `confidence_interval`, `required_replications`, `summarize`, `compare_with_baseline` (+ tests con datos sintéticos) | C | pendiente | contrato (T0.3) |
| T5.3 | Réplicas definitivas (≈ 30) y S1 | C | pendiente | T5.1, T5.2 |
| T5.4 | Rendimiento: medir tiempo por réplica completa y optimizar los cuellos propios | A, B | pendiente | T5.1 |

## Inc6 · Análisis, verificación y entrega

| ID | Tarea | Resp. | Estado | Depende de |
|---|---|---|---|---|
| T6.1 | Gráficas (matplotlib) por pregunta P1–P8 en `results/` | C | pendiente | T5.3 |
| T6.2 | Verificación/validación: casos límite (ρ > 1 con 2 tornos), ritmo por torno vs F2, capacidad | A, B, C | pendiente | T5.3 |
| T6.3 | Memoria Parte 2 (resultados y respuestas a P1–P8) | A, B, C | pendiente | T6.1, T6.2 |

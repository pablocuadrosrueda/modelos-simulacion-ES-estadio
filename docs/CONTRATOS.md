# Contratos entre módulos

Este documento es la **fuente de verdad** de las interfaces compartidas. Cambiar
cualquier cosa de aquí (columnas, firmas, unidades, nombres de flujos aleatorios)
exige anotarlo en [`DECISIONES.md`](DECISIONES.md) y avisar a los responsables
afectados en el PR.

## Convenciones

| Aspecto | Convención |
|---|---|
| Reloj SimPy (`env.now`) | **segundos**, con `t = 0` en el inicio del partido. `simpy.Environment(initial_time=config.t_open_min * 60)`, es decir, `-5400`. |
| Tiempos en resultados | **minutos respecto al inicio del partido** (float). La apertura de puertas es `-90`, el final del partido `+105`. Conversión: `entities.s_to_min` y `entities.min_to_s`. |
| Suceso no ocurrido | `NaN` en tiempos; `-1` en identificadores enteros (`gate_used`, `exit_id`). |
| Índices | Puertas, bloques y salidas **1-indexados** dentro de su macrozona. Ids legibles: `A-G1` (puerta), `A-B3` (bloque/vomitorio), `A-S2` (salida), `A-G1-T2` (torno). |
| Proporciones | KPIs `*_pct` en **porcentaje (0-100)**. `turnstile_util` en fracción (0-1). |
| Azar | Solo a través de `RngStreams` (`rng.py`). Nunca `np.random.*` global ni `random`. |

## Configuración (`config.py`)

```python
load_config(path=configs/base.json, overrides=None) -> Config
load_experiment(path, base_path=configs/base.json) -> Experiment  # .configs: tuple[Config, ...]
deep_merge(base: dict, overrides: dict) -> dict
```

* `Config` replica 1:1 las claves de `configs/base.json` (dataclasses inmutables).
  Clave desconocida o ausente, tipo erróneo o regla semántica rota -> `ConfigError`.
* Un fichero de experimento tiene `experiment`, `label`, `question` y **o bien**
  `overrides` (un escenario) **o bien** `variants: [{name, overrides}]` (varios).
  Si un escenario no fija `name`, se usa el nombre del fichero.
* Añadir un parámetro = añadirlo a `base.json` **y** al dataclass correspondiente
  (y a `validate` si tiene reglas).

## Números aleatorios (`rng.py`)

```python
rngs = RngStreams(seed)          # una por réplica
rngs["service"]                   # numpy.random.Generator
```

Flujo `name` = `default_rng(SeedSequence(entropy=seed, spawn_key=(STREAM_INDEX[name],)))`.

Para fuentes **por recurso**, `rngs.substream(name, *clave)` devuelve un generador
nuevo derivado del flujo y de la clave (`str`/`int >= 0`), independiente del orden
de creación (D21). Uso actual: un generador por torno,
`substream("turnstile_failure", zona, puerta, k)`.

| Índice | Flujo | Uso | Módulo |
|---:|---|---|---|
| 0 | `arrivals` | franja e instante de llegada | arrivals |
| 1 | `assignment` | macrozona, puerta, bloque | arrivals |
| 2 | `group` | colectivo | arrivals |
| 3 | `speed` | velocidad de marcha | arrivals |
| 4 | `distance` | distancia puerta -> asiento | arrivals |
| 5 | `service` | servicio en torno (por espectador, en `generate_spectators`; D17) | arrivals |
| 6 | `read_failure` | I2 | entry |
| 7 | `vomitory` | paso por vomitorio (N tiempos en `build_stadium_resources`, por `id`; D18) | stadium |
| 8 | `seat_conflict` | I1 (ocurrencia y resolución) | incidents |
| 9 | `turnstile_failure` | I3 | entry |
| 10 | `exit_choice` | desempates de salida | exit, emergency |
| 11 | `reaction` | reacción a la alarma | emergency |
| 12 | `gate_choice` | desempates al redirigir (I4) | entry |

**Solo se añaden flujos al final.** Reordenar cambia todos los resultados.

## Resultado de una réplica: `runner.run_replica(config, seed) -> pd.DataFrame`

Una fila por espectador (`len(df) == config.n_spectators`), columnas en el orden
de `entities.SPECTATOR_COLUMNS`:

**Alcance provisional de Inc1 (T1.4, D19):** la réplica termina al sentarse el
último espectador, o al alcanzar `max_sim_hours` de tiempo simulado desde la
apertura. Se conservan todas las filas aunque el límite deje sucesos pendientes.
Salida y evacuación permanecen en NaN (ids en -1). Las incidencias y la
emergencia deben estar desactivadas y la cola debe ser FIFO; configuraciones
fuera de este alcance lanzan `NotImplementedError`, sin ignorar opciones activas.
La permanencia y salida se integran en T3.3 y la emergencia en T4.3.

| Columna | Tipo | Quién la rellena | Descripción |
|---|---|---|---|
| `id` | int | arrivals | 0..N-1 |
| `zone` | str | arrivals | Macrozona (`A`..`D`) |
| `gate` | int | arrivals | Puerta asignada (1..6) |
| `block` | int | arrivals | Bloque (1..10) |
| `tier` | str | arrivals | `lower` (bloques 1-5) / `upper` (6-10) |
| `group` | str | arrivals | `standard` / `elderly` / `reduced_mobility` |
| `speed_mps` | float | arrivals | Velocidad × factor del grupo (m/s) |
| `distance_m` | float | arrivals | Distancia puerta -> asiento (también para salir) |
| `t_arrival` | float | arrivals | Llegada a la cola de la puerta (E1) |
| `service_s` | float | arrivals | Tiempo de servicio en torno (s), sorteado al generar (D17) |
| `gate_used` | int | entry | Puerta por la que entra (≠ `gate` si se redirige; -1 si no entra) |
| `t_start_control` | float | entry | Inicio del control (E2) |
| `t_end_control` | float | entry | Fin del control (E3) |
| `read_failure` | bool | entry | Hubo relectura (I2) |
| `t_vomitory` | float | stadium | Llegada a la cola del vomitorio |
| `t_seated` | float | stadium | Sentado (E4) |
| `conflict` | bool | stadium/incidents | Tuvo conflicto por asiento (I1) |
| `late` | bool | stadium | `t_arrival < 0` y `t_seated > 0` |
| `exit_id` | int | exit/emergency | Salida usada (1..6; -1 si no sale) |
| `t_exit_queue` | float | exit/emergency | Llegada a la cola de la salida |
| `t_exit` | float | exit | Paso por la salida ordinaria (E6) |
| `abandoned` | bool | emergency | En cola exterior al sonar la alarma; no cuenta en la evacuación |
| `t_safe` | float | emergency | Llega a zona segura en evacuación (E8) |

`df.attrs`:

* `"incidents"`: DataFrame con `entities.INCIDENT_COLUMNS` =
  `kind` (I1..I4), `zone`, `resource`, `t_start`, `t_end`, `spectator_id`
  (-1 si no aplica). Fallo de lectura (I2): `t_end - t_start` = tiempo extra.
* `"seed"`: semilla de la réplica.
* `"scenario"`: `config.name`.

Invariantes (tests de verificación):

* `t_arrival <= t_start_control <= t_end_control <= t_vomitory <= t_seated <= t_exit_queue <= t_exit` (cuando no son NaN).
* Sin emergencia: todo espectador acaba con `t_exit` no NaN (salvo tope `max_sim_hours`).
* Con emergencia: `t_exit` es NaN y cada espectador tiene `t_safe` o `abandoned` (o no había llegado).

## KPIs por réplica: `metrics.compute_kpis(df, config) -> dict`

Claves = `metrics.KPI_COLUMNS`. `experiments.run_experiment(name, n_reps)` devuelve
una fila por (escenario, réplica) con `metrics.ID_COLUMNS + metrics.KPI_COLUMNS`.
Un KPI que no aplica al escenario vale `NaN`.

| Columna | Unidad | Definición | Preguntas |
|---|---|---|---|
| `experiment` | str | Código del experimento (X0..X7, S1) | — |
| `scenario` | str | `config.name` (p. ej. `X1_2tornos`) | — |
| `replica` | int | 0..n_reps-1 | — |
| `seed` | int | `base_seed + replica` (común a todos los escenarios) | — |
| `n_spectators` | pers. | N simulados | — |
| `n_entered` | pers. | Con `t_end_control` no NaN | — |
| `wait_mean_min` | min | Media de `t_start_control - t_arrival` | P1-P4, P7 |
| `wait_p95_min` | min | Percentil 95 de esa espera | P1-P4, P7 |
| `pct_wait_lt_10` | % | % con espera < 10 min | P2 |
| `queue_max_gate` | pers. | Máximo de personas a la vez en la cola de una puerta (reconstruido con `t_arrival`, `t_start_control`) | P1, P7 |
| `turnstile_util` | 0-1 | Σ(`t_end_control - t_start_control`) / (nº tornos × tiempo desde apertura hasta el último fin de control) | P1, P2 |
| `access_mean_min` | min | Media de `t_seated - t_arrival` | P1 |
| `late_pct` | % | De los que tienen `t_arrival < 0`, % con `t_seated > 0` | P1-P4, P6 |
| `wait_mean_priority_min` | min | Espera media de `priority_groups` (NaN si no hay) | P4 |
| `wait_mean_rest_min` | min | Espera media del resto | P4 |
| `group_wait_diff_min` | min | priorizados − resto | P4 |
| `conflict_delay_s` | s/pers. | Media de `t_seated - t_vomitory` en bloques con algún conflicto activo menos la de bloques sin conflicto (excluye a quien tiene el conflicto) | P6 |
| `n_conflicts` | nº | Incidencias I1 | P6 |
| `n_read_failures` | nº | Incidencias I2 | — |
| `n_turnstile_failures` | nº | Incidencias I3 | — |
| `exit_time_min` | min | max(`t_exit`) − `t_end_min` | P5 |
| `exit_queue_max` | pers. | Máximo a la vez en la cola de una salida (`t_exit_queue`, `t_exit`) | P5 |
| `evac_time_min` | min | max(`t_safe`) − `alarm_min` | P8 |
| `evac_pct_ref` | % | % de evacuables con `t_safe - alarm_min <= reference_min` | P8 |
| `n_abandoned` | pers. | `abandoned == True` | P8 |

> `turnstile_util` y `conflict_delay_s` quedan fijadas en `docs/DECISIONES.md`
> (D12); si se cambia alguna, actualizar esta tabla y esa decisión.

## Firmas de los procesos (resumen)

| Módulo | Función | Contrato |
|---|---|---|
| arrivals | `generate_spectators(config, rngs) -> list[Spectator]` | N espectadores con atributos iniciales |
| entry | `build_entry_resources(ctx)`, `entry_process(sp, ctx)`, `choose_gate`, `priority_of`, `turnstile_failure_process(zone, gate, ctx)`, `start_turnstile_failure_processes(ctx) -> list[Process]` | E1-E3, I2, I3. `entry_process` espera él mismo hasta `t_arrival` (D16). I3: incidencia con `resource = "A-G1-T2"` (D21) |
| stadium | `build_stadium_resources(ctx)`, `seating_process(sp, ctx)`, `is_late` | E3->E4 |
| incidents | `log_incident`, `has_seat_conflict`, `seat_conflict(sp, ctx)` (sub-proceso), `gate_closure_process(ctx)` | I1, I4 |
| exit | `build_exit_resources(ctx)`, `exit_process(sp, ctx)`, `choose_exit`, `release_time_min`, `exit_pass_time_s` | E5, E6 |
| emergency | `alarm_process(ctx)`, `evacuation_process(sp, ctx)` | E7, E8 |
| runner | `SimContext`, `run_replica(config, seed)` | E0, E9 |
| metrics | `compute_kpis(df, config)`, `queue_length_max` | KPIs |
| experiments | `run_experiment(name, n_reps, base_seed)`, `find_experiment_file`, `replica_seed` | réplicas |
| analysis | `confidence_interval`, `required_replications`, `summarize`, `compare_with_baseline` | §5.3 |

`ctx` es un `runner.SimContext` (env, config, rngs, spectators, incidents,
entry, stadium, exits, phase). Los procesos SimPy son generadores que reciben
`(spectator, ctx)` y mutan el `Spectator`.

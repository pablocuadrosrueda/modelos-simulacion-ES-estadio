# Avisos entre roles

Tablón para cambios que **afectan a otro rol**: una interfaz que cambia, algo que
aún no está en `main`, un orden de ejecución que conviene respetar. Lo lees al
iniciar sesión, después de `docs/ESTADO.md`.

Reglas:
* Si tu PR cambia un contrato (campos de `Spectator`, firmas, columnas, flujos
  aleatorios), añade un aviso **en el mismo PR**: fecha, de quién a quién, qué
  cambia, qué tiene que hacer el otro y cuándo está en `main`.
* Marca el aviso como **vigente** hasta que esté fusionado en `main` y los
  afectados lo hayan aplicado; entonces pásalo a «Archivo».
* La decisión de fondo va en `docs/DECISIONES.md`; aquí solo la consecuencia práctica.

## Vigentes

### 2026-11-23, de B a C: salida ordinaria lista (T3.1, T3.2, D24)
**Estado:** en la rama `feat/perez-T3.1-exit`; **aún no en `main`**.

* **C (T3.3):** en E0, `ctx.exits = build_exit_resources(ctx)` (después de
  `ctx.stadium`). Encadena `yield from seating_process(sp, ctx)` y después
  `yield from exit_process(sp, ctx)`: `exit_process` espera él solo hasta su
  liberación (`release_time_min`, ya con la política escalonada de X4) y rellena
  `exit_id`, `t_exit_queue` y `t_exit`. No hay que lanzar nada en E5.
* **C (T3.3, KPIs):** `exit_queue_max` se reconstruye con `t_exit_queue` y
  `t_exit` por `(zone, exit_id)`; el paso dura `pass_time_s` (unos 0,23 s), así que
  quien está pasando cuenta en la cola hasta `t_exit`.
* **B (T4.x):** `ExitResources.blocked` y `pass_time_s` son los que cambiará la alarma.

### 2026-11-23 · C → A, B · Inc2 conectado e indicadores (T2.8, D25)
**Estado:** preparado para PR desde `feat/chema-T2.8-metrics`.

* Aplicados los avisos de prioridad, I1, I3 e I4. El runner ya lanza averías y
  cierre en E0; mantiene I2/emergencia pendientes. La cola usa `gate_used`.
* Calcula P4, contraste P6 por solape temporal y recuentos de incidencias.
  Definiciones exactas en CONTRATOS/D25. No cambia Spectator ni firmas.
* Caso de desarrollo: `make run EXP=configs/dev/i2_mini.json REPS=3`.

### 2026-11-23 · A → C · Redirección ante el cierre de puerta (T2.7, D23)
**Estado:** **en `main`** (PR #16). Pendiente de aplicar por C (runner y métricas).

* **C (runner), para poder ejecutar X6:** lanzar
  `incidents.gate_closure_process(ctx)` en E0, después de
  `build_entry_resources` (con el cierre desactivado termina al instante), y
  dejar de rechazar `gate_closure.enabled = true`. `entry_process` ya llama a
  `choose_gate` y espera la reapertura por sí solo.
* **C (métricas):** `gate_used` puede diferir de `gate` cuando hay redirección.
  Hoy `compute_kpis` calcula `queue_max_gate` con `df.groupby(["zone", "gate"])`,
  la puerta **asignada**: con X6 mezclaría colas de puertas distintas. Debe
  agrupar por `["zone", "gate_used"]`. `turnstile_util` no se ve afectada (es
  global, sobre `n_turnstiles`).
* Quien espera a la reapertura cuenta como en cola de su puerta desde
  `t_arrival` hasta `t_start_control`, así que su espera entra en `wait_*` y en
  la cola de esa puerta.

### 2026-11-23 · B → A, C · I1 conflicto por asiento (T2.5, D21)
**Estado:** **en `main`** (PR #13). Pendiente de aplicar por C.

* **C (runner):** `seating_process` ya aplica I1 por sí solo; no hay que lanzar
  nada más. Para ejecutar X0 o X5 falta que `run_replica` deje de rechazar
  `seat_conflict.enabled = true` (D19).
* **C (T2.8):** cada conflicto deja `Spectator.conflict = True` y una incidencia
  `I1` con `resource` = bloque (`"A-B3"`), `spectator_id`, `t_start` (al llegar al
  asiento) y `t_end` (resuelto). `n_conflicts` = incidencias `I1`. Para
  `conflict_delay_s`: el bloque está «con conflicto activo» entre `t_start` y `t_end`.
* **A:** el sorteo de I1 no va en `generate_spectators` (D17); se hace en E0 dentro
  de `build_stadium_resources` (D21), así que `arrivals` no cambia.

### 2026-11-23 · A → C · I3 avería de torno lista para el runner (T2.3, D22)
**Estado:** **en `main`** (PR #14). Pendiente de aplicar por C.

* **C (runner):** en E0, después de `ctx.entry = build_entry_resources(ctx)`,
  llamar a `entry.start_turnstile_failure_processes(ctx)`. Si
  `incidents.turnstile_failure.enabled` es falso no crea nada, así que se puede
  llamar siempre.
* **C (runner):** dejar de rechazar `turnstile_failure.enabled = true` en la
  guarda de incidencias (las demás siguen pendientes).
* Los procesos de avería **no terminan**: la réplica debe acabar por
  `finished | time_limit`, como ya hace; no esperar a que acaben.
* Cada avería queda en `ctx.incidents` como `Incident("I3", zona, "A-G1-T2",
  t_start, t_end)` (min), y por tanto en `df.attrs["incidents"]`;
  `n_turnstile_failures` puede contar las filas `kind == "I3"`. Duda abierta
  para T2.8 en ESTADO (averías después de la entrada).
* **Todos:** sin cola, `t_start_control` es ahora exactamente `t_arrival` (aviso
  de B en T1.3); las tolerancias existentes siguen siendo válidas.

### 2026-11-23 · A → C · Prioridad no expulsiva en el torno (T2.4, D20)
**Estado:** **en `main`** (PR #8). Pendiente de aplicar por C.

* **C (runner):** `run_replica` todavía lanza `NotImplementedError` si
  `queue_discipline != "fifo"` («pendiente de T2.4»). Ya se puede quitar esa
  guarda: `entry_process` aplica la prioridad por sí solo (`priority_of`,
  `preempt=False`) y no hace falta nada más en E0. Sin esto, X3 no se puede ejecutar.
* **C (T2.8):** `wait_mean_priority_min` y `group_wait_diff_min` se calculan con
  `config.priority_groups`, no con la disciplina (D20).
* **Numeración:** la semántica de la prioridad entró en `main` como un segundo
  D19; se renumera a **D20**. D19 es el alcance provisional del runner (T1.4).

### 2026-11-23 · B → A, C · I4 cierre de puerta y `log_incident` (T2.6)
**Estado:** **en `main`** (PR #5). Pendiente de aplicar: C (lanzarlo en el runner)
y A (T2.2, T2.7).

* **C (runner):** lanza `incidents.gate_closure_process(ctx)` en E0, después de
  `build_entry_resources`. Con `gate_closure.enabled = false` termina al instante,
  así que se puede lanzar siempre.
* **A (T2.2, T2.3, T2.7):** `log_incident(ctx, Incident(...))` ya está implementado:
  añade la incidencia a `ctx.incidents` y la devuelve para fijar `t_end` después.
* **A (T2.7):** al reabrir, `gate_closure_process` dispara `reopen_event[(zona, puerta)]`
  y lo **sustituye por un evento nuevo**. Quien espera debe leer
  `ctx.entry.reopen_event[key]` en el momento de esperar, no guardarlo antes.
  Los que esperan se reanudan en orden de registro (D13; hay un test en
  `tests/test_incidents.py`). `gate_open[key]` ya es `True` cuando se reanudan.

### 2026-11-23 · C → A, B · Réplicas y CSV de Inc1 (T1.6)
**Estado:** **en `main`** (PR #9).

* `make run EXP=configs/dev/i1_mini.json REPS=3` ejecuta tres réplicas y guarda
  los indicadores en `results/i1_mini_kpis.csv`. La API devuelve la tabla sin
  escribir ficheros. Las semillas son comunes entre variantes.
* Se corrige en métricas el redondeo s/min señalado por B: esperas de magnitud
  <= 1e-9 min se consideran cero, sin contar colas ficticias ni fallar por una
  diferencia numérica negativa. No cambian columnas, firmas ni parámetros.

### 2026-11-23 · C → A, B · Runner de Inc1 preparado (T1.4, D19)
**Estado:** **en `main`** (PR #6). Vigente mientras el runner rechace
incidencias, emergencia o prioridad.

* Conecta entrada y asiento con las interfaces de T1.2/T1.3. Devuelve una fila
  por espectador, las columnas acordadas y los metadatos de la réplica.
* Por ahora termina al sentarse el último o al alcanzar `max_sim_hours` desde
  apertura. Las fases posteriores siguen pendientes; sucesos no ocurridos, NaN.
* Las configuraciones deben ser FIFO y desactivar incidencias y emergencia;
  otras opciones lanzan `NotImplementedError` (D19). Para probar, cargar
  `configs/dev/i1_mini.json` con `load_experiment` o, desde T1.6, `make run`.

### 2026-11-20 · A → B, C · `Spectator.service_s` y orden de entrada (D16, D17)
**Estado actualizado:** T1.1 y T1.2 fusionadas en `main` (PR #1 y #2).
Sigue vigente la aplicación de D17 a las futuras incidencias de Inc2.

* **`Spectator` tiene un argumento obligatorio más:** `service_s` (tiempo de
  servicio en torno, s), justo después de `t_arrival`. Si construyes
  `Spectator(...)` a mano en tus tests, pásalo (p. ej. `4.0`). Aparece como
  columna en el DataFrame de resultados.
* **Todo sorteo por espectador se hace al generarlo** (D17), no dentro de los
  procesos: así los números aleatorios son comunes entre escenarios. Quien
  implemente I1 o I2 debe sortear ocurrencia y duración en `generate_spectators`
  y guardarlas como atributo (ver D17).
* **`generate_spectators` devuelve la lista ordenada por `t_arrival`**
  (`id` crece con la llegada).
* **`entry_process(sp, ctx)` espera por sí mismo hasta `t_arrival`** (D16):
  `run_replica` (C) puede lanzar todos los procesos en t = −90 en orden de `id`,
  sin calcular retardos. A igual instante de llegada, el orden de lanzamiento
  decide el turno en el torno.
* **`entry.service_time_s` ya no existe.** No lo uses.
* **B (T1.3):** `seating_process` parte de `sp.t_end_control` y escribe
  `t_vomitory` y `t_seated`.
* **C (T1.4):** aplicado en el runner (PR #6).

## Archivo

### 2026-11-23 · B → A, C · `stadium` listo (T1.3) y precisión de tiempos
**Estado:** fusionado en `main` (PR #4) y aplicado por C en T1.4 (PR #6),
incluida la tolerancia numérica en el orden temporal.

* **C (T1.4):** `run_replica` crea `ctx.stadium = build_stadium_resources(ctx)`
  en E0 (después de `ctx.entry`) y encadena
  `yield from entry_process(sp, ctx)` → `yield from seating_process(sp, ctx)`.
  `seating_process` también espera solo hasta `t_end_control` si se lanza antes.
  Rellena `t_vomitory`, `t_seated` y `late`; `conflict` queda en `False` hasta T2.5.
* **C (T1.4, D18):** `build_stadium_resources` usa `config.n_spectators` y el `id`
  como índice: los `id` deben ir de 0 a N−1 (ya lo garantiza `generate_spectators`).
* **A y C · coma flotante:** al convertir s ↔ min (`s_to_min(min_to_s(x))`)
  `t_start_control` puede quedar ~1e-14 min por debajo de `t_arrival` cuando no
  hay espera. Los tests de invariantes (T1.7, `test_orden_temporal`) deben comparar
  con tolerancia, o A puede guardar `t_start_control = t_arrival` cuando no hay cola.

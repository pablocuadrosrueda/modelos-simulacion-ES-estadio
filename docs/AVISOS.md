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

### 2026-11-23 · C → A, B · Runner de Inc1 preparado (T1.4, D19)
**Estado:** **en `main`** (PR #6). Vigente mientras el runner rechace
incidencias, emergencia o prioridad.

* Conecta entrada y asiento con las interfaces de T1.2/T1.3. Devuelve una fila
  por espectador, las columnas acordadas y los metadatos de la réplica.
* Por ahora termina al sentarse el último o al alcanzar `max_sim_hours` desde
  apertura. Las fases posteriores siguen pendientes; sucesos no ocurridos, NaN.
* Las configuraciones deben ser FIFO y desactivar incidencias y emergencia;
  otras opciones lanzan `NotImplementedError` (D19). Para probar, cargar
  `configs/dev/i1_mini.json` con `load_experiment`; la CLI llega en T1.6.

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

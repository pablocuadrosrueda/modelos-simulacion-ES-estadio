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

### 2026-11-23 · B → A, C · `stadium` listo (T1.3) y precisión de tiempos
**Estado:** en la rama `feat/perez-T1.3-stadium`; **aún no en `main`**.

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

### 2026-11-20 · A → B, C · `Spectator.service_s` y orden de entrada (D16, D17)
**Estado:** en las ramas `feat/cuadros-T1.1-arrivals` y `feat/cuadros-T1.2-entry`;
**aún no en `main`** (esperan sus PR). Hasta entonces, para trabajar contra ello,
parte de `feat/cuadros-T1.2-entry` o espera a la fusión.

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
* **C (T1.4):** `run_replica` depende de T1.2 y T1.3 en `main`; hasta entonces,
  stubs.

## Archivo

_(vacío)_

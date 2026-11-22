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

### 2026-11-20 · A → B, C · `Spectator.service_s` y orden de entrada (D16, D17)
**Estado actualizado el 2026-11-22:** T1.1 y T1.2 ya están en `main`
(PR #1 y #2 fusionados el 2026-11-20). Se puede partir de `main` actualizado.
El aviso sigue vigente para las obligaciones de D17 en las futuras incidencias
de Inc2 y hasta que los afectados hayan aplicado sus consecuencias.

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
* **C (T1.4):** T1.2 ya está en `main`; queda T1.3 para verificar la cadena
  completa de entrada y asiento. T1.5 se puede implementar con datos sintéticos.

## Archivo

_(vacío)_

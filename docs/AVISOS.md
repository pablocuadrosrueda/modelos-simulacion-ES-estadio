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

### 2026-11-25 · C → A, B · Parte C de T6.2 verificada
**Estado:** en revisión en `feat/chema-T6.2-verificacion-C`; T6.2 conjunta sigue en curso.

* Auditoría reproducible de 2.965 filas finales, reparto, colectivos, relojes,
  resúmenes, contrastes por semilla y precisión: `scripts/verify_results.py`.
* `--replay`: una réplica por cada uno de los 19 escenarios, desde sus configs
  resueltas y semilla original; coinciden los 21 KPIs y metadatos de auditoría.
  No son réplicas nuevas ni amplían la muestra de T5.3. La huella del código
  normaliza CRLF→LF para admitir los finales de línea de Git en Windows.
* Informe: `docs/VERIFICACION_C_T6.2.md`, con alcance y límites. No se han tocado
  módulos de A/B, parámetros, contratos ni resultados de la campaña.
* A y B: revisar y confirmar vuestra evidencia existente de capacidad y supuestos
  para cerrar T6.2. No hace falta rehacer comprobaciones vigentes.
* T6.1 ya fusionada en PR #30. T6.3 depende del cierre conjunto de T6.2.
### 2026-11-25, de B a A y C: T6.2 en marcha y lectura de P8
**Estado:** en la rama `feat/perez-T6.2-validation`; **aún no en `main`**.

* **A y C:** `docs/VALIDACION_T6.2.md` reúne todas las comprobaciones del
  apartado 6 de la especificación con su prueba y resultado. Revisad vuestras
  filas (A: casos límite de entrada y ritmo por torno; C: conservación, orden
  temporal y precisión) y añadid lo que falte.
* **C (T6.3 y gráficas de P8):** con todas las salidas, las 17 de 180 réplicas
  que superan 8 min se deben a una sola persona de movilidad reducida que camina
  despacio y lejos; sin ese colectivo el vaciado no pasa de 7,36 min. La
  respuesta a P8 debe distinguirlo: con todas las salidas falla la marcha de
  esas personas, no la capacidad de las salidas; con una bloqueada, sí falla la
  capacidad. Se reproduce con `scripts/validate_b.py`.
### 2026-11-25 · A → B, C · T6.2: parte de A hecha, lo vuestro listado
**Estado:** en revisión en `feat/cuadros-T6.2-verificacion`.

* Entrada y capacidad verificadas con `results/final` (sin regenerarlo) en
  `docs/VERIFICACION.md`, sección T6.2, con la tabla «Validación frente a la
  memoria» y las correcciones del PDF.
* **B y C:** vuestra parte está en «Pendiente de B y C» del mismo fichero, con
  las cifras de partida (salida 8,37 frente a 7,7; evacuación 7,47/8,42 frente a
  5,9/7,1; I1 5,32 min frente a 4,67 de la triangular; vaciado máximo 9,3576 en
  las dos variantes de X7). Añadid vuestras secciones ahí para no pisaros.
* `capacity.py` gana el modelo fluido y `busy_rate_per_turnstile` (antes copiada
  en el test y el script de T2.1). No cambian contratos, configs ni flujos.
  No se ha encontrado ningún error en módulos de B o C.


### 2026-11-25 · C → A, B · Figuras para la memoria (T6.1)
**Estado:** fusionadas en `main` mediante PR #30.

* P1–P8 y S1: `results/figures`, PNG 300 dpi y SVG. Índice e interpretación:
  `docs/GRAFICAS_T6.1.md`. Datos definitivos de T5.3 (PR #29 fusionada).
* P4 usa `groups.csv` (D32); P6 no confunde duración I1 con retraso al resto.
  P8 muestra 163/180 frente a 0/180 réplicas vaciadas en ≤8 minutos.
* Para la memoria, conservar unidades, IC y tamaños; no afirmar cumplimiento
  universal por una media menor de ocho minutos ni optimalidad de nueve acomodadores.
* Sin cambios de contratos o parámetros. Siguiente: T6.2 conjunta, luego T6.3.


### 2026-11-23 · C → A, B · T5.3 completa, X5 nueve y X6 recalculado (D33/D34)
**Estado:** fusionada en `main` mediante PR #29.

* 2.965 réplicas completas, 19 escenarios con tamaños entre 30 y 247. Todos
  cumplen IC 95 % con semianchura ≤5 % de la espera media (máximo 4,9865 %).
* X5 mantiene 3/6 y añade 9, con los parámetros originales. Duración I1 con
  espera: 44,60 / 13,74 / 6,64 min (180 por nivel). No se altera lógica de B.
* X6 usa −30: espera de afectados 0,543 min con redirección y 9,626 sin ella.
  El piloto antiguo en +20 queda histórico, fuera de las tablas definitivas.
* X7: vaciado completo ≤8 min en 163/180 sin bloqueo y 0/180 con uno; medias
  7,469 y 8,420 min. Porcentaje casi 100 % no implica todos fuera en cada partido.
* Datos/procedencia en `results/final`, informe en `docs/RESULTADOS_T5.3.md`.
  Modelo calculado en `fd6475c` y hashes comprobados antes de ajustes posteriores
  de las herramientas. No se reescribe la procedencia de los resultados.
* Corregidas rutas Windows; CI específica de rutas/spawn/reanudación. Al
  reanudar se conservan los tamaños planificados y nunca se duplican semillas.
* C puede empezar T6.1; T6.2/T6.3 son conjuntas. Partes 1/2 deben justificar
  D31 (−30) y D33 (nueve), además de explicar la saturación. Se mantienen D23/D25.

## Archivo

### 2026-11-23 · C → A, B · Decisión X5 y campaña T5.3 (D33/D34)
**Estado:** en curso en `feat/chema-T5.3-final`, por petición de Chema.

* X5 añade nueve acomodadores, conservando tres/seis, probabilidad del 1 %,
  resolución Triangular(1,3,10) min y atención de un conflicto por acomodador.
  La saturación se analiza como resultado de P6; no se cambia lógica de B.
* Se repite el piloto de X6 en −30 (D31) e incluye X5 con nueve y S1. Los datos
  de X6 en +20 quedan históricos; los de `results/final/pilot` los sustituyen.
* T5.3: mínimo treinta y estimación del piloto por escenario; se amplía hasta
  comprobar el IC al 95 % con semianchura ≤5 % de la espera media. Semillas
  comunes en los índices compartidos; checkpoints para reanudar sin duplicar.
* Corregidas las rutas portables del manifiesto y añadida CI de Windows para
  rutas y reanudación con procesos. Formato de resultados en CONTRATOS.

### 2026-11-23 · C → A, B · Piloto T5.1 y cohortes de P4 (D32)
**Estado:** en revisión desde `feat/chema-T5.1-pilot`; informe en `docs/PILOTO_T5.1.md`.

* 120 réplicas de X0–X7 terminadas completas, con semillas comunes. El criterio
  del 5 % estima hasta 181 réplicas totales, no 30 por defecto; se verificará
  la precisión al ampliar. Se conservan parámetros e hipótesis de la memoria.
* P4: el X0 tiene `priority_groups=[]`; «resto» no era el mismo colectivo que
  en X3. Se añade análisis con cohortes comunes de X3, sin cambiar simulación,
  configs ni KPIs originales. Formato en CONTRATOS/D32.
* T2.1 de A ya está fusionada (PR #25); capacidad/rendimiento en VERIFICACION.
  Siguen pendientes de decisión del grupo el cierre X6 en +20 y el recuento I3.

### 2026-11-23 · A → C · Cierre de puerta de X6 movido a −30 min (D31, decidida)
**Estado:** decidida; el cambio va en la rama `feat/cuadros-X6-study` y estará en
`main` al fusionarse su PR. Hasta entonces, para un piloto, usa el override
`{"incidents": {"gate_closure": {"start_min": -30}}}`.

* **C (T5.1):** `configs/base.json` pasa a `gate_closure.start_min = -30`
  (10 min, puerta A-1). Los `X6_*.json` lo heredan. Con +20, X6 no respondía a P7;
  con −30, sin redirección cuesta ≈ 5 min de espera media a los asignados a la
  puerta cerrada y +0,7 p. p. de entrada tardía; con redirección el impacto
  desaparece. No hace falta cambiar nada más en el runner.
* **C (T5.1, KPIs de P7):** el p95 global apenas cambia con el cierre (1 de 24
  puertas). Para P7 son más informativos `queue_max_gate`, `late_pct` y la espera
  de los asignados a la puerta cerrada (`gate == 1`, zona A); ver
  `docs/ESTUDIO_X6.md`.

### 2026-11-23 · C → A, B · I2 y alarma conectadas en el runner (T4.3, D30)
**Estado:** fusionada en `main` (PR #24).

* Aplicadas T2.2, T4.1 y T4.2: I2 ya se admite; la alarma interrumpe el proceso
  único de cada espectador y E8 espera a todos los recorridos, no a las averías.
* Metadatos nuevos: `stop_time_min` y `alarm_triggered`. KPIs de evacuación con
  denominador de todos los evacuables; vaciado incompleto o porcentaje aún no
  observable, NaN. Casos/definiciones en CONTRATOS y D30.
* La doble D25 de trabajo paralelo se desambigua: Inc2 conserva D25, evacuación
  de B pasa a D28; estadística usa D29 (PR #17). Solo referencias en módulos de B.
* `make run EXP=configs/dev/i4_mini.json REPS=3`: dos variantes, todas las
  incidencias activadas, una salida bloqueada frente a todas abiertas.


### 2026-11-23 · C → A, B · Runner hasta salida ordinaria (T3.3, D27)
**Estado:** **en `main`** (PR #20).

* Aplicado el contrato de T3.1/T3.2: recursos en E0 y asiento → salida. Ya no
  termina al sentarse el último. Las políticas simultánea y escalonada funcionan.
* Los dos xfail de salida se activan. KPI de vaciado NaN si la réplica se trunca;
  cola máxima por salida incluye paso en servicio. Evacuación e I2 pendientes.
* Caso reproducible: `make run EXP=configs/dev/i3_mini.json REPS=3`.

### 2026-11-23, de B a C: evacuación lista para el runner (T4.1, T4.2, D28)
**Estado:** en `main` (PR #19); aplicada por C en la rama T4.3.

* **C (T4.3):** cada espectador va en un único proceso con `try` y
  `except simpy.Interrupt`. Dentro del `try`, el recorrido normal (entrada,
  asiento, permanencia, salida); en el `except`,
  `yield from emergency.evacuation_process(sp, ctx)`.
* **C (T4.3):** en E0, después de crear `ctx.exits` y la lista de procesos,
  lanzar `env.process(emergency.alarm_process(ctx, journeys))`, con
  `journeys[i]` el proceso del espectador `id == i`. Con la emergencia
  desactivada termina al instante, así que se puede lanzar siempre. Hay que dejar
  de rechazar `emergency.enabled = true`.
* **C (T4.3):** E8 es cuando terminan todos los procesos de espectadores (los
  que no habían llegado o abandonan terminan al momento). Los procesos de
  averías (I3) no terminan nunca: no esperar por ellos.
* **C (KPIs):** `abandoned` marca a quien estaba en cola exterior; quien no
  había llegado queda con `t_safe` NaN y `abandoned = False`. Los evacuables son
  quienes tienen `t_safe`.
### 2026-11-23 · A → C · I2 fallo de lectura; incidencias de entrada completas (T2.2, D26)
**Estado:** en `main` (PR #21); aplicada por C en la rama T4.3.

* **C (runner):** con T2.2, T2.3, T2.5, T2.6 y T2.7 todas las incidencias de
  entrada están implementadas. En `main` el runner aún rechaza cualquier
  incidencia con `NotImplementedError` y no lanza
  `start_turnstile_failure_processes(ctx)` ni `gate_closure_process(ctx)`: sin
  eso **X0, que las lleva activadas, no se puede ejecutar**. El PR abierto de
  T2.8 ya integra I1, I3 e I4 pero sigue rechazando I2 («pendiente de T2.2»);
  cuando T2.2 esté en `main`, esa guarda se puede quitar. I2 no necesita nada
  en E0: el sorteo va en `build_entry_resources` y la relectura en
  `entry_process`.
* **C (métricas):** `n_read_failures` = filas `kind == "I2"` de
  `df.attrs["incidents"]` (coincide con `df["read_failure"].sum()`). La
  relectura ocupa el torno, así que entra en el servicio de `turnstile_util`
  (`t_end_control - t_start_control`), como pide D12.
* `build_entry_resources` consume ahora el flujo `read_failure` (no afecta a los
  demás flujos ni a resultados previos).

### 2026-11-23 · C → A, B · Inc2 conectado e indicadores (T2.8, D25)
**Estado:** fusionada en `main` (PR #18).

* Aplicados los avisos de prioridad, I1, I3 e I4. El runner ya lanza averías y
  cierre en E0; mantiene I2/emergencia pendientes. La cola usa `gate_used`.
* Calcula P4, contraste P6 por solape temporal y recuentos de incidencias.
  Definiciones exactas en CONTRATOS/D25. No cambia Spectator ni firmas.
* Caso de desarrollo: `make run EXP=configs/dev/i2_mini.json REPS=3`.

### 2026-11-23 · C → A, B · Análisis estadístico de réplicas (T5.2, D29)
**Estado:** publicada en PR #17; D29 distingue estadística de D24 (salida).

* `summarize` devuelve media, semianchura y n válido de cada KPI por escenario.
  `compare_with_baseline` usa diferencias escenario − base emparejadas por seed.
  El formato exacto está en CONTRATOS. No cambian los CSV por réplica ni Spectator.
* Los NaN se omiten por KPI; con una sola réplica la semianchura es NaN.
  Semillas duplicadas por escenario se rechazan, sin contarlas como réplicas nuevas.
* T1.6 ya fusionada en el PR #9; T1.7 publicada en el PR #10. Los checks de ambos
  (Python 3.10/3.12 y documentación) han pasado.


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


### 2026-11-23, de B a C: salida ordinaria lista (T3.1, T3.2, D24)
**Estado:** en `main` (PR #15) y aplicado por C en T3.3 (PR #20).

* **C (T3.3):** en E0, `ctx.exits = build_exit_resources(ctx)` (después de
  `ctx.stadium`). Encadena `yield from seating_process(sp, ctx)` y después
  `yield from exit_process(sp, ctx)`: `exit_process` espera él solo hasta su
  liberación (`release_time_min`, ya con la política escalonada de X4) y rellena
  `exit_id`, `t_exit_queue` y `t_exit`. No hay que lanzar nada en E5.
* **C (T3.3, KPIs):** `exit_queue_max` se reconstruye con `t_exit_queue` y
  `t_exit` por `(zone, exit_id)`; el paso dura `pass_time_s` (unos 0,23 s), así que
  quien está pasando cuenta en la cola hasta `t_exit`.
* **B (T4.x):** `ExitResources.blocked` y `pass_time_s` son los que cambiará la alarma.

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

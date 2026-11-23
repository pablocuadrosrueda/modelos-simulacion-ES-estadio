# Registro de decisiones

Cada entrada: fecha, decisión, motivo y consecuencias. **Todo cambio de contrato**
(firmas, columnas, unidades, flujos aleatorios, claves de config) se anota aquí.
Las entradas no se borran; si una decisión se revierte, se añade otra que la
sustituya.

---

### D1 · Layout `src/` con paquete `sanmames` — 2026-11-19
Código en `src/sanmames/`, tests en `tests/`, scripts en `scripts/`. Instalación
editable (`pip install -e .[dev]`).
**Motivo:** evita importar por accidente desde la raíz y obliga a instalar el
paquete como lo usarán los scripts y los tests.

### D2 · Un generador aleatorio por fuente de azar — 2026-11-19
`RngStreams(seed)` da un `numpy.random.Generator` por fuente (`rng.STREAM_NAMES`),
derivado con `SeedSequence(entropy=seed, spawn_key=(índice,))`. El índice es la
posición fija del nombre.
**Motivo:** reproducibilidad y números aleatorios comunes entre escenarios
(memoria §4.5 y §5.3): un cambio en una fuente no desplaza las demás.
**Consecuencia:** solo se añaden flujos al final de `STREAM_NAMES`.

### D3 · Configs como diff sobre `base.json` — 2026-11-19
Cada experimento declara solo lo que cambia (`overrides`) o una lista de
`variants`. `load_config` hace fusión profunda (los dicts se fusionan, las
listas se reemplazan) y valida estrictamente (clave desconocida → error).
**Motivo:** «cambiar un solo factor» (memoria §5.1) queda explícito y no se
duplican parámetros.

### D4 · `CLAUDE.md` importa `AGENTS.md` — 2026-11-19
`CLAUDE.md` contiene solo `@AGENTS.md`. Las instrucciones viven en `AGENTS.md`,
que leen tanto Claude Code como Codex.
**Motivo:** una única fuente de instrucciones para todos los agentes.

### D5 · Repo único en `modelos-simulacion-ES-estadio/` — 2026-11-19
Es el único repositorio git (remoto `origin` en GitHub). No hay repo en el
directorio superior `proyecto-final/`.

### D6 · Convenciones de tiempo — 2026-11-19
Reloj SimPy en segundos con t = 0 en el inicio del partido
(`Environment(initial_time=t_open_min*60)`); resultados en minutos respecto al
inicio. Ver `docs/CONTRATOS.md`.
**Motivo:** coincide con la memoria (§4.2) y evita conversiones con desfase.

### D7 · Resultados autosuficientes — 2026-11-19
El DataFrame por espectador incluye, además de los atributos de la memoria
(§4.1), `gate_used`, `read_failure`, `t_vomitory`, `exit_id`, `t_exit_queue`,
`abandoned` y `t_safe`, para poder reconstruir colas, utilización, retraso por
conflicto y evacuación solo con `compute_kpis(df, config)`. Las incidencias van
en `df.attrs["incidents"]`.

### D8 · I2 e I3 en `entry.py` (responsable A) — 2026-11-19 · confirmada 2026-11-20
El reparto asigna a B las incidencias I1 e I4. El fallo de lectura (I2) y la
avería de torno (I3) actúan sobre el torno, así que se implementan en `entry.py`.

### D9 · Cambios en configs existentes durante Inc0 — 2026-11-19
* `X0_base.json`: `overrides` con `name: "X0_base"` (antes `{}` y el nombre
  quedaba como `X0`), por coherencia con el resto.
* `base.json`: nueva clave `emergency.blocked_exit_zone = "A"` (la memoria fija
  la salida bloqueada en la macrozona A).

### D10 · Venv fuera del repo si la ruta contiene `:` — 2026-11-19
`python -m venv` rechaza rutas con `:`. El `Makefile` usa entonces
`~/.venvs/modelos-simulacion-ES-estadio` (sobrescribible con `VENV=`).

### D11 · Semillas de réplica — 2026-11-19
`seed = base_seed + réplica` con `base_seed = 20261105` por defecto, igual en
todos los escenarios (`experiments.replica_seed`).

### D12 · Utilización de tornos — 2026-11-20
`turnstile_util = U = (1/cT)∫B dt` como en la memoria (§4.4): `c` es el número
**nominal** de tornos y `T` va desde la apertura hasta el último fin de control.
Los tornos averiados cuentan como disponibles y no ocupados, de modo que las
averías bajan la utilización. `conflict_delay_s` según `docs/CONTRATOS.md`.

### D13 · Puerta cerrada sin redirección — 2026-11-20
Quien llega a una puerta cerrada espera a la reapertura conservando su orden de
llegada (SimPy reanuda en orden de registro a los procesos que esperan un mismo
evento). Cubrir con un test en T2.6/T2.7.

### D14 · Alarma y espectadores en tránsito — 2026-11-20 (hipótesis)
Quien ya ha pasado el torno al sonar la alarma (caminando, en el vomitorio o en
un conflicto de asiento) evacúa con su tiempo de reacción y recorre la distancia
completa a la salida de su macrozona. Quien sigue en cola exterior abandona la
zona y no cuenta. Hay que justificarla en la memoria de la Parte 2.

### D15 · Rendimiento — 2026-11-20
Medir el tiempo de una réplica completa (N = 48.775) ya en Inc2 (T2.1), no solo
en T5.4, para detectar pronto cuellos de botella.

### D16 · `entry_process` espera hasta la llegada; orden de los espectadores — 2026-11-20
* `entry_process(sp, ctx)` hace `timeout` hasta `min_to_s(sp.t_arrival)` si se
  lanza antes. `run_replica` (C) puede lanzar todos los procesos en E0 (t = −90)
  sin calcular retardos.
* `generate_spectators` devuelve la lista **ordenada por `t_arrival`** (`id` crece
  con la llegada). Así, a igual instante de llegada, el orden de lanzamiento
  (por `id`) decide el orden FIFO en el torno.
* ~~Nueva función pública `entry.service_time_s(config, rng)`~~ — sustituida por
  D17 (el servicio se sortea por espectador en `generate_spectators`).

### D17 · Números aleatorios comunes: todo sorteo por espectador, al generarlo — 2026-11-20
**Regla:** cualquier variable aleatoria que pertenezca a un espectador se sortea
en `arrivals.generate_spectators` (vectorizada, N números por flujo) y se guarda
como atributo suyo; los procesos solo la leen. Sortear dentro de los procesos,
con un flujo compartido, asigna los números según el orden en que el modelo
atiende a la gente, que cambia entre escenarios (p. ej. 2 vs 4 tornos), y rompe
los números aleatorios comunes que exige la memoria (§5.3).
* Aplicado: nuevo atributo `Spectator.service_s` (columna del DataFrame),
  `arrivals.sample_service_times`. Se elimina `entry.service_time_s`.
* Pendiente de aplicar en T2.2 (I2): ocurrencia y tiempo extra de la relectura
  (`read_failure_u`, `read_extra_s`); y en T2.5 (I1): ocurrencia del conflicto y
  su duración. I3 e I4 son procesos por recurso, no por espectador: cada uno usa
  su propio flujo.

### D18 · Paso por el vomitorio con números comunes, sorteado en `stadium` — 2026-11-23
El paso por el vomitorio es una variable por espectador, así que D17 obliga a no
sortearla dentro del proceso. Para no tocar `Spectator` ni `arrivals` (rol A),
`stadium.build_stadium_resources` sortea de una vez `n_spectators` tiempos
Triangular(`vomitory_pass_s`) del flujo `"vomitory"` y los guarda en
`StadiumResources.vomitory_pass_s`; el espectador `id` usa la posición `id`.
Como `id` va de 0 a N−1 y no depende del escenario (salvo el perfil de llegadas,
igual que `service_s`), cada espectador recibe el mismo número en todos los
escenarios. No es columna del DataFrame. Si se prefiere un atributo
`Spectator.vomitory_s` como `service_s`, el cambio es local a A y B.

### D19 · Alcance provisional del runner de Inc1 — 2026-11-23
T1.4 encadena entrada y asiento y termina al sentarse el último espectador,
como fija el objetivo de Inc1. La duración máxima de corrida `max_sim_hours`
se mide desde la apertura; al alcanzarla se devuelven todas las filas con NaN
en los sucesos no ocurridos. Se mantienen firmas, columnas y metadatos.
Hasta implementar Inc2/Inc4 se rechazan incidencias o emergencia activas; la
prioridad queda pendiente de T2.4. Así, ejecutar X0 o X7 no produce resultados
que aparenten incluir fases todavía pendientes. La configuración de desarrollo
`configs/dev/i1_mini.json` es un experimento diff con una macrozona, 600
espectadores y todas las incidencias/emergencia desactivadas, compatible con
`load_experiment` y con la futura CLI de T1.6. No añade parámetros al modelo.

### D20 · Semántica de la prioridad en el torno (X3) — 2026-11-23
* Solo actúa con `queue_discipline == "priority"`; con `"fifo"`, `priority_groups`
  se ignora. Con `"priority"` y `priority_groups` vacío equivale a FIFO.
* Niveles SimPy (menor = antes): `PRIORITY_FAILURE` (−1, avería I3) < `PRIORITY_HIGH`
  (0, grupos priorizados) < `PRIORITY_NORMAL` (1). Dentro de un nivel, FIFO.
* No expulsiva: `entry_process` siempre pide con `preempt=False`.
* Consecuencia para los KPIs (C, T2.8): `wait_mean_priority_min` y
  `group_wait_diff_min` se calculan con `config.priority_groups`, no con la
  disciplina.
* Numeración: se fusionó como un segundo D19 (PR #8) cuando el D19 del runner
  (PR #6) ya estaba en `main`; renumerada a D20 el 2026-11-23.

### D21 · I1 con números comunes, sorteado en E0 — 2026-11-23
Igual que D18. `stadium.build_stadium_resources` llama a
`incidents.sample_seat_conflicts`, que sortea del flujo `"seat_conflict"`, para
los `n_spectators`, un `u` ~ Uniforme(0, 1) y una resolución
Triangular(`resolution_min`) en segundos. Se guardan en `StadiumResources`
(`seat_conflict_u`, `seat_conflict_resolution_s`) por `id`. Hay conflicto si
`u < prob`: al pasar de 0,5 % a 1 % el conjunto crece y conserva a los
anteriores, y X5 (3 frente a 6 acomodadores) compara los mismos conflictos.
* El conflicto se detecta **al llegar al asiento**, tras el paso por el
  vomitorio, y el espectador **retiene la plaza** mientras espera al acomodador
  de su macrozona (FIFO) y mientras dura la resolución.
* Incidencia `I1`: `resource` = bloque (`"A-B3"`), `spectator_id`, `t_start` al
  detectarlo y `t_end` al resolverse (incluye la espera al acomodador).
* Sustituye, para I1, la indicación de D17 de sortearlo en `generate_spectators`.
### D22 · Averías de torno (I3): reloj en funcionamiento y generador por torno — 2026-11-23
* **Reloj:** el tiempo entre fallos Exponencial(`mtbf_min`) se mide **en
  funcionamiento**: empieza en la apertura y, tras cada avería, al terminar la
  reparación. Así `mtbf_min` es el tiempo medio de buen funcionamiento (MTBF
  en sentido estricto) y un torno no puede encadenar fallos durante su propia
  reparación. Cada torno hace en promedio `T / (mtbf_min + media(repair_min))`
  averías en un horizonte `T` (≈ T / 246,5 con la base).
* **Cuándo se para:** al vencer ese tiempo el torno se avería, pero termina el
  servicio en curso (memoria §3.2: «cuando el torno queda libre»): la avería
  pide una plaza con `PRIORITY_FAILURE` y `preempt=False` y la reparación
  Uniforme(`repair_min`) cuenta desde que la consigue (`t_start` de la
  incidencia). Como el recurso de la puerta no distingue tornos físicos, «el
  torno k» ocupa la primera plaza que se libera; con c bucles por puerta nunca
  hay más de c averías a la vez.
* **Números aleatorios comunes (D17):** cada torno `(zona, puerta, k)` tiene su
  propio generador, `rngs.substream("turnstile_failure", zona, puerta, k)`, que
  depende solo de la semilla y de esa identidad (`SeedSequence` con
  `spawn_key = (9, …clave codificada)`). Sortea en orden fijo Exp, Unif, Exp,
  Unif… El calendario de sorteos del torno A-G1-T1 es el mismo con 2, 3 o 4
  tornos por puerta (X1) y con otras macrozonas; solo cambia, inevitablemente,
  la espera hasta que el torno queda libre. No se añade ningún flujo a
  `STREAM_NAMES`; el flujo padre `turnstile_failure` no se consume.
* Numeración: D21 está reservado por T2.5 (rama `feat/perez-T2.5-seat-conflict`,
  I1 con números comunes), abierta antes; esta decisión toma D22.

### D23 · Cierre de puerta (I4): a quién afecta y a qué puerta se redirige — 2026-11-23
* **Hipótesis pendiente de confirmar por el grupo.** El cierre afecta solo a
  quien **llega** (E1) mientras dura (memoria §3.2: «nadie entra por esa puerta»,
  «las llegadas se redirigen o esperan»). Quien ya está en la cola o en control
  de esa puerta al cerrarse sigue su curso y los tornos siguen atendiéndolo. Es
  la lectura más simple y literal; la memoria no trata la cola existente.
  * Alternativa (no implementada): parar los tornos de la puerta durante el
    cierre y/o redirigir la cola existente. Sin redirección aumentaría la espera
    de los que estaban en cola (hasta `duration_min` más); con redirección
    trasladaría esa cola a las puertas vecinas. En ambos casos X6 mostraría un
    efecto mayor del cierre y una diferencia mayor entre las dos variantes.
* **Elección al llegar, una vez:** `choose_gate` se evalúa en E1 con el estado
  de ese instante; quien se redirige no vuelve a cambiar de puerta. Sin
  desplazamiento extra (la memoria no modela el exterior).
* **Criterio y desempate:** entre las puertas **abiertas** de la macrozona, la de
  menor `(len(queue), count, nº de puerta)`, determinista y sin azar (el flujo
  `gate_choice` queda sin uso). Un desempate aleatorio habría que sortearlo por
  espectador al generarlo (D17) y cambiaría `Spectator`.
* **Sin alternativa abierta** (p. ej. `gates_per_zone = 1`) o sin redirección: se
  espera a la reapertura (D13), leyendo `reopen_event` en cada vuelta.
* Quien llega exactamente en el instante de reapertura puede encontrarse la
  puerta aún cerrada según el orden de los sucesos simultáneos de SimPy; con
  llegadas continuas tiene probabilidad nula.

### D24. Salida ordinaria: elección de salida y desempate con números comunes (2026-11-23)
* El espectador elige salida **al llegar** a la zona de salidas, tras recorrer
  `distance_m`: la no bloqueada de su macrozona con menos personas (en cola más la
  que está pasando). `t_exit_queue` es ese instante y `t_exit` el final de su paso.
* Desempate entre salidas igual de cargadas: como en D18, `build_exit_resources`
  sortea en E0 `n_spectators` uniformes del flujo `"exit_choice"`
  (`ExitResources.tie_u`, por `id`); entre las `k` empatadas, en orden de
  `exit_id`, se toma la de posición `floor(u * k)`.
* Quien se sienta después de su liberación (E5) sale en cuanto se lanza
  `exit_process`. La política escalonada (`release_time_min`, T3.2) se implementa
  a la vez porque es una línea: grada superior `exit_stagger_min` después.
* Validación (apartado 4.3 de la memoria): 12.195 personas de una macrozona
  tardan 7,7 min en atravesar las 6 salidas (`tests/test_exit.py`).

### D25 · Integración y cálculo de indicadores de Inc2 (T2.8) — 2026-11-23
El runner admite los componentes ya fusionados: prioridad, I1, I3 e I4. I2 y
emergencia siguen rechazadas. El fin sigue dependiendo de los espectadores o
del límite, nunca de que terminen los bucles de avería. La cola se reconstruye
por puerta usada, excluyendo a quienes todavía no han llegado (`gate_used=-1`).
P4 usa los colectivos de `priority_groups` con independencia de la disciplina.
Para operacionalizar el «conflicto activo» de P6 se comprueba solape de intervalos
en el mismo bloque/zona y se excluye al causante; sin población expuesta o de
comparación, NaN. Los contadores siguen la definición literal de filas registradas:
no se aplica un filtro silencioso a I3 tras la entrada; la duda sobre ese filtro
se mantiene en ESTADO. `configs/dev/i2_mini.json` es una comprobación pequeña,
con I2 desactivada y cierre a -30 solo en desarrollo, sin alterar X6 ni la base.

### D26 · I2 con números comunes, sorteado en E0 en `entry` — 2026-11-23
Igual que D18 y D21. `entry.build_entry_resources` llama a
`entry.sample_read_failures`, que sortea del flujo `"read_failure"`, para los
`n_spectators`, un `u` ~ Uniforme(0, 1) y un extra Uniforme(`extra_s`) en
segundos. Se guardan en `EntryResources` (`read_failure_u`,
`read_failure_extra_s`) por `id`, aunque la incidencia esté desactivada. Hay
relectura si está activa y `u < prob`: al pasar de 3 % a 6 % el conjunto crece y
conserva a los anteriores, y cada espectador tiene el mismo extra en todos los
escenarios (también con 2/3/4 tornos y con otro perfil de llegadas).
* La relectura va **justo después del servicio** y **no libera el torno**:
  ocupa `service_s + extra`; ni interrumpe ni se interrumpe.
* Incidencia `I2`: `resource` = puerta usada (`"A-G1"`), `spectator_id`,
  `t_start` al empezar la relectura (`t_start_control + service_s`) y `t_end` =
  `t_end_control`.
* Sustituye, para I2, la indicación de D17 de sortearlo en
  `generate_spectators`. **No cambia el contrato de `Spectator`** ni `arrivals`.
* Numeración: `main` llegaba a D24 y las ramas abiertas reclaman D24 (T5.2) y
  D25 (T2.8 y T4.1); esta toma D26 para no chocar con ninguna.

### D27 · Réplica completa y KPIs de salida ordinaria (T3.3) — 2026-11-23
Se sustituye el fin provisional de D19 por el último espectador fuera. Se crean
los recursos de salida en E0 y se encadenan los procesos de B sin alterar sus
módulos. El límite sigue midiéndose desde apertura y conserva todas las filas.
El tiempo de vaciado de una réplica incompleta es NaN: el último paso observado
no es el vaciado total. La cola por salida incluye a quien está atravesándola,
según D24; sin llegadas se observa cero. Los contadores de incidencias mantienen
D25, incluida la duda documentada sobre averías posteriores a la entrada.

### D28. Evacuación: reparto con el runner, reacción con números comunes y salida bloqueada (2026-11-23)
* **Quién hace qué.** `emergency.alarm_process(ctx, journeys)` cambia el estado
  al sonar la alarma y llama a `interrupt()` en los procesos vivos de
  `journeys` (`journeys[i]` es el del espectador `id == i`). El proceso de cada
  espectador (runner, T4.3) captura `simpy.Interrupt` y sigue con
  `yield from evacuation_process(sp, ctx)`. Al interrumpir dentro de un `with
  recurso.request()`, SimPy libera el torno, el vomitorio o el acomodador.
* **Qué le toca a cada uno** (`status_at_alarm`, desarrolla D14): si aún no ha
  llegado, nada (ya no llega). Si ha llegado y no ha terminado el control (en
  cola, esperando reapertura o pasando el torno), abandona (`abandoned = True`).
  Si ya pasó el torno (caminando, en el vomitorio, en un conflicto o sentado),
  evacúa: reacción, la distancia `distance_m` completa a `speed_mps` por
  `speed_factor`, la salida no bloqueada con menos cola y el paso de evacuación.
* **Reacción con números comunes.** Al sonar la alarma se sortean de una vez
  los `n_spectators` tiempos de reacción del flujo `"reaction"` y se guardan en
  `ExitResources.reaction_s` por `id`, como en D18.
* **Salidas.** El paso de todas las salidas pasa a ser el de una anchura
  `exit_width_m` por `exit_width_factor` (unos 0,17 s por persona). Con
  `blocked_exit` se inutiliza la salida 1 de `blocked_exit_zone`: la memoria dice
  "una salida de la macrozona A" sin decir cuál, y con salidas iguales da lo mismo.
* Al sonar la alarma se cierran todas las puertas de acceso y `ctx.phase` pasa
  a `"evacuation"`. Un conflicto I1 en curso se da por terminado en `alarm_min`.
* Validación (apartado 4.3 de la memoria): 12.195 personas de una macrozona
  tardan 5,9 min en atravesar las 6 salidas ensanchadas y 7,1 min con una
  bloqueada (`tests/test_emergency.py`).

### D29 · Salidas estadísticas y muestras incompletas (T5.2) — 2026-11-23
El análisis usa una observación por réplica, como exige §5.3 de la memoria.
Los resúmenes son tablas anchas con media, semianchura del IC t-Student y n
válido por KPI (`<nombre>_mean`, `<nombre>_halfwidth`, `<nombre>_n`). Se mantiene
una fila por escenario y, en las comparaciones, se añade `baseline` y se excluye
la fila del base. La diferencia es escenario − base, emparejada por `seed`.
Se rechazan semillas duplicadas por escenario para no contarlas como réplicas
independientes. NaN no equivale a cero: sin datos no hay estimación, y con una
sola réplica no hay IC estimable. El tamaño definitivo se estima con el t y la
desviación del piloto, redondeando arriba y sin bajar del piloto ya ejecutado.
Se debe comprobar el IC de nuevo al añadir réplicas. Una media cero con
variabilidad exige un objetivo absoluto, no se inventa una precisión relativa.
Son convenciones de salida de T5.2; no cambia ningún parámetro de la simulación.

### D30 · Integración completa de alarma y KPIs (T4.3) — 2026-11-23
El proceso único por espectador captura la interrupción y continúa con la
clasificación/evacuación de B (D28). Se lanza la alarma tras crear todos los
recorridos. El fin sigue siendo todos los recorridos terminados o el límite;
no se espera a los bucles de avería. I2 se admite usando el módulo de A (D26).
Se añaden metadatos `stop_time_min` y `alarm_triggered` para distinguir una
réplica truncada antes de la alarma o durante la evacuación.
`evac_time_min` solo se conoce si todos los de dentro al sonar la alarma tienen
`t_safe`. El denominador de `evac_pct_ref` son todos los de dentro al sonar la
alarma (control terminado y sin salida ordinaria previa), no solo los que ya
están seguros. Se calcula si la evacuación terminó o se observó el horizonte de
referencia; antes, NaN. Sin evacuables, ambos KPIs son NaN. `n_abandoned` cuenta
los marcados, cero si no hay; sin emergencia permanece NaN. Si sonó la alarma,
los KPIs P5 ordinarios no aplican y quedan NaN.
La doble D25 surgida de trabajo paralelo se desambigua: D25 = Inc2 (T2.8),
D28 = evacuación de B. Las referencias de documentación en sus módulos se
actualizan sin cambiar su implementación. D29 queda para estadística (PR #17).

### D31 · Instante del cierre de puerta en X6 — 2026-11-23 · **pendiente de confirmar por el grupo**
**Propuesta:** `incidents.gate_closure.start_min = −30` (hoy +20), con
`duration_min = 10` y la misma puerta (A-1). Estudio en `docs/ESTUDIO_X6.md`
(5 réplicas por celda, semillas comunes).
* **Motivo:** P7 pregunta por un «cierre en hora punta». A +20 llega el 2 % del
  público y X6 no distingue las variantes: la diferencia sin − con redirección en
  la espera media de A-1 es de 4 ± 1 s. A −30, comienzo de la franja de máximas
  llegadas (−30 a 0), es de 292 ± 24 s y la entrada tardía sube 0,67 ± 0,11 p. p.
  sin redirección; es el máximo de los instantes probados (−45, −30, −20, −10, 0,
  +20). Además, a −30 no hay cola formada al cerrar, así que la hipótesis D23 no
  influye.
* **Alternativas:** −20 (194 ± 6 s; hasta ≈ 100 personas en cola al cerrar en
  algunas semillas, sensible a D23); −30 con 20 min (escenario de estrés: 636 ± 25
  s, 59 % de A-1 con más de 10 min); mantener +20 y reformular P7 como cierre fuera
  de punta.
* **Si se confirma:** cambiar `configs/base.json` (y sus tests de config) en un
  commit aparte; los `X6_*.json` heredan el valor de la base.

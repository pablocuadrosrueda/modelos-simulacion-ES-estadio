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

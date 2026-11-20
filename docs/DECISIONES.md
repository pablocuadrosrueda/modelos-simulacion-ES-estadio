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
* Nueva función pública `entry.service_time_s(config, rng)` (Triangular del
  servicio; admite low == high para tests deterministas). Es una adición: no
  cambia ninguna firma existente.

# Estado del proyecto

_Última actualización: 2026-11-23 · `main` contiene Inc0; Inc1 en curso._

## Hecho

**Inc0 · Esqueleto — completado.**

* Tooling: `pyproject.toml` (paquete `sanmames` en `src/`), `Makefile`
  (`install`, `test`, `lint`, `format`, `run`), ruff y pytest.
* Configuración: `configs/base.json` + experimentos X0–X7 y S1 como diff.
  `config.py` (carga, fusión profunda, validación estricta) **implementado**.
* Azar: `rng.py` (`RngStreams`, un generador por fuente) **implementado**.
* Contratos: `entities.py` (`Spectator`, `Incident`, columnas), `metrics.KPI_COLUMNS`,
  `runner.SimContext` y stubs con docstring en el resto de módulos.
  Documentados en `docs/CONTRATOS.md`.
* Tests: `test_config`, `test_rng`, `test_experiments_cli` pasan;
  `test_conservacion` y `test_orden_temporal` son esqueletos `xfail` estrictos.
* Docs: `AGENTS.md`, `docs/ESPECIFICACION.md`, `docs/TAREAS.md`, este fichero,
  `docs/DECISIONES.md`, `README.md`.

Aún **no hay lógica de simulación**: `run_replica` y los procesos lanzan
`NotImplementedError`.

**Inc1 · en curso.**

* T1.1 (A, en revisión): `arrivals.py` implementado. Franja por perfil + instante
  uniforme; zona/puerta/bloque, grupo, velocidad (normal truncada por inversión
  de la FDA, consume exactamente N uniformes) y distancia, cada uno de su flujo y
  vectorizados. Los espectadores salen **ordenados por llegada** (`id` crece con
  `t_arrival`); los atributos no dependen del perfil (NRC en X2).
  Tests en `tests/test_arrivals.py` (chi-cuadrado α = 0,001).
* T1.2 (A, en revisión; rama sobre la de T1.1): `entry.py` con
  `build_entry_resources` (un `PriorityResource` por puerta), `priority_of`
  (FIFO; `"priority"` lanza `NotImplementedError` hasta T2.4) y `entry_process`
  sin incidencias por `spectator.gate`. `entry_process` espera hasta `t_arrival`
  (D16). El servicio en torno es un atributo del espectador (`service_s`,
  D17: números aleatorios comunes). Tests en `tests/test_entry.py`: orden FIFO,
  capacidad de tornos, independencia de puertas, determinismo y servicio
  idéntico con 2 y 4 tornos.

* T1.3 (B, hecho; PR #4): `stadium.py` con `build_stadium_resources` (un
  `Resource` FIFO de `vomitory_capacity` plazas por `(zona, bloque)` y uno de
  `stewards_per_zone` acomodadores por zona), `seating_process` sin conflictos
  (espera a `t_end_control`, camina `distance_m / speed_mps`, cola y paso por el
  vomitorio, se sienta) e `is_late`. Tiempos de paso con números comunes (D18).
  Tests en `tests/test_stadium.py`: capacidad de 8 plazas y oleadas FIFO,
  independencia de vomitorios, orden `t_end_control ≤ t_vomitory ≤ t_seated`
  con entrada + asiento encadenados, `is_late` y determinismo. Los stubs de
  `exit.py` y `emergency.py` ya existían desde Inc0 con docstring y firma; no
  hubo que cambiarlos.

* T2.6 (B, en revisión; adelantada mientras se cierra Inc1): en `incidents.py`,
  `log_incident` y `gate_closure_process` (I4). Si está activa, cierra la puerta
  en `start_min`, registra una incidencia `I4` (`resource = "A-G1"`), la reabre
  tras `duration_min` y dispara `reopen_event`, que se sustituye por uno nuevo.
  Tests en `tests/test_incidents.py`: apertura y cierre a su hora, solo la puerta
  afectada, incidencia con `t_start`/`t_end`, reanudación en orden (D13), duración
  cero, desactivada y `start_min` ya pasado.

## Siguiente paso

**Inc1 · rebanada vertical** (ver `docs/TAREAS.md`): una macrozona, entrada sin
incidencias, CSV y KPIs de espera. En paralelo:

* A: T1.1 → T1.2
* B: T1.3
* C: T1.5 (no depende de nada más que del contrato), luego T1.4 → T1.6 → T1.7

## Reparto

| Rol | Módulos | Integrante | Sesión de agente |
|---|---|---|---|
| A | config, rng, entities, arrivals, entry | Pablo Cuadros | Claude Code |
| B | stadium, exit, emergency, incidents (I1, I4) | Pablo Pérez | Claude Code |
| C | metrics, runner, analysis, experiments, tests | Chema | Codex |

## Dudas abiertas

Ninguna pendiente.

Resueltas el 2026-11-20 (ver `docs/DECISIONES.md`): reparto de roles A/B/C (arriba), I2/I3 en `entry.py` (D8),
utilización de tornos (D12), puerta cerrada sin redirección (D13), evacuación de
quien está en tránsito (D14, hipótesis) y medición temprana de rendimiento (D15).
Probado con Python 3.13.2 (rama T2.6): 122 tests pasan, 5 xfail esperados, ruff limpio.

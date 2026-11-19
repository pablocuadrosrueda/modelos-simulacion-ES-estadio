# Estado del proyecto

_Última actualización: 2026-11-19 · rama `feat/i0-esqueleto`._

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

## Siguiente paso

**Inc1 · rebanada vertical** (ver `docs/TAREAS.md`): una macrozona, entrada sin
incidencias, CSV y KPIs de espera. En paralelo:

* A: T1.1 → T1.2
* B: T1.3
* C: T1.5 (no depende de nada más que del contrato), luego T1.4 → T1.6 → T1.7

## Reparto

| Rol | Módulos | Integrante | Sesión de agente |
|---|---|---|---|
| A | config, rng, entities, arrivals, entry | _por asignar_ | _por asignar_ |
| B | stadium, exit, emergency, incidents (I1, I4) | _por asignar_ | _por asignar_ |
| C | metrics, runner, analysis, experiments, tests | _por asignar_ | _por asignar_ |

## Dudas abiertas

1. **Asignación de personas a roles A/B/C** y de cada sesión de agente (2 Claude
   Code + 1 Codex).
2. **I2 e I3** (fallo de lectura y avería de torno) se han asignado a A dentro de
   `entry.py`, porque el reparto solo da I1 e I4 a B. Confirmar.
3. **Definición fina de KPIs** que la memoria deja abierta: denominador de la
   utilización de tornos (desde la apertura hasta el último control) y cálculo de
   `conflict_delay_s`. Propuesta en `docs/CONTRATOS.md`; decide C en T1.5/T2.8.
4. **Espectadores que llegan con la puerta cerrada y sin redirección**: esperan a
   la reapertura fuera de la cola o dentro de ella. La memoria dice «espera a que
   reabra»; se propone que mantengan su orden de llegada.
5. **Evacuación y quien está en tránsito o en el vomitorio** al sonar la alarma
   (no solo los sentados): la memoria solo detalla sentados y colas exteriores.
   Propuesta: todo el que ha pasado el torno evacua desde su posición.
6. **Rendimiento**: 48.775 procesos SimPy × ≈ 400 ejecuciones; medir en T5.4.

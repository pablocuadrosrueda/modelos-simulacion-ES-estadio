# Estado del proyecto

_Última actualización: 2026-11-20 · `main` contiene Inc0._

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
   Code + 1 Codex). Rellenar la tabla de arriba.

Resueltas el 2026-11-20 (ver `docs/DECISIONES.md`): I2/I3 en `entry.py` (D8),
utilización de tornos (D12), puerta cerrada sin redirección (D13), evacuación de
quien está en tránsito (D14, hipótesis) y medición temprana de rendimiento (D15).
Probado con Python 3.10.12: 68 tests pasan, 5 xfail esperados, ruff limpio.

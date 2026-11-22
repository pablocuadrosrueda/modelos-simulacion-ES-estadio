# Estado del proyecto

_Última actualización: 2026-11-22 · `main` contiene Inc0 y T1.1/T1.2;
T1.5 revisada localmente, pendiente de publicar, en `feat/chema-T1.5-metrics`._

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

Hay generación de espectadores y entrada sin incidencias. Aún no se puede
ejecutar una réplica completa: `run_replica` y los procesos de asiento, salida
y emergencia siguen pendientes.

**Inc1 · en curso.**

* T1.1 (A, hecho; PR #1 fusionado): `arrivals.py` implementado. Franja por perfil + instante
  uniforme; zona/puerta/bloque, grupo, velocidad (normal truncada por inversión
  de la FDA, consume exactamente N uniformes) y distancia, cada uno de su flujo y
  vectorizados. Los espectadores salen **ordenados por llegada** (`id` crece con
  `t_arrival`); los atributos no dependen del perfil (NRC en X2).
  Tests en `tests/test_arrivals.py` (chi-cuadrado α = 0,001).
* T1.2 (A, hecho; PR #2 fusionado): `entry.py` con
  `build_entry_resources` (un `PriorityResource` por puerta), `priority_of`
  (FIFO; `"priority"` lanza `NotImplementedError` hasta T2.4) y `entry_process`
  sin incidencias por `spectator.gate`. `entry_process` espera hasta `t_arrival`
  (D16). El servicio en torno es un atributo del espectador (`service_s`,
  D17: números aleatorios comunes). Tests en `tests/test_entry.py`: orden FIFO,
  capacidad de tornos, independencia de puertas, determinismo y servicio
  idéntico con 2 y 4 tornos.
* T1.5 (C, en curso; revisada localmente, rama `feat/chema-T1.5-metrics`): `queue_length_max` reconstruye
  intervalos `[llegada, inicio_control)`, sin contar esperas nulas ni sumar
  personas de puertas distintas. Un fin NaN indica que sigue esperando.
  `compute_kpis` calcula recuentos, espera media/P95, porcentaje de espera
  menor de 10 min, cola máxima por puerta, utilización nominal desde apertura
  (D12), acceso medio y porcentaje de entrada tardía. Los demás KPIs quedan
  en NaN. Las esperas y accesos pendientes no se sustituyen por ceros; el
  denominador de `late_pct` sigue siendo todos los que llegan antes del inicio,
  como fija el contrato. Tests con datos sintéticos en `tests/test_metrics.py`.
  No cambia firmas, columnas, parámetros ni flujos aleatorios.

## Siguiente paso

**Inc1 · rebanada vertical** (ver `docs/TAREAS.md`): una macrozona, entrada sin
incidencias, CSV y KPIs de espera. En paralelo:

* A: T1.1 y T1.2 ya fusionadas; continuar con sus tareas de Inc2 según dependencias.
* B: T1.3 (pendiente según el tablero).
* C: publicar T1.5 y abrir PR para revisión del equipo; después T1.4 → T1.6 → T1.7.
  T1.4 necesita T1.3; las métricas se prueban sin esperar al módulo de asiento.
  Commit y push autorizados por Chema. Publicación pendiente: Git por HTTPS no
  tiene credenciales locales y la conexión UJA (`jmcb0024`) devuelve HTTP 403
  al intentar escribir en el repositorio. No se ha creado rama remota ni PR.

### Revisión local del rol C

Por petición de Chema, preparar código, tests y documentación **sin commit**.
Antes de implementar, describir el objetivo de la tarea, qué se va a cambiar,
qué queda fuera de su alcance y sus dependencias. Al terminar, explicar los
cambios y proporcionar comandos completos para probarlos, incluida la ruta del
clon. Indicar también las siguientes tareas, cuáles pueden empezar y cuáles
dependen de trabajo pendiente de los compañeros. Incorporar sus correcciones.
Hacer el commit cuando lo indique. La publicación de la rama y el PR se tratan
después.

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
Base del clon verificada el 2026-11-22 con Python 3.12.14: 99 tests pasan,
5 xfail esperados, ruff limpio. Con T1.5: `make test` da 122 tests correctos
(23 nuevos de métricas) y 5 xfail esperados; `make lint` y `git diff --check`
limpios. Para revisar solo esta tarea: `.venv/bin/python -m pytest
tests/test_metrics.py -v` desde la raíz del clon.

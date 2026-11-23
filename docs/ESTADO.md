# Estado del proyecto

_Última actualización: 2026-11-23 · `main` contiene Inc0, T1.1, T1.2, T1.3 y T1.5; Inc1 en curso._
_Última actualización: 2026-11-23 · `main` contiene Inc0, T1.1, T1.2, T1.3 y T1.5;
T2.6 en revisión en la rama `feat/perez-T2.6-gate-closure`._
_Última actualización: 2026-11-23 · `main` contiene Inc0 y T1.1/T1.2/T1.3/T1.5;
T1.4 publicada y en revisión en el PR #6, rama `feat/chema-T1.4-runner`._

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
* Tests base: configuración, azar, llegadas, entrada y estadio. En la rama
  T1.4 se activan las comprobaciones de entrada, reproducibilidad y conservación;
  las de salida siguen con `xfail` estricto hasta T3.3/T3.4.
* Docs: `AGENTS.md`, `docs/ESPECIFICACION.md`, `docs/TAREAS.md`, este fichero,
  `docs/DECISIONES.md`, `README.md`.

En `main` hay llegadas, entrada y ubicación implementadas. En la rama T1.4
el runner conecta esos módulos hasta sentarse todos o alcanzar el tiempo
máximo. Permanencia, salida, incidencias y emergencia siguen pendientes.

**Automatización (T0.5) — hecha.** CI de GitHub Actions (`ruff` + `pytest` en Python
3.10 y 3.12, y un job que exige actualizar `ESTADO`/`TAREAS` con código y
`AVISOS`/`DECISIONES` con contratos: `scripts/check_pr_docs.py`), plantilla de PR,
`make check`, `make hooks` (pre-push) y `make docs-check`. Pendiente fuera del
repo: activar la protección de `main` exigiendo esos checks.

**Inc1 · en curso.**

* T1.1 (A, hecho; PR #1 fusionado): `arrivals.py` implementado. Franja por perfil + instante
  uniforme; zona/puerta/bloque, grupo, velocidad (normal truncada por inversión
  de la FDA, consume exactamente N uniformes) y distancia, cada uno de su flujo y
  vectorizados. Los espectadores salen **ordenados por llegada** (`id` crece con
  `t_arrival`); los atributos no dependen del perfil (NRC en X2).
  Tests en `tests/test_arrivals.py` (chi-cuadrado α = 0,001).
* T1.2 (A, hecho; PR #2 fusionado): `entry.py` con
  `build_entry_resources` (un `PriorityResource` por puerta), `priority_of`
  (FIFO o prioridad, ver T2.4) y `entry_process`
  sin incidencias por `spectator.gate`. `entry_process` espera hasta `t_arrival`
  (D16). El servicio en torno es un atributo del espectador (`service_s`,
  D17: números aleatorios comunes). Tests en `tests/test_entry.py`: orden FIFO,
  capacidad de tornos, independencia de puertas, determinismo y servicio
  idéntico con 2 y 4 tornos.
* T1.5 (C, hecho; PR #3 fusionado): `queue_length_max` reconstruye
  intervalos `[llegada, inicio_control)`, sin contar esperas nulas ni sumar
  personas de puertas distintas. Un fin NaN indica que sigue esperando.
  `compute_kpis` calcula recuentos, espera media/P95, porcentaje de espera
  menor de 10 min, cola máxima por puerta, utilización nominal desde apertura
  (D12), acceso medio y porcentaje de entrada tardía. Los demás KPIs quedan
  en NaN. Las esperas y accesos pendientes no se sustituyen por ceros; el
  denominador de `late_pct` sigue siendo todos los que llegan antes del inicio,
  como fija el contrato. Tests con datos sintéticos en `tests/test_metrics.py`.
  No cambia firmas, columnas, parámetros ni flujos aleatorios.

* T1.3 (B, hecho; PR #4): `stadium.py` con `build_stadium_resources` (un

* T1.3 (B, hecho; PR #4 fusionado): `stadium.py` con `build_stadium_resources` (un
  `Resource` FIFO de `vomitory_capacity` plazas por `(zona, bloque)` y uno de
  `stewards_per_zone` acomodadores por zona), `seating_process` sin conflictos
  (espera a `t_end_control`, camina `distance_m / speed_mps`, cola y paso por el
  vomitorio, se sienta) e `is_late`. Tiempos de paso con números comunes (D18).
  Tests en `tests/test_stadium.py`: capacidad de 8 plazas y oleadas FIFO,
  independencia de vomitorios, orden `t_end_control ≤ t_vomitory ≤ t_seated`
  con entrada + asiento encadenados, `is_late` y determinismo. Los stubs de
  `exit.py` y `emergency.py` ya existían desde Inc0 con docstring y firma; no
  hubo que cambiarlos.

**Inc2 · en curso.**

* T2.4 (A, en revisión; rama `feat/cuadros-T2.4-priority`, apilada sobre T1.2):
  `priority_of` con `queue_discipline == "priority"`: los grupos de
  `priority_groups` piden con `PRIORITY_HIGH` y adelantan a los normales en cola;
  no expulsiva (`preempt=False`, un control iniciado no se interrumpe) y FIFO dentro
  de cada nivel (D19). Tests en `tests/test_entry.py`, incluido un escenario exacto
  a mano y la comprobación, con la misma semilla, de que X3 baja la espera de
  mayores y PMR y no la del resto.
* T2.6 (B, en revisión; adelantada mientras se cierra Inc1): en `incidents.py`,
  `log_incident` y `gate_closure_process` (I4). Si está activa, cierra la puerta
  en `start_min`, registra una incidencia `I4` (`resource = "A-G1"`), la reabre
  tras `duration_min` y dispara `reopen_event`, que se sustituye por uno nuevo.
  Tests en `tests/test_incidents.py`: apertura y cierre a su hora, solo la puerta
  afectada, incidencia con `t_start`/`t_end`, reanudación en orden (D13), duración
  cero, desactivada y `start_min` ya pasado.
* T1.4 (C, en revisión; PR #6, rama `feat/chema-T1.4-runner`): `run_replica` crea el entorno
  en la apertura, flujos de azar y recursos de entrada y estadio; genera el
  público y lanza un proceso por espectador, entrada → asiento. Devuelve todas
  las columnas de `SPECTATOR_COLUMNS`, metadatos `seed`, `scenario` e incidencias
  vacías con su esquema. Config de desarrollo `configs/dev/i1_mini.json`
  (experimento diff de una macrozona, 600 personas, FIFO, sin incidencias).
  El alcance provisional y el límite desde apertura están en D19/CONTRATOS.
  Tests de integración en `tests/test_runner.py`, incluidos cálculo de tiempos
  de un espectador, FIFO, fin al sentarse el último, límite con sucesos pendientes,
  varias zonas y rechazo de opciones todavía pendientes. Se retiran los `xfail`
  que T1.4 hace pasar; el orden temporal admite tolerancia de 1e-9 min (aviso B).
* T1.5 (C, hecho): métricas fusionadas en el
  [PR #3](https://github.com/pablocuadrosrueda/modelos-simulacion-ES-estadio/pull/3),
  incorporadas a esta rama al actualizar con `main`. Calcula recuentos,
  esperas media/P95, porcentaje de espera menor de 10 min, cola máxima por
  puerta, utilización nominal (D12), acceso medio y entrada tardía. Los demás
  indicadores quedan en NaN; 23 pruebas sintéticas en `tests/test_metrics.py`.

## Siguiente paso

**Inc1 · rebanada vertical** (ver `docs/TAREAS.md`): una macrozona, entrada sin
incidencias, CSV y KPIs de espera. En paralelo:

* A: T1.1 y T1.2 ya fusionadas; continuar con sus tareas de Inc2 según dependencias.
* B: T1.3 fusionada (PR #4); T2.6 en revisión. Después T2.5 (I1), cuando T1.4 esté en `main`.
* C: revisión del equipo y merge de [T1.5, PR #3](https://github.com/pablocuadrosrueda/modelos-simulacion-ES-estadio/pull/3);
  después T1.4 → T1.6 → T1.7.
  T1.4 necesita T1.3; las métricas se prueban sin esperar al módulo de asiento.
  Autenticación local de Git resuelta con GitHub CLI y cuenta `jmcb0024`.
  Rama publicada y PR abierto; todavía no fusionado en `main`.
* A y B: T1.1/T1.2/T1.3 ya fusionadas; continuar sus tareas según dependencias.
* C: revisión de T1.4 en el [PR #6](https://github.com/pablocuadrosrueda/modelos-simulacion-ES-estadio/pull/6). T1.5 ya fusionada (PR #3).
  T1.6 necesita ambos módulos: runner y métricas. T1.7 necesita
  T1.4; las pruebas existentes ya activadas no sustituyen su caso límite de
  muchos tornos ni el refuerzo de conservación. No hay que esperar otro módulo
  de A/B para completar Inc1 una vez se integren T1.4 y T1.5.

### Revisión local del rol C

Por petición de Chema, antes de implementar describir el objetivo, los cambios
previstos y las dependencias de la tarea. Preparar código, tests y documentación
**sin commit**. Al terminar, explicar los cambios, facilitar comandos completos
para probarlos (con la ruta del clon) e indicar qué tareas quedan y sus
dependencias. Incorporar sus correcciones y hacer el commit cuando lo indique.
La publicación y el PR se tratan después.

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
Probado con Python 3.13.2 (rama T2.6, con T1.5 integrada): 145 tests pasan, 5 xfail esperados, ruff limpio.
Probado con Python 3.13.2 (rama T1.3): 114 tests pasan, 5 xfail esperados, ruff limpio.
Verificación local de T1.4 con Python 3.12.14: `make test` da 134 tests correctos
y 2 xfail esperados (salida pendiente); `make lint` y `git diff --check` limpios.
Prueba manual de `i1_mini`, semilla 20261105: 600 filas, 600 sentados, último
asiento en t = +31,907 min. Para las pruebas de esta tarea, desde la raíz del
clon: `.venv/bin/python -m pytest tests/test_runner.py tests/test_orden_temporal.py
tests/test_conservacion.py -v`. `make run` queda pendiente de T1.6.

Tras integrar main con T1.5: 157 tests correctos y 2 xfail esperados, lint limpio.

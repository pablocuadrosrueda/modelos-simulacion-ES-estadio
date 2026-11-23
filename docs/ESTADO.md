# Estado del proyecto

_Última actualización: 2026-11-23 · `main` contiene Inc0, Inc1 salvo T1.6/T1.7
(T1.1–T1.5) y, de Inc2, T2.4 y T2.6._

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
* Tests base: configuración, azar, llegadas, entrada y estadio. Con T1.4 se
  activaron las comprobaciones de entrada, reproducibilidad y conservación;
  las de salida siguen con `xfail` estricto hasta T3.3/T3.4.
* Docs: `AGENTS.md`, `docs/ESPECIFICACION.md`, `docs/TAREAS.md`, este fichero,
  `docs/DECISIONES.md`, `README.md`.

En `main` hay llegadas, entrada (FIFO y prioridad X3) y ubicación implementadas,
y el runner las conecta hasta sentarse todos o alcanzar el tiempo máximo. I4
está implementada en `incidents.py`, pero el runner aún no la lanza.
Permanencia, salida, I1–I3 y emergencia siguen pendientes.

**Automatización (T0.5) — hecha.** CI de GitHub Actions (`ruff` + `pytest` en Python
3.10 y 3.12, y un job que exige actualizar `ESTADO`/`TAREAS` con código y
`AVISOS`/`DECISIONES` con contratos: `scripts/check_pr_docs.py`), plantilla de PR,
`make check`, `make hooks` (pre-push) y `make docs-check`. Pendiente fuera del
repo: activar la protección de `main` exigiendo esos checks.

**Inc1 · rebanada vertical — falta T1.6 y T1.7.**

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
* T1.4 (C, hecho; PR #6 fusionado): `run_replica` crea el entorno
  en la apertura, flujos de azar y recursos de entrada y estadio; genera el
  público y lanza un proceso por espectador, entrada → asiento. Devuelve todas
  las columnas de `SPECTATOR_COLUMNS`, metadatos `seed`, `scenario` e incidencias
  vacías con su esquema. Config de desarrollo `configs/dev/i1_mini.json`
  (experimento diff de una macrozona, 600 personas, FIFO, sin incidencias).
  El alcance provisional y el límite desde apertura están en D19/CONTRATOS;
  mientras no se actualice, rechaza `queue_discipline = "priority"` (ver AVISOS).
  Tests de integración en `tests/test_runner.py`, incluidos cálculo de tiempos
  de un espectador, FIFO, fin al sentarse el último, límite con sucesos pendientes,
  varias zonas y rechazo de opciones todavía pendientes. Se retiran los `xfail`
  que T1.4 hace pasar; el orden temporal admite tolerancia de 1e-9 min (aviso B).
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

**Inc2 · en curso** (T2.4 y T2.6 hechas).

* T2.4 (A, hecho; PR #8 fusionado):
  `priority_of` con `queue_discipline == "priority"`: los grupos de
  `priority_groups` piden con `PRIORITY_HIGH` y adelantan a los normales en cola;
  no expulsiva (`preempt=False`, un control iniciado no se interrumpe) y FIFO dentro
  de cada nivel (D20). Tests en `tests/test_entry.py`, incluido un escenario exacto
  a mano y la comprobación, con la misma semilla, de que X3 baja la espera de
  mayores y PMR y no la del resto.
* T2.6 (B, hecho; PR #5 fusionado): en `incidents.py`,
  `log_incident` y `gate_closure_process` (I4). Si está activa, cierra la puerta
  en `start_min`, registra una incidencia `I4` (`resource = "A-G1"`), la reabre
  tras `duration_min` y dispara `reopen_event`, que se sustituye por uno nuevo.
  Tests en `tests/test_incidents.py`: apertura y cierre a su hora, solo la puerta
  afectada, incidencia con `t_start`/`t_end`, reanudación en orden (D13), duración
  cero, desactivada y `start_min` ya pasado.
* T2.5 (B, en revisión; rama `feat/perez-T2.5-seat-conflict`): I1 en
  `incidents.py` (`sample_seat_conflicts`, `has_seat_conflict`, `seat_conflict`)
  e integrado en `seating_process`: al llegar al asiento, con `u < prob`, el
  espectador retiene la plaza del vomitorio, espera a un acomodador de su zona y
  resuelve en Triangular(1, 3, 10) min. Ocurrencia y duración sorteadas en E0 por
  `id` (D21, números comunes). Tests en `tests/test_seat_conflict.py`: reparto,
  números comunes entre escenarios, 0,5 % ⊂ 1 %, plaza retenida, límite de
  acomodadores por zona e integración entrada + asiento. El runner aún rechaza
  incidencias activas (D19).

## Siguiente paso

**Cerrar Inc1** (`make run EXP=<mini> REPS=3` con CSV de KPIs) y seguir con Inc2
según dependencias (ver `docs/TAREAS.md`):

* A: T2.1 (cuatro macrozonas y medida de tiempo, D15), T2.3 (I3). T2.2 (I2)
  necesita `log_incident`, ya en `main`; T2.7 (redirección) necesita T2.6, ya en
  `main`.
* B: T2.5 en revisión; después T3.1 (salida ordinaria).
* C: T1.6 (CLI y CSV) → T1.7. Pendiente de C en el runner: admitir
  `queue_discipline = "priority"` (T2.4 ya en `main`) y lanzar
  `gate_closure_process` en E0 (T2.6 ya en `main`); ver `docs/AVISOS.md`.

### Revisión local del rol C

Por petición de Chema, antes de implementar describir el objetivo, los cambios
previstos y las dependencias de la tarea. Preparar código, tests y documentación
**sin commit**. Al terminar, explicar los cambios, facilitar comandos completos
para probarlos (con la ruta del clon) e indicar qué tareas quedan y sus
dependencias. Incorporar sus correcciones y hacer el commit cuando lo indique.
La publicación y el PR se tratan después.
_Última actualización: 2026-11-23 · main verificado en `2c8740e`.
T1.6 publicada en el PR #9 en `feat/chema-T1.6-experiments`._

## Hecho

**Inc0 · completado.** Paquete `sanmames`, configuración validada, flujos de azar,
entidades e interfaces compartidas. CI, plantilla de PR y comprobación documental
fusionadas en el PR #7. `make check`, `make hooks` y `make docs-check` disponibles.

**Inc1 · implementación principal fusionada; cierre en revisión local.**

* T1.1 y T1.2 (A, hechas; PR #1 y #2): generación de espectadores ordenados por
  llegada y entrada FIFO, con servicio sorteado por espectador (D16/D17).
* T1.3 (B, hecha; PR #4): recursos de vomitorio y acomodadores, desplazamiento y
  asiento sin conflictos. Paso por vomitorio sorteado por id en E0 (D18).
* T1.4 (C, hecha; PR #6): runner de llegada → entrada → asiento, hasta sentarse
  todos o alcanzar `max_sim_hours` desde apertura. Tabla completa y metadatos.
  `configs/dev/i1_mini.json`: 600 espectadores, zona A, sin incidencias.
  Permanencia, salida e incidencias siguen pendientes de integración.
* T1.5 (C, hecha; PR #3): KPIs de entrada y cola máxima por puerta. Utilización
  nominal desde apertura (D12); métricas de fases futuras en NaN.
* T1.6 (C, en revisión): réplicas con semillas comunes entre variantes,
  tabla con columnas acordadas y CLI que acepta nombres o rutas de experimento
  y guarda `results/<fichero>_kpis.csv`. En `feat/chema-T1.6-experiments`, carpeta
  `modelos-simulacion-ES-estadio`. Incluye corrección numérica en métricas para
  esperas nulas con errores de redondeo s/min (tolerancia 1e-9 min), con tests.
* T1.7 (C, en revisión): siete pruebas nuevas de conservación en cada
  transición, cola pendiente al alcanzar el límite y muchos tornos frente a una
  puerta saturada con las mismas llegadas/servicios. En
  `feat/chema-T1.7-verificacion`, carpeta `modelos-simulacion-ES-estadio-T1.7`.
  Orden temporal y conservación existentes activos; dos xfail de salida pendientes.

**Inc2 · componentes adelantados, ya fusionados.**

* T2.4 (A, hecha; PR #8): prioridad no expulsiva por `priority_groups`, FIFO
  dentro de cada nivel y comparación de grupos con semillas comunes. D19 de A.
* T2.6 (B, hecha; PR #5): `log_incident` y cierre/reapertura de puerta, registro
  I4 y sustitución de `reopen_event`. Requiere integración con la elección de
  puerta T2.7 (A) y el runner; Inc1 todavía rechaza incidencias activadas.

## Siguiente paso

* C: publicar T1.6 y T1.7 en PR separados, autorizado por Chema. Ambas
  actualizadas con main; Inc1 termina al fusionarse las dos. Continuar T5.2
  (estadística con datos sintéticos), sin depender de otros módulos.
* Después, T2.8 (KPIs de grupos y conflictos) requiere T2.4, ya fusionada, y T2.5
  de B, pendiente. T3.3 (integrar salida) requiere T3.1 de B, pendiente.
* A: puede continuar T2.7 usando T2.6 ya fusionada; B puede avanzar T2.5/T3.1
  según el tablero. El módulo de prioridad está implementado, pero el alcance
  provisional del runner mantiene FIFO hasta su integración posterior.

## Reparto

| Rol | Módulos | Integrante | Sesión de agente |
|---|---|---|---|
| A | config, rng, entities, arrivals, entry | Pablo Cuadros | Claude Code |
| B | stadium, exit, emergency, incidents (I1, I4) | Pablo Pérez | Claude Code |
| C | metrics, runner, analysis, experiments, tests | Chema | Codex |

## Revisión local del rol C

Antes de implementar, describir objetivo, cambios y dependencias. Preparar código,
tests y documentación **sin commit**. Al terminar, explicar los cambios y dar
comandos completos para probarlos, con la ruta del clon; indicar tareas siguientes
con sus dependencias. Incorporar correcciones. Commit cuando Chema lo indique;
la publicación y el PR se tratan después. T1.4 ya revisada, publicada y fusionada.

## Verificación

T1.4 integrada con T1.5: 157 tests correctos, 2 xfail esperados. Antes de la última
actualización de main: T1.6, 179 correctos; T1.7, 164 correctos; lint limpio.
Con main `2c8740e`, esta rama pasa `make check`: 197 tests correctos y 2
xfail esperados; lint y diff limpios. Publicada en el PR #9; pendiente de revisión del equipo.

T1.6: `make run EXP=configs/dev/i1_mini.json REPS=3` genera tres filas en
`results/i1_mini_kpis.csv`, semillas 20261105/20261106/20261107 y 600 entradas
por réplica. El CSV es generado, no versionado. `make test` y `make lint`.

T1.7: desde su carpeta, `PYTHONPATH=src make test
VENV=../modelos-simulacion-ES-estadio/.venv` y `make lint
VENV=../modelos-simulacion-ES-estadio/.venv`. Se comparte el entorno, pero
`PYTHONPATH=src` selecciona el código de esa carpeta.

## Dudas abiertas

Ninguna pendiente.

Resueltas el 2026-11-20 (ver `docs/DECISIONES.md`): reparto de roles A/B/C (arriba), I2/I3 en `entry.py` (D8),
utilización de tornos (D12), puerta cerrada sin redirección (D13), evacuación de
quien está en tránsito (D14, hipótesis) y medición temprana de rendimiento (D15).
Verificación de `main` (2026-11-23, tras los PR #5–#8, Python 3.13.2):
`make lint` limpio y `make test` con 175 tests correctos y 2 xfail esperados
(salida, T3.3/T3.4). Prueba manual de T1.4 con `i1_mini`, semilla 20261105:
600 filas, 600 sentados, último asiento en t = +31,907 min. `make run` queda
pendiente de T1.6.
La fusión paralela dejó dos entradas D19 en `DECISIONES.md`: prioridad de A y
alcance provisional del runner de C. Distinguirlas por título hasta acordar la
renumeración. No cambia el comportamiento del modelo.

PR de cierre de Inc1: T1.6 #9 y T1.7 #10, abiertos para revisión del equipo.

## Verificación de cierre T1.7 (PR #10)

Rama sincronizada con main y con la actualización remota del equipo. Siete
pruebas nuevas de conservación por espectador en cada transición, cola pendiente
al alcanzar el límite y muchos tornos con demanda idéntica. Con T1.6 integrada:
204 tests correctos, 2 xfail esperados de salida, lint y comprobación documental
limpios. No cambia código de simulación ni interfaces. Pendiente de revisión y merge.

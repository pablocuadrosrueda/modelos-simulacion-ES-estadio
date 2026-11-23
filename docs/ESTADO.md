# Estado del proyecto

_Última actualización: 2026-11-23. `main` contiene Inc0, Inc1, Inc2 salvo T2.1,
Inc3 completo, módulos de emergencia T4.1/T4.2 y estadística T5.2.
T4.3 (integración de alarma y KPIs) está en revisión en esta rama._

## Hecho

**Inc0 · completado.** Paquete `sanmames` (`pyproject.toml`, `Makefile`, ruff y
pytest), `configs/base.json` + experimentos X0–X7 y S1 como diff, `config.py`
(carga, fusión profunda, validación estricta), `rng.py` (`RngStreams`, un
generador por fuente), contratos (`entities.py`, `metrics.KPI_COLUMNS`,
`runner.SimContext`, stubs con docstring) documentados en `docs/CONTRATOS.md`, y
docs para agentes. Automatización (T0.5, PR #7): CI con ruff + pytest en Python
3.10 y 3.12 y job de docs (`scripts/check_pr_docs.py`), plantilla de PR,
`make check`, `make hooks` y `make docs-check`. Pendiente fuera del repo: activar
la protección de `main` exigiendo esos checks.

**Inc1 · rebanada vertical — completado.**

* T1.1 (A, hecho; PR #1): `arrivals.py`. Franja por perfil + instante uniforme;
  zona/puerta/bloque, grupo, velocidad (normal truncada por inversión de la FDA)
  y distancia, cada uno de su flujo y vectorizados. Espectadores **ordenados por
  llegada** (`id` crece con `t_arrival`); los atributos no dependen del perfil
  (NRC en X2). Tests en `tests/test_arrivals.py` (chi-cuadrado α = 0,001).
* T1.2 (A, hecho; PR #2): `entry.py` con un `PriorityResource` por puerta,
  `priority_of` y `entry_process` sin incidencias por `spectator.gate`. Espera
  hasta `t_arrival` (D16); servicio en torno como atributo `service_s` (D17).
* T1.3 (B, hecho; PR #4): `stadium.py`. Vomitorio FIFO de `vomitory_capacity`
  plazas por `(zona, bloque)`, `stewards_per_zone` acomodadores por zona,
  `seating_process` sin conflictos e `is_late`. Paso por vomitorio sorteado por
  `id` en E0 (D18).
* T1.4 (C, hecho; PR #6): `run_replica`, llegada → entrada → asiento, hasta
  sentarse todos o alcanzar `max_sim_hours` desde apertura (D19). Todas las
  columnas de `SPECTATOR_COLUMNS` y metadatos. `configs/dev/i1_mini.json`: 600
  espectadores, zona A, FIFO, sin incidencias. Rechaza todavía incidencias,
  emergencia y `queue_discipline = "priority"` (ver `docs/AVISOS.md`).
* T1.5 (C, hecho; PR #3): KPIs de entrada y cola máxima por puerta. Utilización
  nominal desde apertura (D12); esperas pendientes no se sustituyen por ceros;
  métricas de fases futuras en NaN.
* T1.6 (C, hecho; PR #9): réplicas con semillas comunes entre variantes, tabla
  con las columnas acordadas y CLI que acepta nombres o rutas de experimento y
  guarda `results/<fichero>_kpis.csv`. Incluye corrección numérica en métricas
  para esperas nulas con redondeo s/min (tolerancia 1e-9 min), con tests.
* T1.7 (C, hecho; PR #10): siete pruebas nuevas de conservación en cada
  transición, cola pendiente al alcanzar el límite y muchos tornos frente a una
  puerta saturada con las mismas llegadas y servicios. Dos xfail de salida
  siguen pendientes de T3.3/T3.4.

**Inc2 · completado salvo T2.1 (en revisión).**

* T2.3 (A, hecho; PR #14): I3 en
  `entry.py`. Cada torno `(zona, puerta, k)` alterna Exponencial(`mtbf_min`) en
  marcha y Uniforme(`repair_min`) parado; pide una plaza con `PRIORITY_FAILURE`
  y `preempt=False` (adelanta a toda la cola, también a `PRIORITY_HIGH`, sin
  cortar un servicio), suma en `failed_turnstiles` y registra `I3` con
  `resource = "A-G1-T2"`, `t_start` y `t_end`. `turnstile_failure_process` lanza
  un sub-bucle por torno; nueva `start_turnstile_failure_processes(ctx)` para E0.
  Generador por torno con `RngStreams.substream` (D22): calendario idéntico con
  2, 3 o 4 tornos. Además, sin cola `t_start_control = t_arrival` exacto (aviso
  de B sobre redondeo s/min). Tests en `tests/test_turnstile_failure.py`,
  `tests/test_rng.py` y `tests/test_entry.py`.
* T2.4 (A, hecho; PR #8): `priority_of` con `queue_discipline == "priority"`:
  los grupos de `priority_groups` piden con `PRIORITY_HIGH` y adelantan a los
  normales; no expulsiva (`preempt=False`) y FIFO dentro de cada nivel (D20).
  Tests en `tests/test_entry.py`, con un escenario exacto a mano y la
  comprobación, con la misma semilla, de que X3 baja la espera de mayores y PMR.
* T2.5 (B, hecho; PR #13): I1 en
  `incidents.py` (`sample_seat_conflicts`, `has_seat_conflict`, `seat_conflict`)
  e integrado en `seating_process`: al llegar al asiento, con `u < prob`, el
  espectador retiene la plaza del vomitorio, espera a un acomodador de su zona y
  resuelve en Triangular(1, 3, 10) min. Ocurrencia y duración sorteadas en E0 por
  `id` (D21, números comunes). Tests en `tests/test_seat_conflict.py`.
* T2.6 (B, hecho; PR #5): `log_incident` y `gate_closure_process` (I4): cierra la
  puerta en `start_min`, registra `I4`, la reabre tras `duration_min` y dispara
  `reopen_event`, que se sustituye por uno nuevo (D13). La elección de puerta
  llega con T2.7; falta lanzarla desde el runner (C).
* T2.7 (A, hecho; PR #16): `choose_gate`
  en `entry.py`, evaluado al llegar (E1). Puerta asignada abierta: esa. Cerrada
  con `redirect_on_gate_closure`: la abierta de su macrozona con menos cola por
  `(len(queue), count, nº de puerta)`, sin azar; sin redirección o sin otra
  abierta: espera en un bucle que lee `reopen_event` en cada vuelta y entra en
  su puerta en orden de llegada (D13). `gate_used` es la puerta real. Quien ya
  está en cola al cerrarse sigue su curso (hipótesis D23, pendiente del grupo).
  Tests en `tests/test_choose_gate.py`, incluido X6 saturado en punta.

* T2.2 (A, hecho; PR #21): I2 en `entry.py`.
  `build_entry_resources` sortea en E0, del flujo `read_failure`, un `u` y un
  extra Uniforme(`extra_s`) por `id` (`sample_read_failures`) y los guarda en
  `EntryResources`; hay relectura si `u < prob` (`has_read_failure`, D26). La
  relectura sigue al servicio sin liberar el torno: `read_failure = True`,
  `t_end_control` incluye el extra e incidencia `I2` de la puerta usada. Mismos
  fallos y extras con 2/3/4 tornos y con otro perfil; al subir `prob` el
  conjunto crece. Tests en `tests/test_read_failure.py`.
* T2.1 (A, en revisión; rama `feat/cuadros-T2.1-capacity`): comprobación de
  capacidad de la memoria (§4.3) en `src/sanmames/capacity.py` (E[S], disponibilidad,
  capacidad, ρ en la franja pico real, vomitorios, vaciado y evacuación) y con
  simulación (reparto, ritmo por torno con cola ≈ teórico, 2/3/4/10 tornos,
  utilización), con X0 completo. Tests en `tests/test_capacity.py`, script
  `scripts/validate_capacity.py` y resultados en `docs/VERIFICACION.md`: todas las
  comprobaciones cuadran. Réplica completa de X0: 3,0 s (10 réplicas: 30,2 s).

**Inc3: en curso.**

* T3.1 y T3.2 (B, hecho; PR #15): `exit.py` con
  `exit_pass_time_s` (60 / (anchura * 66), unos 0,23 s), `build_exit_resources`
  (6 salidas de capacidad 1 por zona), `release_time_min` (simultánea, o la grada
  superior `exit_stagger_min` después), `choose_exit` (menos cola, sin bloqueadas,
  desempate con números comunes, D24) y `exit_process` (liberación, marcha, cola y
  paso). Tests en `tests/test_exit.py`, incluida la validación del apartado 4.3 de
  la memoria: 12.195 personas de una zona cruzan las 6 salidas en 7,7 min.

**Inc4: en curso.**

* T4.1 y T4.2 (B, hecho; PR #19): `emergency.py`
  con `status_at_alarm` (no ha llegado, en cola exterior, dentro o ya fuera),
  `alarm_process` (fase de evacuación, accesos cerrados, reacción sorteada por
  `id`, salidas ensanchadas, salida 1 de la zona A bloqueada si toca, e
  interrupción de los procesos de los espectadores) y `evacuation_process`
  (abandono o reacción, marcha más rápida, salida con menos cola y `t_safe`).
  Decisión D25. Tests en `tests/test_emergency.py`, incluida la validación del
  apartado 4.3 de la memoria: una macrozona evacúa en 5,9 min, y en 7,1 min con
  una salida bloqueada. Falta que el runner lo integre (T4.3, C).

## Siguiente paso

El equipo ha fusionado T2.8 (#18), I2 (#21), emergencia T4.1/T4.2 (#19) y
T3.3/T3.4 mediante el PR #22 (incluye los commits de salida del PR #20).
T5.2 está fusionada en PR #17 con salida y conservación completas.

C publica ahora T4.3: runner con I2 y alarma, interrupción/evacuación de todos los
estados y KPIs de emergencia, sin modificar lógica de A/B. D30 documenta datos
incompletos y metadatos de fin/alarma; D28 desambigua la antigua D25 de evacuación.
Validación conjunta con T5.2: 368 tests correctos, cero xfail y lint limpio. Tres réplicas de cada
variante de `i4_mini` con todas las incidencias; X0 completo ejecutado desde CLI
en un test. Referencias de capacidad en recorrido completo: 7,7 min de salida,
5,9 min de evacuación y 7,1 min con salida bloqueada, sin marcha/reacción para
aislar la capacidad, no como resultados definitivos del escenario real.

Próximo C: T5.1, piloto X0–X7 de diez réplicas con semillas comunes, tras revisar
T4.3 y confirmar T2.1 (A, reparto/rendimiento del estadio completo). T5.2 permite
calcular IC y tamaño definitivo; T5.3 depende del piloto. Después T6.1 gráficas y
T6.2 validación con el equipo; la memoria T6.3 depende de ambas. Los experimentos
oficiales no se lanzan en este PR de integración. Siguen abiertas las dudas de
I3 tras entrada y cierre X6; no se cambian parámetros en silencio.
* A: T2.1 en revisión (rama `feat/cuadros-T2.1-capacity`): comprobación de
  capacidad y tiempo de réplica en `docs/VERIFICACION.md`.

## Reparto

| Rol | Módulos | Integrante | Sesión de agente |
|---|---|---|---|
| A | config, rng, entities, arrivals, entry | Pablo Cuadros | Claude Code |
| B | stadium, exit, emergency, incidents (I1, I4) | Pablo Pérez | Claude Code |
| C | metrics, runner, analysis, experiments, tests | Chema | Codex |

## Revisión local del rol C

Por petición de Chema: antes de implementar, describir objetivo, cambios y
dependencias. Preparar código, tests y documentación **sin commit**. Al terminar,
explicar los cambios y dar comandos completos para probarlos, con la ruta del
clon; indicar tareas siguientes con sus dependencias. Incorporar correcciones.
Commit cuando Chema lo indique; la publicación y el PR se tratan después.
Autorización vigente (2026-11-23): implementar y publicar las siguientes tareas del rol C (T5.2, T2.8, T3.3, T3.4 y T4.3)
por ramas/PR separados, sin fusionarlos directamente.

## Verificación

Rama T4.3 con todo `main`: Python 3.12, `make check` limpio, 368 tests correctos,
sin xfail. Restaurado el import pytest necesario en conservación tras la fusión
de T3.3/T3.4; el PR #23 recoge también el arreglo de contexto del equipo.
B: después, T5.4 (rendimiento) y T6.2/T6.3 con el grupo.

* T1.4: `i1_mini`, semilla 20261105: 600 filas, 600 sentados, último asiento en
  t = +31,907 min.
* T1.6: `make run EXP=configs/dev/i1_mini.json REPS=3` genera tres filas en
  `results/i1_mini_kpis.csv`, semillas 20261105/20261106/20261107 y 600 entradas
  por réplica. El CSV es generado, no versionado.
* T1.7 (PR #10): siete pruebas de conservación por espectador en cada
  transición, cola pendiente al alcanzar el límite y muchos tornos con demanda
  idéntica. Desde su carpeta, `PYTHONPATH=src make test
  VENV=../modelos-simulacion-ES-estadio/.venv` y `make lint
  VENV=../modelos-simulacion-ES-estadio/.venv`. Se comparte el entorno, pero
  `PYTHONPATH=src` selecciona el código de esa carpeta.

## Dudas abiertas

* T2.3 (A → C): los procesos de avería siguen hasta el final de la réplica, así
  que con la salida integrada `n_turnstile_failures` contará también averías
  posteriores a la entrada, que no afectan a nadie. ¿Contar solo las I3 con
  `t_start` anterior al último fin de control, o dejarlo así? La memoria no lo
  precisa; queda para T2.8.
* T2.7 (A → grupo): D23 es una hipótesis: el cierre solo afecta a quien llega
  mientras dura. Alternativa: parar también los tornos de esa puerta y/o
  redirigir su cola; ver D23.
* T2.7 (A → grupo): en `configs/base.json` el cierre empieza en `start_min = +20`,
  cuando solo llega el 2 % del público. En una macrozona realista (N/4, 6
  puertas, semilla 11) afecta a 26 personas frente a 330 si empieza en −25. Con 2
  tornos, la espera máxima en la puerta cerrada pasa de 9,0 a 8,3 min con
  redirección si empieza en +20, y de 16,9 a 6,3 min si empieza en −25. Para que
  P7 mida el «cierre en hora punta» habría que adelantarlo; no se cambia aquí.
* T2.1 (A → grupo): la memoria da ρ ≈ 0,65 para el perfil anticipado; con su
  franja pico real (−45 a −30, 24,4 %) es 0,81. Error de la memoria, no del modelo;
  corregir el texto de la Parte 2. Vaciado simulado 8,3 min frente a 7,7 de
  capacidad pura (incluye marcha y cola): coherente.

Resueltas el 2026-11-20 (ver `docs/DECISIONES.md`): reparto de roles (arriba),
I2/I3 en `entry.py` (D8), utilización de tornos (D12), puerta cerrada sin
redirección (D13), evacuación de quien está en tránsito (D14, hipótesis) y
medición temprana de rendimiento (D15). Resuelta el 2026-11-23: el doble D19 de
la fusión paralela se renumeró; D19 es el alcance del runner y D20 la prioridad.

## Análisis de C (T5.2, fusionada en PR #17)

IC t-Student, réplicas estimadas con el piloto, resúmenes por escenario y
diferencias emparejadas por seed. 41 pruebas propias. Formato D29/CONTRATOS.
Los dos xfail antiguos de salida ya están activados; no quedan pruebas xfail.

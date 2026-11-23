# Estado del proyecto

_Última actualización: 2026-11-23. `main` contiene Inc0, Inc1 e Inc3 completos,
Inc2 salvo T2.1, de Inc4, T4.1 y T4.2, y de Inc5, T5.2. Nada en revisión._

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
  puerta saturada con las mismas llegadas y servicios.

**Inc2 · en curso** (falta T2.1).

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
  llega con T2.7; el runner la lanza en E0 desde T2.8.
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
  conjunto crece. Tests en `tests/test_read_failure.py`. El runner aún la
  rechaza (falta quitar esa guarda, C).
* T2.8 (C, hecho; PR #18): prioridad e incidencias I1, I3 e I4 integradas en el
  runner (averías y cierre lanzados en E0); indicadores por grupos, conflictos y
  recuentos de incidencias; colas por puerta real (`gate_used`). Caso de
  desarrollo `configs/dev/i2_mini.json`. Decisión D25.

**Inc3: completado.**

* T3.1 y T3.2 (B, hecho; PR #15): `exit.py` con
  `exit_pass_time_s` (60 / (anchura * 66), unos 0,23 s), `build_exit_resources`
  (6 salidas de capacidad 1 por zona), `release_time_min` (simultánea, o la grada
  superior `exit_stagger_min` después), `choose_exit` (menos cola, sin bloqueadas,
  desempate con números comunes, D24) y `exit_process` (liberación, marcha, cola y
  paso). Tests en `tests/test_exit.py`, incluida la validación del apartado 4.3 de
  la memoria: 12.195 personas de una zona cruzan las 6 salidas en 7,7 min.
* T3.3 (C, hecho; PR #20): el runner encadena asiento, permanencia y salida y
  termina al salir el último; KPIs de vaciado y cola máxima por salida. Caso
  `configs/dev/i3_mini.json`. Decisión D27.
* T3.4 (C, hecho; PR #22): conservación individual en cada transición y en
  puntos intermedios, con políticas, incidencias y límites de tiempo. Ya no
  queda ningún xfail.

**Inc4: en curso** (falta T4.3).

* T4.1 y T4.2 (B, hecho; PR #19): `emergency.py`
  con `status_at_alarm` (no ha llegado, en cola exterior, dentro o ya fuera),
  `alarm_process` (fase de evacuación, accesos cerrados, reacción sorteada por
  `id`, salidas ensanchadas, salida 1 de la zona A bloqueada si toca, e
  interrupción de los procesos de los espectadores) y `evacuation_process`
  (abandono o reacción, marcha más rápida, salida con menos cola y `t_safe`).
  Decisión D28. Tests en `tests/test_emergency.py`, incluida la validación del
  apartado 4.3 de la memoria: una macrozona evacúa en 5,9 min, y en 7,1 min con
  una salida bloqueada. Falta que el runner lo integre (T4.3, C).

**Inc5: en curso.**

* T5.2 (C, hecho; PR #17): `analysis.py` con intervalos t de Student, réplicas
  necesarias estimadas con el piloto, resúmenes por escenario y diferencias
  emparejadas por semilla. 41 pruebas en `tests/test_analysis.py`. Decisión D29.

## Siguiente paso

* C: T4.3 (integrar la evacuación en el runner; ver `docs/AVISOS.md`) y quitar
  la guarda que aún rechaza I2 (T2.2 ya en `main`); sin eso X0 y X7 no se pueden
  ejecutar. Después T5.1: los experimentos oficiales
  esperan a Inc4 y no se desactivan incidencias del modelo para presentar
  resultados definitivos.
* A: T2.1 (cuatro macrozonas y medida del tiempo de una réplica, D15).
* B: T5.4 (rendimiento) en cuanto haya réplicas completas con evacuación; T6.2
  y T6.3 con el grupo.
* Grupo: confirmar la hipótesis D23 (cola existente al cerrar una puerta) y el
  instante del cierre en X6 (`start_min = +20` cae fuera de la hora punta; ver
  Dudas abiertas).

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
Autorización vigente (2026-11-23): implementar y publicar T5.2, T2.8, T3.3 y T3.4
por ramas/PR separados, sin fusionarlos directamente.

## Verificación

`main` tras los PR #18 a #22 (2026-11-23, Python 3.13.2): `make lint` limpio y
318 tests correctos, sin ningún xfail, una vez repuesto el `import pytest` de
`tests/test_conservacion.py` que se perdió al integrar `main` en la rama de T3.3
(sin él, pytest no llega a ejecutar ese fichero y ruff da error).

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

Resueltas el 2026-11-20 (ver `docs/DECISIONES.md`): reparto de roles (arriba),
I2/I3 en `entry.py` (D8), utilización de tornos (D12), puerta cerrada sin
redirección (D13), evacuación de quien está en tránsito (D14, hipótesis) y
medición temprana de rendimiento (D15). Resuelta el 2026-11-23: el doble D19 de
la fusión paralela se renumeró; D19 es el alcance del runner y D20 la prioridad.

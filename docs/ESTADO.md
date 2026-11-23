# Estado del proyecto

_Última actualización: 2026-11-23. `main` contiene Inc0 a Inc4 completos y, de
Inc5, T5.1, T5.2 y T5.4. T5.3 está en ejecución en esta rama._

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

**Inc2 · completado.**

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
* T2.1 (A, hecho; PR #25): comprobación de
  capacidad de la memoria (§4.3) en `src/sanmames/capacity.py` (E[S], disponibilidad,
  capacidad, ρ en la franja pico real, vomitorios, vaciado y evacuación) y con
  simulación (reparto, ritmo por torno con cola ≈ teórico, 2/3/4/10 tornos,
  utilización), con X0 completo. Tests en `tests/test_capacity.py`, script
  `scripts/validate_capacity.py` y resultados en `docs/VERIFICACION.md`: todas las
  comprobaciones cuadran. Réplica completa de X0: 3,0 s (10 réplicas: 30,2 s).
* Estudio X6 (A, en revisión; rama `feat/cuadros-X6-study`; no es tarea del
  tablero): sensibilidad del instante del cierre I4 (`start_min` de −45 a +20,
  10 y 20 min, con y sin redirección, 5 réplicas con semillas comunes) en
  `scripts/study_gate_closure.py` y `docs/ESTUDIO_X6.md`. Con redirección el cierre
  se absorbe siempre; sin ella el efecto es máximo a −30 (+292 ± 24 s de espera
  media en A-1, +0,67 p. p. de entrada tardía) y nulo a +20 (+4 s). **Decidido (D31):
  `start_min = −30`**, ya aplicado en `configs/base.json` con un test de regresión.

**Inc3: completado.**

* T3.1 y T3.2 (B, hecho; PR #15): `exit.py` con
  `exit_pass_time_s` (60 / (anchura * 66), unos 0,23 s), `build_exit_resources`
  (6 salidas de capacidad 1 por zona), `release_time_min` (simultánea, o la grada
  superior `exit_stagger_min` después), `choose_exit` (menos cola, sin bloqueadas,
  desempate con números comunes, D24) y `exit_process` (liberación, marcha, cola y
  paso). Tests en `tests/test_exit.py`, incluida la validación del apartado 4.3 de
  la memoria: 12.195 personas de una zona cruzan las 6 salidas en 7,7 min.

**Inc4: completado.**

* T4.1 y T4.2 (B, hecho; PR #19): `emergency.py`
  con `status_at_alarm` (no ha llegado, en cola exterior, dentro o ya fuera),
  `alarm_process` (fase de evacuación, accesos cerrados, reacción sorteada por
  `id`, salidas ensanchadas, salida 1 de la zona A bloqueada si toca, e
  interrupción de los procesos de los espectadores) y `evacuation_process`
  (abandono o reacción, marcha más rápida, salida con menos cola y `t_safe`).
  Decisión D28. Tests en `tests/test_emergency.py`, incluida la validación del
  apartado 4.3 de la memoria: una macrozona evacúa en 5,9 min, y en 7,1 min con
  una salida bloqueada.
* T4.3 (C, hecho; PR #24): el runner admite I2 y emergencia; cada recorrido
  captura la interrupción de la alarma y sigue con la evacuación. KPIs de
  emergencia y metadatos de fin y alarma (D30).

**Inc5: en curso.**

* T5.4 (B, hecho; PR #27): tiempo de réplica de
  los 13 escenarios en `docs/VERIFICACION.md`, de 3,4 a 4,3 s, y 4,7 s en X7. En
  X7 bajaba de 6,9 s al quitar una búsqueda en todas las incidencias para cada
  espectador al evacuar; resultados idénticos. Sin más cuellos de botella en los
  módulos de B.

## Siguiente paso

T5.3 en ejecución desde `feat/chema-T5.3-final`, PR #29 (borrador hasta terminar).
Aplicadas decisiones del grupo: X6 en −30 (D31); X5 conserva parámetros y añade
nueve acomodadores (D33). Piloto actualizado completo: 190 réplicas, 19 escenarios
(X0–X7 con 13 variantes principales + seis S1), en `results/final/pilot`.
Las 100 réplicas de escenarios no modificados reproducen todos los KPIs del
piloto anterior. X6 en +20 queda histórico en `results/pilot`.

Piloto X5: duración media de I1 con espera de 44,02 / 13,69 / 6,75 min con
3 / 6 / 9 acomodadores; se conserva el resultado de saturación. X6 en −30:
382,8 llegadas por réplica durante el cierre de A-1; todas redirigidas si se
activa. La espera de ese colectivo es 0,529 min con redirección y 9,678 sin ella.
Son cifras piloto; las definitivas se incorporarán al acabar la campaña.

Objetivo inicial de T5.3: 2.798 réplicas en total (mínimo treinta por escenario,
según precisión del piloto, hasta 247 en S1). Las 190 semillas/escenarios del
piloto se reutilizan; quedan 2.608 nuevas en la primera ampliación. Se volverá
a comprobar el IC 95 % y la semianchura ≤5 % de la espera media (D34), ampliando
los escenarios que lo necesiten. Checkpoints locales por réplica para reanudar
sin duplicados y con validación de código, configs y versiones.

Validación de código: 399 tests correctos, uno lento opcional omitido. CI verde
en Linux Python 3.10/3.12 y prueba específica de Windows (rutas y spawn/reanudación).
Corregidas claves de rutas del manifiesto con `/`, también en Windows.

Después: T6.1 gráficas, T6.2 validación conjunta y T6.3 memoria. I3 conserva D25:
se cuentan todas las incidencias registradas, no solo las que afectaron al público.

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
Autorización vigente (2026-11-23): implementar y publicar las siguientes tareas del rol C (T5.2, T2.8, T3.3, T3.4, T4.3, T5.1 y T5.3)
por ramas/PR separados, sin fusionarlos directamente.

## Verificación

Rama T5.4 sobre `main` tras el PR #25 (Python 3.13.2): 386 passed, 1 skipped; `make lint` limpio.

Rama T4.3 con todo `main`: Python 3.12, `make check` limpio, 368 tests correctos,
sin xfail. Restaurado el import pytest necesario en conservación tras la fusión
de T3.3/T3.4; el PR #23 recoge también el arreglo de contexto del equipo.

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

* T5.4 (B a grupo): en X5 los acomodadores son el cuello de botella. Con
  conflictos al 1 % hay unos 490 por partido, unos 122 por macrozona, y cada uno
  ocupa a un acomodador 4,7 min de media. Con 3 acomodadores por zona, en tres
  réplicas la duración media de un conflicto (con la espera al acomodador) es de
  40 a 52 min, el último espectador se sienta hasta en t = +180 y la réplica
  termina hasta en t = +181. Con 6, de 12 a 17 min. Es lo que dan los parámetros
  de la memoria, no un fallo, pero conviene confirmar que son los que se quieren
  (sobre todo la resolución Triangular(1, 3, 10) min y que un acomodador atienda
  un solo conflicto a la vez) antes de responder P6.
* T2.3 (A → C): los procesos de avería siguen hasta el final de la réplica, así
  que con la salida integrada `n_turnstile_failures` contará también averías
  posteriores a la entrada, que no afectan a nadie. ¿Contar solo las I3 con
  `t_start` anterior al último fin de control, o dejarlo así? La memoria no lo
  precisa; queda para T2.8.
* T2.7 (A → grupo): D23 es una hipótesis: el cierre solo afecta a quien llega
  mientras dura. Alternativa: parar también los tornos de esa puerta y/o
  redirigir su cola; ver D23.
* X6 (A → grupo): en `configs/base.json` el cierre empieza en `start_min = +20`,
  cuando solo llega el 2 % del público, y X6 no responde a nada (diferencia sin −
  con redirección de 4 s). Estudio completo en `docs/ESTUDIO_X6.md`. Decidido (D31):
  `start_min = −30` (10 min), aplicado en `configs/base.json`. La memoria dice +20:
  corregir el texto de la Parte 2.
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

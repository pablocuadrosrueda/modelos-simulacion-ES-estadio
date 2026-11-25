# Estado del proyecto

_Última actualización: 2026-11-25. `main` contiene Inc0 a Inc5 completos y
T6.1 (PR #30). T6.2 en curso: parte de B en la rama `feat/perez-T6.2-validation`._
_Última actualización: 2026-11-25. `main` contiene Inc0 a Inc5 completos
(T5.3 fusionada en PR #29). T6.1 fusionada en PR #30; parte C de T6.2 en revisión._
(T5.3 fusionada en PR #29) y T6.1 (PR #30). T6.2, parte de A, en revisión._

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
  espectadores, zona A, FIFO, sin incidencias. Alcance inicial ampliado después por T2.8/T3.3/T4.3.
* T1.5 (C, hecho; PR #3): KPIs de entrada y cola máxima por puerta. Utilización
  nominal desde apertura (D12); esperas pendientes no se sustituyen por ceros;
  métricas de fases futuras en NaN.
* T1.6 (C, hecho; PR #9): réplicas con semillas comunes entre variantes, tabla
  con las columnas acordadas y CLI que acepta nombres o rutas de experimento y
  guarda `results/<fichero>_kpis.csv`. Incluye corrección numérica en métricas
  para esperas nulas con redondeo s/min (tolerancia 1e-9 min), con tests.
* T1.7 (C, hecho; PR #10): siete pruebas nuevas de conservación en cada
  transición, cola pendiente al alcanzar el límite y muchos tornos frente a una
  puerta saturada con las mismas llegadas y servicios. Los dos xfail de salida
  se activaron posteriormente en T3.3/T3.4.

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
  llega con T2.7; lanzada desde el runner en T2.8 (C).
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

**Inc5: completado.**

* T5.4 (B, hecho; PR #27): tiempo de réplica de
  los 13 escenarios en `docs/VERIFICACION.md`, de 3,4 a 4,3 s, y 4,7 s en X7. En
  X7 bajaba de 6,9 s al quitar una búsqueda en todas las incidencias para cada
  espectador al evacuar; resultados idénticos. Sin más cuellos de botella en los
  módulos de B.

**Inc6: en curso.**

* T6.2, parte de A (en revisión; rama `feat/cuadros-T6.2-verificacion`):
  entrada y capacidad contrastadas con `results/final` **sin regenerar datos**
  (`scripts/validate_final.py`, `tests/test_validacion_entrada.py`, resultados en
  `docs/VERIFICACION.md`). Cuadran con la memoria: E[S] 4,3 s (I2 3,001 ± 0,011 %),
  disponibilidad 97,4 % (I3 60,1 ± 1,0 averías frente a 59,4), 13,54 pers/min
  medidos con cola frente a 13,59, ρ = 0,70 / 0,93 / 1,40, repartos por zona,
  franja y grupo (χ², p ≥ 0,2), conservación en las 2.965 réplicas y números
  comunes (KPIs de entrada idénticos semilla a semilla). Nuevo modelo fluido en
  `capacity.py`: reproduce la espera de X1_2tornos (3,83 frente a 4,02 ± 0,08 min;
  P95 11,76 frente a 11,9) y del cierre X6 (9,66 frente a 9,63 ± 0,12 sin
  redirección; 0,59 frente a 0,54 con ella). Casos límite: la espera crece a
  ρ − 1 con 2 tornos, plana con 4, y cierre en −30 con/sin redirección.
  `busy_rate_per_turnstile` pasa a `capacity.py` (estaba duplicada en el test y
  el script de T2.1). No cambia ningún parámetro, hipótesis ni dato de
  `results/final`. Pendiente de B y C, listado en VERIFICACION: salida 7,7 min,
  evacuación 5,9/7,1 min, dispersión de I1, KPIs de C.

## Siguiente paso

T5.3 terminada y fusionada en PR #29.
**2.965 réplicas completas de 19 escenarios**: 13 principales X0–X7 (incluye
X5 con 3/6/9 acomodadores y X6 en −30) y seis S1. Entre 30 y 247 réplicas por
escenario. Los 19 IC al 95 % cumplen semianchura ≤5 % de la espera media;
máximo observado 4,9865 %. Piloto actualizado: 190 réplicas; las 100 de escenarios
sin cambio reproducen todos los KPIs anteriores. Las diez de cada piloto se
reutilizan sin contarlas dos veces. X6 en +20 queda histórico.

Datos definitivos y procedencia: `results/final`; piloto actualizado en su
subcarpeta `pilot`. Informe reproducible: `docs/RESULTADOS_T5.3.md`, generado
con `scripts/report_campaign.py`. El cálculo se fija en commit `fd6475c`;
se verificaron sus 18 hashes al terminar. Las mejoras posteriores del informe
y de conservación de objetivos al reanudar no cambian esos datos ni su origen.

Resultados principales (IC del 95 % en el informe):
* X5, 180 réplicas por nivel: duración media I1 con espera de 44,60 / 13,74 /
  6,64 min con 3 / 6 / 9 acomodadores. Decisión D33 aplicada sin reducir los
  parámetros de resolución; la saturación de tres es resultado de P6.
* X6 en −30: espera del colectivo que llega a A-1 durante el cierre de 0,543
  min con redirección (199 réplicas), frente a 9,626 sin ella (45 réplicas).
* X7, 180 por variante: vaciado medio 7,469 min sin bloqueo y 8,420 con uno.
  Vaciado completo ≤8 min en 163/180 y 0/180; no confundir media con garantía.

Validación local: 400 tests correctos, uno lento opcional omitido, lint limpio.
Auditoría: cero pérdidas o duplicados, semillas por índice correctas, tamaños
no inferiores al plan, 180 semillas con idénticos conflictos en X5 3/6/9, y
verificación del cierre/redirección. Hay CI Linux 3.10/3.12 y Windows específica
para rutas y procesos/reanudación. Checkpoints locales, agregados versionados.

**T6.1 fusionada en PR #30**: figuras P1–P8
**T6.1 hecha (PR #30)**: figuras P1–P8
y suplemento S1 en PNG 300 dpi + SVG, con IC del 95 %, unidades y n.
Comando: `.venv/bin/python scripts/plot_results.py`. Índice e interpretación en
`docs/GRAFICAS_T6.1.md`; puntos exactos y hashes en `results/figures`.
No se repiten simulaciones ni se alteran los datos finales. P4 usa colectivos
comparables; P6 distingue duración I1 y retraso del resto; P8 separa media de
vaciado y frecuencia observada de cumplir ocho minutos.

**T6.2 · parte C preparada para revisión**, rama `feat/chema-T6.2-verificacion-C`.
`scripts/verify_results.py` comprueba las 2.965 réplicas: identidades entre tablas,
recuentos terminales, reparto, relojes, rangos de KPIs y NaN según la fase.
Recalcula resumen, contrastes emparejados (P4 con colectivos comparables) y precisión.
Con `--replay` se han repetido 19 réplicas (una por escenario, semilla 20261105):
IDs y terminación correctos, los 21 KPIs coinciden con T5.3 en todos los casos.
Código de `src/` contrastado por SHA-256 con el de la campaña, salvo
`capacity.py` (módulo de análisis, ver abajo).

**Arreglo de CI (A, rama `fix/cuadros-verify-capacity`).** Tras T6.2 de A (PR #33),
`test_bad_replay_is_rejected_instead_of_reporting_success` fallaba: `--replay`
rechazaba la huella de `src/sanmames/capacity.py`, que ganó funciones nuevas
(modelo fluido, `busy_rate_per_turnstile`). El diff respecto a `fd6475c` es solo
aditivo y ningún módulo que genera datos importa `capacity`, así que se excluye
de la comprobación de huellas (`ANALYSIS_ONLY`). Tests nuevos: cambiar
`capacity.py` no bloquea el replay y cambiar `runner.py` sí. `--replay` completo
repetido el 2026-11-25 (Python 3.13.2): 19 escenarios, los 21 KPIs coinciden.
No cambian `results/final` ni el modelo.
Informe y límites: `docs/VERIFICACION_C_T6.2.md`. No se alteran modelo ni datos.

**T6.2 sigue en curso**: A y B deben revisar/confirmar la evidencia existente
de capacidad y supuestos de sus módulos (`docs/VERIFICACION.md`). No se da
por cerrada su parte. T6.3 (memoria) depende del cierre conjunto de T6.2; las
figuras de T6.1 ya están en main.
**T6.2 en curso.** Documento común `docs/VALIDACION_T6.2.md`: mapa de cada
comprobación del apartado 6 de la especificación con su prueba y su resultado,
para que A y C revisen su parte. B añade `scripts/validate_b.py`, con dos
comprobaciones sobre la simulación completa. En X5, con acomodadores casi
ilimitados la duración de un conflicto baja a 4,62 min, la media teórica de la
resolución (4,67): la saturación se debe a los acomodadores. En X7 con todas las
salidas, en las 17 de 180 réplicas que superan 8 min solo llega tarde una
persona de movilidad reducida, sin cola; sin ese colectivo el vaciado no pasa de
7,36 min. Con una salida bloqueada manda la cola en las salidas.

**Siguiente: completar T6.2**, verificación/validación conjunta de A, B y C. Puede iniciarse
ya con T5.3 fusionada. T6.3, memoria de resultados, depende de T6.1 y T6.2.
**Siguiente: T6.2**, verificación/validación conjunta. Parte de A en revisión;
B y C tienen su lista en `docs/VERIFICACION.md` («Pendiente de B y C»). T6.3,
memoria de resultados, depende de T6.1 y T6.2.
En la Parte 2 se justifican X6 en −30 (D31), X5 con nueve (D33), los tamaños
necesarios por precisión (D34) y ρ anticipado=0,81 de la verificación de A.
I3 conserva D25: se cuentan todas las incidencias registradas, no solo las que
perjudicaron a espectadores. No se cambian hipótesis de D23 en esta campaña.

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

T6.2 C (2026-11-25, Python 3.12): `make check`, 421 passed y 1 skipped
(capacidad lenta opcional), lint y docs-check limpios. Catorce pruebas nuevas
detectan corrupción de auditoría, reloj, reparto, resumen, contrastes, precisión,
KPIs, colectivos y reproducción; comprueban invariancia al reordenar y que un
fallo no sobrescriba el informe. Se normaliza CRLF→LF al verificar el código
para admitir el checkout de Windows sin ocultar cambios reales. Reproducidos
realmente los 19 escenarios, una semilla cada uno, con los 21 KPIs y metadatos de auditoría coincidentes.

T6.2, parte de A (2026-11-25, Python 3.13.2): `make check`, 434 passed y 2
skipped (lentos opcionales; con `RUN_SLOW=1` pasan, incluida la réplica que
reproduce `kpis.csv`), lint y docs-check limpios. `git diff` sin cambios en
`results/`.

T6.1 (2026-11-25, Python 3.12): `make check`, 407 passed y 1 skipped
(prueba lenta opcional de capacidad), lint y docs-check limpios. Siete pruebas
nuevas de emparejamiento, identidades, unidades, conteo y exportación; revisión
visual de las nueve figuras. CI Windows ampliada a la exportación de figuras.

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

## Hipótesis y texto pendiente para la Parte 2

* I3 conserva la definición literal D25: incluye averías posteriores a la entrada.
  El recuento no equivale al número de averías que afectaron a espectadores.
* D23 se mantiene: el cierre solo afecta a quienes llegan mientras dura; las
  personas ya en cola siguen atendidas. Cualquier cambio sería otro modelo.
* X5 resuelta por el grupo (D33): se mantienen los parámetros y la saturación
  con tres; se amplía a nueve. Resultados en `RESULTADOS_T5.3.md`.
* X6 resuelta (D31): cierre en −30, aplicado y recalculado. Corregir en la Parte
  2 el +20 de la memoria de la Parte 1; los resultados antiguos son históricos.
* Verificación de A: el pico real anticipado da ρ≈0,81, no 0,65 como decía la
  Parte 1. Corregir el texto; capacidad pura de salida ≈7,7 min y simulación
  añade marcha/cola. No se modifican parámetros por esa diferencia.
* T6.2 (A): correcciones del PDF de la Parte 2 en `docs/VERIFICACION.md`
  («Discrepancias»): ρ de X2 = 0,81; cierre I4 en −30 (D31); y matizar «la cola
  crece sin parar» con 2 tornos (crece durante la punta y se vacía después).
* Duda abierta (T6.2): §6 pide que el ritmo por torno coincida con F2. El modelo
  da 13,6 pers/min, igual al derivado de los parámetros de la memoria, pero la
  cifra publicada en F2 no está en el repo: contrastarla al redactar la Parte 2.

Resueltas el 2026-11-20 (ver `docs/DECISIONES.md`): reparto de roles (arriba),
I2/I3 en `entry.py` (D8), utilización de tornos (D12), puerta cerrada sin
redirección (D13), evacuación de quien está en tránsito (D14, hipótesis) y
medición temprana de rendimiento (D15). Resuelta el 2026-11-23: el doble D19 de
la fusión paralela se renumeró; D19 es el alcance del runner y D20 la prioridad.

## Análisis de C (T5.2, fusionada en PR #17)

IC t-Student, réplicas estimadas con el piloto, resúmenes por escenario y
diferencias emparejadas por seed. 41 pruebas propias. Formato D29/CONTRATOS.
Los dos xfail antiguos de salida ya están activados; no quedan pruebas xfail.

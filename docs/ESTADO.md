# Estado del proyecto

_Última actualización: 2026-11-23 · `main` contiene Inc0 y T1.1/T1.2/T1.3;
T1.4 revisada por Chema, preparada para PR desde `feat/chema-T1.4-runner`._

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

* T1.4 (C, en revisión; rama `feat/chema-T1.4-runner`): `run_replica` crea el entorno
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
* T1.5 (C, en revisión): métricas en el
  [PR #3](https://github.com/pablocuadrosrueda/modelos-simulacion-ES-estadio/pull/3),
  todavía independiente de esta rama y sin fusionar. No se ha mezclado su código
  en T1.4; ambas ramas parten de `main` y sus cambios de documentación deberán
  reconciliarse al fusionar.

## Siguiente paso

**Inc1 · rebanada vertical** (ver `docs/TAREAS.md`): una macrozona, entrada sin
incidencias, CSV y KPIs de espera. En paralelo:

* A y B: T1.1/T1.2/T1.3 ya fusionadas; continuar sus tareas según dependencias.
* C: revisión local de T1.4 con Chema antes del commit y revisión del equipo de
  T1.5 (PR #3). T1.6 necesita ambos módulos: runner y métricas. T1.7 necesita
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
Probado con Python 3.13.2 (rama T1.3): 114 tests pasan, 5 xfail esperados, ruff limpio.
Verificación local de T1.4 con Python 3.12.14: `make test` da 134 tests correctos
y 2 xfail esperados (salida pendiente); `make lint` y `git diff --check` limpios.
Prueba manual de `i1_mini`, semilla 20261105: 600 filas, 600 sentados, último
asiento en t = +31,907 min. Para las pruebas de esta tarea, desde la raíz del
clon: `.venv/bin/python -m pytest tests/test_runner.py tests/test_orden_temporal.py
tests/test_conservacion.py -v`. `make run` queda pendiente de T1.6.

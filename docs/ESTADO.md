# Estado del proyecto

_Última actualización: 2026-11-23 · main verificado en `2c8740e`.
T1.7 revisada por Chema, preparada para publicar en `feat/chema-T1.7-verificacion`._

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
* T1.6 (C, en curso; sin commit): réplicas con semillas comunes entre variantes,
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
Con main `2c8740e`, esta rama pasa `make check`: 182 tests correctos y 2
xfail esperados; lint y diff limpios. Publicación autorizada por Chema; pendiente de revisión del equipo.

T1.6: `make run EXP=configs/dev/i1_mini.json REPS=3` genera tres filas en
`results/i1_mini_kpis.csv`, semillas 20261105/20261106/20261107 y 600 entradas
por réplica. El CSV es generado, no versionado. `make test` y `make lint`.

T1.7: desde su carpeta, `PYTHONPATH=src make test
VENV=../modelos-simulacion-ES-estadio/.venv` y `make lint
VENV=../modelos-simulacion-ES-estadio/.venv`. Se comparte el entorno, pero
`PYTHONPATH=src` selecciona el código de esa carpeta.

## Dudas abiertas

La fusión paralela dejó dos entradas D19 en `DECISIONES.md`: prioridad de A y
alcance provisional del runner de C. Distinguirlas por título hasta acordar la
renumeración. No cambia el comportamiento del modelo.

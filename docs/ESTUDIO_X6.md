# Estudio: instante del cierre de puerta (I4) para X6 / P7

**Pregunta:** ¿qué valor de `incidents.gate_closure.start_min` permite que X6
responda a P7 («cierre en hora punta»)? En `configs/base.json` el cierre (puerta 1
de la macrozona A, 10 min) empieza en **+20 min**, cuando solo llega el 2 % del
público.

**Cómo se ha hecho:** `scripts/study_gate_closure.py` (API pública: `load_config`,
`run_replica`, `compute_kpis`, `analysis.confidence_interval`). Base X0 con todas
sus incidencias (I1, I2, I3); solo cambian el instante, la duración y la
redirección. 5 réplicas por celda con semillas comunes 20261105 + i (D11): 95
réplicas en 394 s. Medias ± semianchura del IC 95 % (t de Student, n = 5); las
diferencias sin − con redirección son **emparejadas por semilla**. Filas por
réplica en `results/estudio_x6.csv` (no versionado).

**Ejecución:** 2026-11-23 · Python 3.13.2 · `main` en `d10fa96`.

«A-1» = espectadores **asignados** a la puerta cerrada (≈ 2.000 por réplica),
estén o no redirigidos.

## Resultados · cierre de 10 min

Sin / con redirección:

| Inicio | Espera media A-1 (s) | Espera máx. A-1 (min) | % A-1 > 10 min | Cola máx. en una puerta | Entrada tardía (%) | Llegan a A-1 en el cierre | En cola en A-1 al cerrar |
|---|---|---|---|---|---|---|---|
| −45 | 175 ± 64 / 23 ± 28 | 10,0 / 1,6 | 0,0 / 0,0 | 226 / 134 | 4,51 / 4,35 | 221 | 0 |
| **−30** | **302 ± 28 / 10 ± 7** | 10,4 / 1,3 | 7,1 / 0,0 | 389 / 127 | 5,03 / 4,36 | 380 | 0 |
| −20 | 208 ± 10 / 14 ± 13 | 10,1 / 1,8 | 1,5 / 0,0 | 368 / 137 | 5,06 / 4,47 | 364 | 40 ± 64 |
| −10 | 134 ± 14 / 26 ± 23 | 10,0 / 1,9 | 0,5 / 0,0 | 369 / 134 | 5,00 / 4,66 | 369 | 32 ± 38 |
| 0 | 40 ± 26 / 23 ± 28 | 9,8 / 1,6 | 0,0 / 0,0 | 134 / 134 | 4,35 / 4,35 | 91 | 5 |
| +20 (base actual) | 28 ± 28 / 23 ± 28 | 9,5 / 1,6 | 0,0 / 0,0 | 134 / 134 | 4,35 / 4,35 | 28 | 0 |
| sin cierre | 23 ± 28 | 1,6 | 0,0 | 134 | 4,35 | — | — |

Diferencia **sin − con** redirección (IC 95 %, emparejada):

| Inicio | Espera media A-1 (s) | Espera máx. A-1 (min) | Entrada tardía (p. p.) | p95 global (min) |
|---|---|---|---|---|
| −45 | 152 ± 41 | 8,4 ± 1,3 | 0,16 ± 0,16 | 0,46 ± 0,29 |
| **−30** | **292 ± 24** | 9,1 ± 0,7 | **0,67 ± 0,11** | 0,41 ± 0,64 |
| −20 | 194 ± 6 | 8,3 ± 1,0 | 0,59 ± 0,14 | 0,21 ± 0,38 |
| −10 | 108 ± 11 | 8,1 ± 1,1 | 0,35 ± 0,10 | 0,13 ± 0,10 |
| 0 | 17 ± 4 | 8,2 ± 1,5 | 0,00 ± 0,00 | 0,05 ± 0,04 |
| +20 | 4 ± 1 | 7,9 ± 1,1 | 0,00 ± 0,00 | 0,01 ± 0,01 |

## Resultados · cierre de 20 min (instantes de la punta)

| Inicio | Espera media A-1 (s), sin / con | % A-1 > 10 min, sin / con | Diferencia de espera media A-1 (s) | Diferencia de entrada tardía (p. p.) |
|---|---|---|---|---|
| −30 | 659 ± 24 / 22 ± 7 | 58,9 / 0,0 | 636 ± 25 | 1,06 ± 0,17 |
| −20 | 468 ± 12 / 29 ± 12 | 40,6 / 0,0 | 439 ± 10 | 0,76 ± 0,17 |
| −10 | 284 ± 5 / 26 ± 23 | 23,2 / 0,0 | 258 ± 21 | 0,35 ± 0,10 |

## Contraste con la prueba previa

Con la semilla 20261105, la réplica de prueba da a −30 min 310,6 s sin redirección
y 7,1 s con ella, y a +20 min 55,9 s frente a 51,0 s: coincide con los órdenes de
magnitud previos. A +20 la espera de A-1 es alta en esa semilla porque el torno
A-G1-T1 se avería de −28,5 a −19 min (I3), no por el cierre: sin cierre da también
51 s. Con 5 réplicas ese efecto se promedia (23 ± 28 s).

## Conclusiones

1. **Con redirección el cierre se absorbe por completo en cualquier instante.**
   Las métricas con redirección no se distinguen de las de sin cierre: las otras
   cinco puertas de la macrozona tienen holgura (ρ ≈ 0,93 en punta con 3 tornos).
2. **Sin redirección, el efecto depende por completo del instante:**
   * **−30 a −10 (la punta, −30 a 0 con el 56 % de las llegadas):** efecto grande y
     claro. A −30, unas 380 personas llegan a una puerta cerrada, la espera media de
     A-1 pasa de ≈ 10 s a ≈ 300 s, la cola máxima de una puerta se triplica y la
     entrada tardía sube 0,67 p. p.
   * **−45:** efecto moderado (la punta aún no ha empezado).
   * **0 y +20: no se nota.** A +20 solo 28 personas encuentran la puerta cerrada;
     la diferencia es de 4 s y la entrada tardía no cambia. Con el valor actual,
     **X6 no responde a nada**.
3. **El máximo está en −30 y no en el centro de la punta.** Con el cierre a −30
   la reapertura (−20) llega con la punta en pleno ritmo: la puerta recupera su
   cola con muy poca holgura (≈ 38 llegadas/min frente a ≈ 41 de capacidad) y el
   atasco dura más. A −20 o −10 parte del vaciado cae después del inicio, cuando
   las llegadas bajan al 7 %.
4. El **p95 global** apenas cambia (el cierre afecta a 1 de 24 puertas). Para P7
   conviene informar de indicadores **de la puerta afectada** (espera media y
   máxima de A-1, cola máxima por puerta) y de la entrada tardía.
5. Con 10 min de cierre, la espera máxima sin redirección ronda los 10 min, justo
   el umbral del «% > 10 min»: ese indicador es inestable (7,1 ± 10,6 %). Con 20
   min sí discrimina (59 % frente a 0 %).

## Recomendación

**`start_min = −30`, `duration_min = 10`** (el resto igual: puerta 1 de A).

* Es el comienzo de la franja de máximas llegadas (−30 a 0, 28 % + 28 %), así que
  es literalmente un «cierre en hora punta», y es donde el efecto del cierre y el
  valor de la redirección son mayores y más nítidos (IC estrechos frente a la
  diferencia).
* Mantiene la duración de la memoria (10 min); solo cambia el instante.
* Es el instante en que la hipótesis D23 pesa menos (ver abajo): no hay cola
  formada al cerrar.

**Qué responde X6 en cada caso:**

* Con −30: «un cierre de 10 min en hora punta sin redirección cuesta unos 5 min de
  espera media a los asignados a esa puerta (máxima ≈ 10 min) y +0,7 p. p. de
  entrada tardía; con redirección a la puerta de su macrozona con menos cola el
  impacto desaparece».
* Con +20 (actual): «el cierre no tiene efecto», pero es un artefacto del
  instante, no una propiedad del sistema.

**Alternativas para el grupo:**

* **−20, 10 min:** efecto algo menor (194 s), en el centro de la primera mitad de
  la punta; más expuesto a D23 (hasta ≈ 100 personas en cola al cerrar).
* **−30, 20 min:** escenario de estrés: la espera media de A-1 sin redirección
  sube a ≈ 11 min y el 59 % supera los 10 min; la redirección lo sigue absorbiendo.
  Cambia también la duración de la memoria.
* **Mantener +20:** solo si se quiere estudiar un cierre fuera de punta; entonces
  P7 no debería formularse como «en hora punta».

## Limitación: cola ya formada al cerrar (D23)

El modelo aplica la hipótesis D23: el cierre afecta solo a quien **llega** mientras
dura, y quien ya estaba en la cola de A-1 sigue siendo atendido. La columna «En
cola en A-1 al cerrar» mide a cuántos afectaría la alternativa (parar también la
cola):

| Inicio | En cola al cerrar, por réplica | Frente a llegadas durante el cierre |
|---|---|---|
| −30 | 0, 2, 0, 0, 0 | ≈ 380 |
| −20 | 103, 90, 6, 0, 3 | ≈ 364 |
| −10 | 71, 47, 41, 0, 1 | ≈ 369 |
| 0, +20, −45 | ≤ 14 | — |

Las colas al cerrar aparecen cuando el cierre cae con la punta ya empezada o
coincide con una avería I3 en esa puerta. Con −30 la hipótesis no cambia nada; a
−20/−10 la alternativa sumaría hasta ≈ 100 personas al efecto sin redirección
(hasta ≈ 25 % más de afectados en las peores semillas). Otro argumento para −30.
No se ha cambiado el modelo.

## Pendiente

* Que el grupo confirme el valor (D31). Después, en un commit aparte: cambiar
  `configs/base.json` (y los `X6_*.json` si hiciera falta) y sus tests.
* El piloto T5.1 no debería lanzarse con `start_min = +20` (aviso a C).

# Verificación y validación del modelo (T6.2)

**Cierre (2026-11-25):** partes A/B/C fusionadas en PR #33/#32/#31;
Chema confirma su terminación. Se mantiene la limitación de validación externa.

Documento común de A, B y C. Reúne, para cada comprobación que pide la
especificación (apartado 6 de `docs/ESPECIFICACION.md`), dónde está la prueba y
qué resultado da. Cada rol completa y revisa su parte.

## Mapa de comprobaciones

| Comprobación | Qué se exige | Dónde está la prueba | Resultado | Rol |
|---|---|---|---|---|
| Conservación | La suma de espectadores en todos los estados es siempre N | `tests/test_conservacion.py` (T1.7, T3.4) y auditoría de `results/final` | Pruebas por transición y auditoría final agregada de 2.965 réplicas; detalle en VERIFICACION_C_T6.2.md | C |
| Orden temporal | Llegada, inicio y fin de control, vomitorio, asiento y salida en orden | `tests/test_orden_temporal.py` y tests de cada módulo | Cumple, con tolerancia de 1e-9 min por el paso de segundos a minutos | C |
| Capacidad de recursos | Ningún recurso supera su capacidad | Tests de tornos, vomitorios, acomodadores y salidas | Cumple: tornos, 8 plazas por vomitorio, acomodadores por zona y una persona por salida cada 0,227 s | A, B |
| Casos límite de entrada | Muchos tornos, colas casi nulas; 2 tornos, saturación en punta | `docs/VERIFICACION.md` (T2.1) | Cumple; carga en punta de 1,40 con 2 tornos, 0,93 con 3 y 0,70 con 4 | A |
| Ritmo por torno frente a F2 | El ritmo coincide con el derivado de los parámetros de la Parte 1 | `docs/VERIFICACION.md` (T2.1) | Coherente con la Parte 1: 13,54–13,59 pers/min; F2 no consultada directamente | A |
| Salida frente a la Parte 1 | Una macrozona cruza sus 6 salidas en unos 7,7 min | `tests/test_exit.py` y `docs/VERIFICACION.md` | 7,7 min | B |
| Evacuación frente a la Parte 1 | 5,9 min con todas las salidas y 7,1 con una bloqueada | `tests/test_emergency.py` y `docs/VERIFICACION.md` | 5,9 y 7,1 min | B |
| Saturación de acomodadores (P6) | La cola de X5 se debe a los acomodadores | `scripts/validate_b.py` (abajo) | Con acomodadores casi ilimitados, la duración vuelve a la teórica | B |
| Causa de no cumplir 8 min (P8) | Saber si falla la capacidad de las salidas o la marcha | `scripts/validate_b.py` (abajo) | Con todas las salidas, falla una sola persona de movilidad reducida | B |
| Peso de los conflictos en la entrada tardía de X0 (P1) | Cuánto aporta I1 a la entrada tardía y al acceso del escenario base | `scripts/validate_b.py` (abajo) | 0,090 puntos de entrada tardía y 0,032 min de acceso, con 180 parejas | B |
| Números aleatorios comunes | Los escenarios comparados usan los mismos números | Tests de cada módulo y auditoría de `results/final` | Cumple; por ejemplo, X5 con 3, 6 y 9 tiene los mismos conflictos en las 180 semillas | A, B, C |
| Precisión de los resultados | Semianchura del intervalo de la espera media no mayor que el 5 % | `docs/RESULTADOS_T5.3.md` | Cumple en los 19 escenarios; máximo 4,99 % | C |

## Parte B: comprobaciones con la simulación completa

Se reproducen con `python scripts/validate_b.py` (unos dos minutos). Medido el
2026-11-25 con Python 3.13.2.

### 1. Los acomodadores explican la saturación de X5

Si el retraso de los conflictos en X5 se debe a que faltan acomodadores, con
acomodadores casi ilimitados la duración de un conflicto debe ser solo su
resolución, Triangular(1, 3, 10) min, de media 4,67 min.

| Acomodadores por zona | Réplicas | Duración media de un conflicto (min) | Rango entre réplicas (min) |
|---|---|---|---|
| 6 (X5) | 5 | 14,25 | 11,84 a 17,16 |
| 1.000 | 5 | 4,62 | 4,51 a 4,68 |

Con 1.000 acomodadores la duración baja a 4,62 min, la media teórica de la
resolución. Toda la diferencia con X5 es la espera al acomodador: el modelo se
comporta como se espera y la saturación con 3 acomodadores es un resultado, no
un fallo.

### 2. Por qué X7 con todas las salidas no siempre vacía en 8 min

Con todas las salidas, 17 de las 180 réplicas de `results/final` superan los
8 min de referencia. En todas ellas:

* solo una persona llega a zona segura después de los 8 min, y siempre es de
  movilidad reducida;
* esa persona no hace cola: cruza la salida en 0,17 s, el paso de evacuación;
* su marcha hasta la salida dura entre 6,3 y 7,7 min, a la que se suma su
  tiempo de reacción;
* sin contar a las personas de movilidad reducida, el vaciado no pasa de
  7,36 min.

Con todas las salidas abiertas, la capacidad de las salidas sí cumple los
8 min: lo que falla es la marcha de una persona muy lenta y lejos de la salida
(velocidad de hasta 0,6 por 0,5 por 1,2 = 0,36 m/s y distancia de hasta 180 m).
Con una salida bloqueada, en cambio, el vaciado lo marca la cola en las salidas
(unos 8,4 min en las réplicas revisadas) y no se cumple en ninguna réplica.

Para la respuesta a P8 conviene distinguir los dos casos: con todas las salidas
el riesgo está en evacuar a las personas de movilidad reducida, no en la anchura
de las salidas.

### 3. Peso de los conflictos en la entrada tardía del escenario base

X0 tal como está en `results/final` frente a X0 sin conflictos por asiento, con
las mismas 180 semillas (20261105 a 20261284). Los valores con conflictos se leen
de `results/final/kpis.csv`; los valores sin conflictos se simulan con
`scripts/validate_b.py`. Media y semianchura del intervalo de confianza del 95 %
(t de Student); las diferencias son emparejadas por semilla.

| Indicador | Con conflictos | Sin conflictos | Diferencia | n |
|---|---|---|---|---|
| Entrada tardía (%) | 4,578 (0,052) | 4,488 (0,051) | 0,090 (0,006) | 180 |
| Tiempo medio de acceso (min) | 1,972 (0,008) | 1,941 (0,008) | 0,032 (0,001) | 180 |

Los valores con conflictos coinciden con los oficiales de `results/final`. Los
conflictos explican menos del 2 % de la entrada tardía del escenario base.
Sustituye a la estimación anterior con 20 semillas (0,08 puntos).

## Partes A y C

A: `docs/VERIFICACION.md`, sección T6.2 (PR #33). C: `docs/VERIFICACION_C_T6.2.md`
(PR #31), con las comprobaciones por réplica, recálculo de tablas y diecinueve
reproducciones. No se ha consultado F2 directamente; el ritmo se contrasta con
los parámetros de la memoria, sin afirmar validación independiente de esa fuente.

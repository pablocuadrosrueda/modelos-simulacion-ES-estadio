# A3 · Respuestas a P1, P2, P3, P4 y P7

> Borrador del rol A para la memoria de la Parte 2 (T6.3). P5, P6 y P8 son de B;
> el método estadístico y las conclusiones generales, de C.

**Cómo leer las cifras.** Todas salen de `results/final` (tablas `summary.csv`,
`comparisons.csv`, `kpis.csv` y `audit.csv`) y de `docs/RESULTADOS_T5.3.md`. Se
dan como media ± semianchura del intervalo de confianza del 95 % (t de Student,
una observación por réplica) y con el número de réplicas n. Las diferencias
entre escenarios son **emparejadas por semilla** («parejas»): escenario −
referencia, con los mismos espectadores, servicios e incidencias. La precisión
de la campaña (semianchura ≤ 5 % de la media) se garantizó para la espera media
(D34), no para cada indicador. Las figuras están en `results/figures` y se
describen en `docs/GRAFICAS_T6.1.md`.

En cada respuesta se separa lo que es **hallazgo del modelo** (se sigue de la
lógica y de los parámetros) de lo que **depende de supuestos** sin datos reales.
Como advertía la Parte 1 (§5.3), los resultados son comparaciones entre
escenarios, no predicciones exactas de San Mamés.

---

## P1 · ¿Qué esperas, colas y utilización de tornos produce la operativa actual? ¿Dónde está el cuello de botella?

**Respuesta.** Con la operativa actual (X0: 3 tornos por puerta, FIFO, perfil
base, I1–I3 activas) las esperas en los tornos son cortas y nadie espera 10
minutos, pero los tornos trabajan cerca de su límite en la media hora punta y
son el cuello de botella de la entrada.

**Cifras** (X0, n = 180; figura **P1**):

| Indicador | Valor |
|---|---|
| Espera media en cola | 0,192 ± 0,008 min (unos 11,5 s) |
| Percentil 95 de la espera (media de los P95 por réplica) | 1,150 ± 0,068 min |
| Público que espera menos de 10 min | 100,0 % en las 180 réplicas |
| Máximo de personas en la cola de una puerta | 135 ± 6 |
| Utilización nominal de los tornos (D12) | 40,43 ± 0,01 % |
| Tiempo medio de acceso (llegada a la cola → asiento) | 1,972 ± 0,008 min |
| Llegan antes del inicio y se sientan después | 4,578 ± 0,052 % |

**Cuello de botella.** En la punta (−30 a 0 min) llegan 910 pers/min y los 72
tornos atienden 978 pers/min: ρ = 0,93. Los vomitorios admiten 411 pers/min por
macrozona frente a los 245 que dejan pasar los tornos, de modo que, sin
conflictos de asiento, no limitan la entrada (cálculo analítico, apartado A2).
La verificación muestra que con ρ tan cerca de 1 pequeños cambios en la carga
tienen mucho efecto: con un 25 % más de tiempo de servicio (S1, ρ = 1,15) la
espera media pasa a 1,402 ± 0,050 min (n = 30, diferencia +1,217 ± 0,034 min).

**La entrada tardía no se debe sobre todo a la cola.** Con 4 tornos, donde la
espera es casi nula (0,016 ± 0,001 min), el porcentaje sigue siendo
3,754 ± 0,016 % (n = 183). La diferencia emparejada con X0 es de
−0,824 ± 0,048 puntos porcentuales (180 parejas). Interpretación: eliminar casi
toda la cola de X0 reduce la entrada tardía en menos de un punto; el resto se
explica por quienes llegan en los últimos minutos y por el recorrido hasta el
asiento. Los conflictos pesan poco: repitiendo X0 sin conflictos con las mismas
180 semillas (B, `docs/VALIDACION_T6.2.md`), la entrada tardía baja del 4,578 %
al 4,488 %, 0,090 ± 0,006 puntos, y el acceso de 1,972 a 1,941 min,
0,032 ± 0,001 min (n = 180).

**Hallazgo y supuestos.** Que los tornos sean el recurso más cargado y que la
espera sea corta con ρ = 0,93 se sigue de los parámetros. Las cifras absolutas
dependen del número de tornos por puerta (3, una hipótesis de la Parte 1 porque
el dato real no es público), del perfil de llegadas (hipótesis inspirada en F2)
y del tiempo de servicio, al que la espera es muy sensible.

**Limitaciones.**
* La utilización (40 %) promedia desde la apertura hasta el último control,
  unas dos horas, y no describe la carga de la punta; para eso sirve ρ.
* Los resultados agregados no permiten reconstruir la cola a lo largo del reloj.
* El indicador de la Parte 1 se llamaba «% entrada tardía por colas», pero su
  definición (llega antes de t = 0 y se sienta después) incluye también el
  recorrido y los conflictos. Se propone llamarlo «entrada tardía».

---

## P2 · ¿Cuántos tornos por puerta hacen falta para que el 95 % del público espere menos de 10 minutos?

**Respuesta.** Tres tornos por puerta, el valor actual, es el menor número
ensayado que cumple el objetivo: con 3 y con 4 todo el público espera menos de
10 minutos en todas las réplicas; con 2 no se alcanza el 95 % en ninguna.

**Cifras** (figura **P2**):

| Tornos por puerta | n | ρ | Espera < 10 min | Espera media (min) | P95 (min) | Entrada tardía |
|---|---|---|---|---|---|---|
| 2 (X1) | 30 | 1,40 | 88,96 ± 0,74 % | 4,016 ± 0,078 | 11,764 ± 0,266 | 20,30 ± 0,20 % |
| 3 (X0) | 180 | 0,93 | 100,0 % | 0,192 ± 0,008 | 1,150 ± 0,068 | 4,58 ± 0,05 % |
| 4 (X1) | 183 | 0,70 | 100,0 % | 0,016 ± 0,001 | 0,076 ± 0,002 | 3,75 ± 0,02 % |

* Con 2 tornos, el porcentaje que espera menos de 10 min va del 85,2 % al 92,4 %
  según la réplica (`kpis.csv`): ninguna de las 30 llega al 95 %. Frente a 3
  tornos, la espera media sube 3,832 ± 0,067 min, el porcentaje bajo 10 min cae
  11,04 ± 0,74 puntos y la entrada tardía sube 15,79 ± 0,19 puntos (30 parejas).
* Con 2 tornos la capacidad es menor que la demanda en la punta (ρ = 1,40) y la
  espera crece sin cota mientras dura, hasta unos 12 min; después la cola se
  vacía (apartado A2).
* Pasar de 3 a 4 tornos reduce la espera media en 0,176 ± 0,008 min (unos 11 s)
  y la entrada tardía en 0,82 ± 0,05 puntos (180 parejas), pero no cambia el
  cumplimiento del objetivo, que ya era del 100 %.

**Robustez (S1).** Con 3 tornos, el objetivo se mantiene en las variantes de S1:
con un 10 % más de público, 100,0 % (n = 73); con un 25 % más de tiempo de
servicio (ρ = 1,15), 99,931 ± 0,045 % (n = 30), aunque el P95 sube a
4,919 ± 0,211 min.

**Hallazgo y supuestos.** Que 2 tornos no basten y 3 sí es un hallazgo robusto
en el modelo: se sigue de ρ a un lado y otro de 1 y se mantiene en S1. El margen
de 3 tornos depende del tiempo de servicio y del perfil de llegadas, que son
hipótesis.

**Limitaciones.**
* Solo se han ensayado 2, 3 y 4 tornos por puerta, iguales en todas las puertas.
* El criterio se mide por partido simulado (porcentaje del público de cada
  réplica). Que se cumpla en las 180 réplicas no es una garantía para cualquier
  partido real.

---

## P3 · ¿Cuánto mejoran las esperas y las entradas tardías si parte del público adelanta su llegada?

**Respuesta.** Si un 30 % de quienes llegarían en los últimos 30 minutos adelanta
su llegada (perfil X2), la espera media baja de 11,5 a 3 segundos y la entrada
tardía baja casi a la mitad, del 4,6 % al 2,6 %.

**Cifras** (X2, n = 138; diferencias frente a X0 con 138 parejas; figura **P3**):

| Indicador | X0 | X2 | Diferencia X2 − X0 |
|---|---|---|---|
| Espera media (min) | 0,192 ± 0,008 | 0,050 ± 0,003 | −0,142 ± 0,009 |
| P95 de la espera (min) | 1,150 ± 0,068 | 0,209 ± 0,012 | −0,935 ± 0,078 |
| Máximo en la cola de una puerta | 135 ± 6 | 72 ± 5 | −63 ± 8 |
| Tiempo de acceso (min) | 1,972 ± 0,008 | 1,824 ± 0,003 | −0,149 ± 0,009 |
| Entrada tardía (%) | 4,578 ± 0,052 | 2,604 ± 0,014 | −1,970 ± 0,054 p. p. |

La utilización de los tornos no cambia (40,4 %): el trabajo es el mismo, solo
se reparte mejor en el tiempo. ρ en la punta baja de 0,93 a 0,81 (no a 0,65
como decía la Parte 1; apartado A1, 6.1).

**Interpretación.** La entrada tardía baja 1,97 puntos, más de lo que se gana al
eliminar casi toda la cola con 4 tornos (0,82 puntos, P1). Por tanto, la mayor
parte de la mejora viene de que menos gente llega en los últimos minutos, no de
la reducción de la cola. Esta lectura combina dos contrastes distintos y es una
inferencia, no una medida directa.

**Hallazgo y supuestos.** La dirección del efecto se sigue del modelo: repartir
las mismas llegadas en más tiempo reduce la carga en la punta. La magnitud
depende por completo del perfil X2, una hipótesis de la Parte 1 (un 30 % que
adelanta su llegada a la franja de −60 a −30 min) que no se ha calibrado con
datos.

**Limitaciones.**
* El modelo no representa cómo se conseguiría que el público llegue antes
  (incentivos, información) ni si un 30 % es alcanzable.
* La mejora absoluta de la espera es pequeña porque en X0 ya es corta; el efecto
  sería mayor en un escenario más cargado, que no se ha simulado.

---

## P4 · ¿Qué gana un colectivo priorizado (mayores y personas con movilidad reducida) y cuánto pierde el resto?

**Respuesta.** Con prioridad no expulsiva en los tornos (X3), mayores y personas
con movilidad reducida casi dejan de esperar (unos 11 s menos de media) y el
resto espera 1,5 s más; la espera media del conjunto no cambia.

**Cifras** (mismos colectivos en X0 y en X3, D32; X0 n = 180, X3 n = 181,
diferencias con 180 parejas; figura **P4**):

| Colectivo | X0 (FIFO) | X3 (prioridad) | Diferencia X3 − X0 |
|---|---|---|---|
| Mayores y PMR, espera media (min) | 0,192 ± 0,008 | 0,0108 ± 0,0001 | −0,181 ± 0,008 |
| Resto, espera media (min) | 0,192 ± 0,008 | 0,217 ± 0,009 | +0,0248 ± 0,0011 |

* En X3, la diferencia entre la espera de los priorizados y la del resto es de
  −0,206 ± 0,009 min (n = 181).
* La espera media de todo el público no cambia: +0,00006 ± 0,00007 min (el
  intervalo incluye el cero), ni la entrada tardía: +0,0005 ± 0,0028 puntos.
  La prioridad reordena la cola sin cambiar el trabajo de los tornos.
* La ganancia por persona priorizada (unos 11 s) es unas siete veces la pérdida
  por persona del resto (1,5 s), porque el colectivo priorizado es el 12 % del
  público.

**Hallazgo y supuestos.** Que la espera total no cambie y que el coste se
reparta entre muchos es una propiedad de la prioridad no expulsiva con
servicios iguales. Las magnitudes absolutas son pequeñas porque la espera de X0
es corta; con más carga la ganancia y la pérdida serían mayores, pero eso no se
ha simulado.

**Limitaciones.**
* La prioridad solo se aplica en el torno; no en el vomitorio ni en la salida.
* Se supone que el colectivo se identifica sin error ni coste al llegar a la
  puerta, y que no hay más personas acogidas a la prioridad que el 12 % del
  perfil.
* La movilidad reducida solo se representa con una velocidad menor (factor 0,5)
  en el recorrido; el tiempo de servicio en el torno es el mismo para todos.

---

## P7 · ¿Qué pasa si se cierra una puerta en hora punta? ¿Lo absorbe la redirección a las demás puertas de la macrozona?

**Respuesta.** Sí. Si la puerta A-1 se cierra 10 minutos al empezar la punta
(t = −30 min), quienes llegan a ella esperan de media unos 9,6 minutos sin
redirección y medio minuto con ella: la redirección a la puerta con menos cola
de la misma macrozona absorbe casi todo el efecto.

**Diseño.** Cierre de A-1 durante [−30, −20) min (D31; la Parte 1 decía +20, ver
apartado A1). Colectivo afectado: los asignados a A-1 que llegan durante el
cierre, 383,3 ± 5,6 de media sin redirección y 382,5 ± 2,7 con ella; con
redirección se redirigen todos.

**Cifras** (sin redirección n = 45, con redirección n = 199; diferencias con 45
parejas; figura **P7**):

| Indicador | Sin redirección | Con redirección | Diferencia con − sin |
|---|---|---|---|
| Espera media del colectivo afectado (min) | 9,626 ± 0,120 | 0,543 ± 0,026 | — |
| Espera media de todo el público (min) | 0,403 ± 0,018 | 0,243 ± 0,009 | −0,160 ± 0,007 |
| Máximo en la cola de una puerta | 395 ± 7 | 140 ± 6 | −258 ± 13 |
| Entrada tardía (%) | 5,247 ± 0,108 | 4,645 ± 0,052 | −0,650 ± 0,029 p. p. |
| Público que espera < 10 min (%) | 99,717 ± 0,143 | 100,0 | +0,283 ± 0,143 |

* Sin redirección, quien llega al cerrar espera casi todo el cierre, y quien
  llega después espera menos pero se encuentra la cola acumulada. La espera
  media observada (9,63 min) coincide con la del modelo fluido (9,66; apartado
  A2).
* Con redirección, las otras cinco puertas de la macrozona reciben un 20 % más
  de llegadas durante 10 minutos, con una holgura que lo permite (ρ = 0,93). Las
  colas de esas puertas crecen poco y la espera de los afectados se queda en
  medio minuto.
* La redirección mitiga el cierre, pero no lo hace invisible: frente a X0 sin
  cierre, la espera media de todo el público con redirección es
  +0,050 ± 0,003 min mayor (diferencia emparejada, 180 parejas; calculada por C
  a partir de `kpis.csv`).
* El efecto se ve en el colectivo afectado y en la cola máxima, no en las medias
  globales: el cierre afecta a 1 de las 24 puertas.

**Hallazgo y supuestos.** Que la redirección absorba el cierre es un hallazgo
del modelo en estas condiciones: hay holgura en las demás puertas en la punta.
La magnitud depende de supuestos que la favorecen: información perfecta e
instantánea sobre las colas y ningún recorrido adicional.

**Limitaciones.**
* **D23.** El cierre solo afecta a quien llega mientras dura; quien ya estaba en
  la cola de A-1 sigue siendo atendido. A −30 apenas hay cola formada (en el
  estudio previo, 0 o 2 personas frente a unas 380 llegadas), así que la
  hipótesis casi no influye. Con cierres más tardíos (−20, −10) llegaba a haber
  unas 100 personas en cola al cerrar, y la alternativa daría un efecto mayor
  (`docs/ESTUDIO_X6.md`).
* **Redirección optimista.** Quien llega a la puerta cerrada conoce al instante
  la cola de todas las demás, elige la menor y no camina ninguna distancia extra,
  porque el modelo no representa el exterior. En la realidad la redirección
  costaría tiempo de desplazamiento y no sería perfecta.
* **Un solo caso.** Se ha estudiado una puerta, una duración (10 min) y un
  instante. A +20, el instante de la Parte 1, el cierre no tenía efecto
  apreciable (estudio previo con 5 réplicas).
* Sin redirección hay 45 réplicas, frente a 199 con ella (tamaños por precisión,
  D34); el intervalo de la diferencia usa las 45 parejas comunes.

---

## Cruces con B y C

Lo que este texto da por supuesto de los otros roles:

**B (estadio, salida, evacuación, I1, I4)**
* La entrada tardía y el tiempo de acceso (P1, P3) incluyen el paso por el
  vomitorio y los conflictos de asiento, que son de B. B ha medido el peso de
  los conflictos en X0 (0,090 ± 0,006 puntos de entrada tardía, n = 180).
* La afirmación de que los vomitorios no son cuello de botella «sin conflictos»
  (P1) es analítica; con conflictos, la respuesta es de B (P6).
* P7 supone que el proceso de cierre (`gate_closure_process`, de B) cierra A-1
  en t = −30 y la reabre en t = −20, y que despierta en orden a quienes esperan.
* El modelo de cola usado en P7 y la verificación de A no cubren la salida ni
  la evacuación: los 7,7, 5,9 y 7,1 min de la Parte 1 los contrasta B.

**C (métricas, runner, análisis, figuras)**
* Definiciones de indicadores (`docs/CONTRATOS.md`): porcentaje con espera
  menor de 10 min por réplica, P95 por réplica, cola máxima por puerta usada,
  utilización D12 y entrada tardía.
* Colectivos comunes de P4 en X0 y X3 (D32, `groups.csv`) y colectivo afectado
  de P7 (`audit.csv`, columnas `closure_*`).
* Intervalos t de Student, emparejamiento por semilla y tamaños por precisión
  (D29, D34): la sección de método de C debe explicarlos, porque este texto
  solo los cita.
* Figuras P1–P4 y P7 de `results/figures`.
* El contraste emparejado X6 con redirección − X0 (P7) lo calcula C, porque no
  está en `comparisons.csv`, cuya referencia de X6 es sin redirección.

# C3. Síntesis de resultados y conclusiones

Esta sección reúne las respuestas de A y B para cerrar la memoria conjunta. No
sustituye sus apartados de implementación y resultados. Las cifras son del modelo
con los parámetros ensayados y las diferencias con IC se emparejan por semilla.

## 1. Respuesta a las preguntas del estudio

**P1. Operativa actual.** Con tres tornos por puerta, la espera media es
0,1923 ± 0,0084 min y el P95 medio, 1,1497 ± 0,0685 min. La cola máxima de una
puerta tiene media 135,07 personas y la utilización nominal media es 40,43 %.
Ese promedio no descarta presión en la punta, cuya carga analítica es 0,93.
El tiempo de acceso, unos 1,972 min, incluye también la marcha y el asiento; el
4,578 % de entrada tardía no puede atribuirse exclusivamente a la cola del torno.

**P2. Número de tornos.** Dos tornos por puerta no alcanzan el objetivo de que
el 95 % espere menos de diez minutos: el porcentaje medio es
88,9583 ± 0,7353 %. Con tres y cuatro se observa 100 % en la campaña. Tres es
el menor número de los ensayados que satisface el objetivo observado, bajo el
perfil y tiempos de servicio del caso base. La carga superior a uno con dos
tornos explica que la cola crezca durante la punta; después se vacía.

**P3. Llegadas anticipadas.** La espera media baja a 0,0504 ± 0,0025 min y la
entrada tardía a 2,6045 ± 0,0145 %. La diferencia emparejada de espera respecto
a X0 es -0,1418 ± 0,0093 min (138 parejas). Anticipar reduce la concentración de
la demanda sin añadir capacidad, aunque persisten recorrido y conflictos.

**P4. Prioridad.** Los colectivos mayores y PMR pasan de una espera media de
aproximadamente 0,1922 min en FIFO a 0,0108 min con prioridad. El beneficio
emparejado es -0,1814 ± 0,0083 min; el coste en el resto es
+0,0248 ± 0,0011 min, unos 1,5 s (180 parejas). Hay una redistribución de las
esperas, no una ampliación de la capacidad. Los mismos colectivos se utilizan
en ambos escenarios, evitando comparar poblaciones distintas.

**P5. Salida escalonada.** Retrasar tres minutos la liberación de la grada
superior reduce la media del máximo en una salida de unas 1.460 a 746 personas.
La reducción emparejada es 713,878 ± 0,573 personas, a cambio de aumentar el
vaciado total 1,224 ± 0,105 min (180 parejas). La medida mejora la concentración
de cola, pero no el instante de la última salida. Los máximos incluyen a quien
está cruzando y no suman toda la cola del estadio.

**P6. Acomodadores.** Con probabilidad de conflicto del 1 %, la duración media
I1, incluida la espera al acomodador, es 44,600 / 13,744 / 6,644 min con
3 / 6 / 9 acomodadores por zona. El contraste de retraso en otros espectadores
del bloque es aproximadamente 291,726 / 36,839 / 6,667 s/persona, respectivamente;
no debe confundirse con la duración I1. Tres produce una fuerte acumulación y
nueve mejora notablemente la situación, pero no elimina toda la cola ni demuestra
un mínimo óptimo. La resolución individual mantiene media teórica 4,667 min;
una duración total mayor no contradice su distribución, porque incorpora espera.

**P7. Cierre y redirección.** Con cierre de A-1 durante [-30,-20) min, la
espera media de las personas asignadas a esa puerta que llegan durante el cierre
es 9,626 min sin redirección y 0,543 min con ella. Son muestras distintas de
45 y 199 réplicas. La diferencia global emparejada (con redirección menos sin redirección)
es -0,1596 ± 0,0072 min en 45 parejas. La redirección mitiga el cierre,
pero no lo hace invisible frente a X0: con redirección menos X0, la diferencia
global es +0,04989 ± 0,00346 min (180 parejas). Este último contraste se ha
calculado para la memoria sin modificar las referencias oficiales de T5.3.
La elección inmediata de otra puerta sin desplazamiento exterior hace que el
resultado sea optimista respecto a una redirección real.

**P8. Evacuación.** Con todas las salidas, el vaciado medio es
7,4694 ± 0,0516 min; con una bloqueada, 8,4200 ± 0,0140 min (180 réplicas por
variante). El vaciado completo en ocho minutos se observa en 163/180 partidos
sin bloqueo y 0/180 con bloqueo. Una media inferior al plazo no garantiza cumplir
en cada réplica. B comprobó que, en las 17 superaciones sin bloqueo, llega después
del plazo una única persona con movilidad reducida y sin cola apreciable: el
recorrido lento más la reacción explican el incumplimiento. La lectura es distinta
de la variante bloqueada, donde la cola limita la evacuación. No se ha simulado
un dispositivo de asistencia; su eficacia no se puede dar por demostrada.

## 2. Cambios y aclaraciones respecto a la Parte 1

El guion pide identificar cualquier diferencia con el diseño inicial. En la
memoria conjunta deben conservarse las siguientes explicaciones:

| Cambio o aclaración | Justificación y efecto |
|---|---|
| X6: cierre de +20 a -30 min (D31) | La pregunta trata la hora punta. Se mantienen puerta y duración; los resultados finales usan -30 y los antiguos son históricos. |
| X5: añadir nueve acomodadores (D33) | Se conservan tres y seis, el 1 % y Triangular(1,3,10). Se amplía el diseño para estudiar la acumulación sin ajustar parámetros para mejorar el resultado. |
| Número de réplicas (D34) | Se pasa de la previsión aproximada de treinta a tamaños de 30-247 por escenario, según la precisión verificada. |
| Carga anticipada 0,81 | Corrige el 0,65 de la Parte 1: el pico real está entre -45 y -30. No cambia el modelo. |
| Cierre y cola existente (D23) | Solo afecta a quienes llegan durante el cierre; las personas ya en cola siguen su curso. |
| Recuento I3 (D25) | Incluye todas las averías registradas, también las posteriores a la entrada; no equivale a averías que afectaron a alguien. |
| Prioridad y relectura | La prioridad no expulsa controles en curso y la relectura no libera el torno. Son concreciones de implementación. |

Los tiempos de 7,7 min de salida y 5,9/7,1 min de evacuación son referencias de
capacidad de una macrozona. Los tiempos del partido completo incluyen también
recorridos, reacción y los repartos aleatorios de público. No se ajustan los
parámetros para obligar a que ambos tipos de tiempo coincidan.

## 3. Límites y validez de las conclusiones

La verificación interna comprueba conservación, orden, capacidades, casos límite,
cálculos de indicadores y reproducibilidad. No hay datos completos observados
de colas, salida y evacuación que permitan cuantificar el error respecto al
estadio real. El estudio sirve para comparar políticas bajo las hipótesis
especificadas, con esa limitación de validación externa.

El criterio de precisión controla la incertidumbre muestral de la espera media.
No controla el error de los parámetros, la representación espacial o las reglas
de comportamiento. Las decisiones se estudian con perfiles, probabilidades y
recursos concretos: no cabe generalizar que tres tornos basten para cualquier
demanda o que nueve acomodadores sean siempre suficientes.

Las condiciones del exterior no están representadas y la redirección no añade
marcha ni información imperfecta. Las personas tienen velocidades y distancias
sorteadas, sin un modelo detallado de densidad, empujes o asistencia. Estas
simplificaciones afectan a la interpretación de P7 y P8. El indicador de retraso
I1 es un contraste entre poblaciones expuestas y no expuestas del modelo, no una
medición causal individual del mismo espectador con y sin conflicto.

S1 cambia cada factor por separado y no incluye emergencia. No responde a
combinaciones de aforo, servicio y velocidad ni a medidas de evacuación asistida.
La frecuencia observada de vaciados en plazo se presenta como conteo; no se
convierte en una garantía operacional.

El ritmo de tornos se contrasta con los parámetros documentados en la Parte 1.
La comprobación directa con la fuente F2 sigue sin realizarse, como reconoce A
en T6.2; no debe presentarse en la memoria como validación independiente de ese
artículo. Se mantiene la referencia bibliográfica de la Parte 1 sin atribuirle
nuevas comprobaciones.

## 4. Conclusión general

En el modelo estudiado, la entrada con tres tornos por puerta satisface el
objetivo de espera ensayado, y anticipar llegadas reduce esperas y entradas
tardías. La prioridad beneficia a mayores y PMR con un coste pequeño para el
resto. En la salida, escalonar reduce la cola máxima a costa de alargar el
vaciado. La disponibilidad de acomodadores resulta decisiva al duplicar la
probabilidad de conflicto, mientras que redirigir reduce el efecto del cierre
de una puerta en punta. La evacuación exige distinguir capacidad y marcha de
personas lentas; el promedio de vaciado por sí solo no responde a la referencia
de ocho minutos. Estas conclusiones deben acompañarse de los IC, los tamaños
por escenario y los límites indicados.

Fuentes: tablas definitivas y `docs/RESULTADOS_T5.3.md`; figuras T6.1;
`docs/VERIFICACION.md`, `docs/VALIDACION_T6.2.md` (diagnóstico de B sobre P8) y
`docs/VERIFICACION_C_T6.2.md`. El contraste adicional de P7 usa las columnas
`scenario`, `seed` y `wait_mean_min` de `results/final/kpis.csv`.

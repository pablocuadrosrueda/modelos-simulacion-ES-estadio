# B3: Respuestas a P5, P6 y P8

Autor: Pablo Pérez Molina (rol B). Texto final para la memoria de la Parte 2. P7, el cierre de puerta, se responde en A3. Las figuras son las de results/figures; en la memoria en Word conviene usar los PNG.

## Respuestas

Los resultados proceden de las réplicas definitivas: 180 por escenario. Se da la
media de las réplicas y, entre paréntesis, la semianchura del intervalo de
confianza del 95 %.

### P5. ¿Reduce las colas en las salidas que la grada superior salga más tarde?

Sí. Con la salida escalonada, la cola máxima en las salidas baja de 1.460 a 746
personas, casi la mitad. A cambio, el estadio tarda 1,22 min (0,11) más en
vaciarse: de 8,37 a 9,59 min. La salida escalonada reparte la carga en el tiempo
y conviene si lo que preocupa es la aglomeración en las salidas, no el tiempo
total de vaciado.

![P5: salida escalonada](../../results/figures/P5.png)

### P6. ¿Cuánto retrasan los conflictos por asiento y cuántos acomodadores hacen falta?

Con conflictos al 1 % hay unos 490 conflictos por partido, unos 122 por
macrozona, concentrados en la hora punta. Cada uno ocupa a un acomodador una
media de 4,67 min, así que el número de acomodadores es decisivo:

| Acomodadores por macrozona | Duración media de un conflicto | Retraso al resto del bloque | Entrada tardía |
| --- | --- | --- | --- |
| 3 | 44,6 min (0,5) | 292 s por persona | 14,5 % |
| 6 | 13,7 min (0,2) | 37 s por persona | 7,2 % |
| 9 | 6,6 min (0,1) | 7 s por persona | 5,1 % |

Con 3 acomodadores el sistema se satura: los conflictos esperan mucho más de lo
que tardan en resolverse y, en el peor caso observado, el último espectador se
sienta casi tres horas después del inicio del partido. Con 6 todavía se forma
cola. De los tres niveles probados, solo con 9 la duración de un conflicto se
acerca a la de la propia resolución.

![P6: acomodadores y conflictos](../../results/figures/P6.png)

### P8. ¿Se evacúa el estadio en menos de 8 min? ¿Y con una salida bloqueada?

Con todas las salidas, el vaciado dura de media 7,47 min (0,05) y se cumple el
límite de 8 min en 163 de las 180 réplicas. En las 17 restantes solo llega tarde
una persona de movilidad reducida que camina despacio y está lejos de la salida:
la capacidad de las salidas sí basta, y el riesgo está en evacuar a tiempo a las
personas con movilidad reducida.

Con una salida bloqueada, el vaciado dura de media 8,42 min (0,01) y no se cumple
el límite en ninguna réplica. En este caso sí falla la capacidad: las 5 salidas
restantes no dan abasto. Aun así, a los 8 min ya está a salvo el 98,56 % de
las personas que evacúan.

Estos tiempos son mayores que los 5,9 y 7,1 min de la validación porque incluyen
el tiempo de reacción y la marcha hasta la salida, que la validación excluía a
propósito para medir solo el paso por las salidas.

![P8: evacuación](../../results/figures/P8.png)

# B2: Verificación y validación del asiento, la salida y la evacuación

Autor: Pablo Pérez Molina (rol B). Texto final para la memoria de la Parte 2. La verificación de la entrada y de la capacidad de los tornos está en A2; la del cálculo de indicadores y de la campaña de réplicas, en la parte de C.

## Contraste con la Parte 1

Además de las pruebas automáticas de cada componente, se ha comprobado que el
modelo reproduce los cálculos de capacidad de la Parte 1. Para aislar el paso
por las salidas, la prueba usa una macrozona de 12.195 personas que llegan
juntas, con 1 m de recorrido y 1 s de reacción.

| Caso | Salidas | Paso por persona | Parte 1 | Modelo |
| --- | --- | --- | --- | --- |
| Salida ordinaria | 6 de 4 m | 0,227 s | 7,7 min | 7,7 min |
| Evacuación | 6 de 5,2 m | 0,175 s | 5,9 min | 5,9 min |
| Evacuación con una salida bloqueada | 5 de 5,2 m | 0,175 s | 7,1 min | 7,1 min |

Las pruebas comprueban también que ningún recurso supera su capacidad: nunca hay
más de 8 personas en un vomitorio, un conflicto retiene su plaza, cada macrozona
usa solo sus acomodadores y cada salida deja pasar una persona cada 0,227 s.
También se comprueba el orden de los sucesos de cada espectador: fin del control,
llegada al vomitorio, asiento y salida.

Por último, dos casos límite con el estadio completo confirman la lectura de los
resultados de P6 y P8:

* Con acomodadores prácticamente ilimitados, la duración media de un conflicto
  baja a 4,62 min, la media teórica de la resolución (4,67 min). Por tanto, la
  saturación observada con 3 acomodadores se debe a que faltan acomodadores, no
  a un error del modelo.
* En las réplicas de evacuación con todas las salidas que no vacían en 8 min,
  solo llega tarde una persona, siempre de movilidad reducida y sin hacer cola
  en la salida. Sin ese colectivo, el vaciado nunca pasa de 7,36 min.

## Peso de los conflictos en la entrada tardía del escenario base

En el escenario base, con conflictos al 0,5 % y 6 acomodadores por macrozona, el
4,46 % de quienes llegan antes del inicio se sienta después. Repitiendo las 20
primeras réplicas con los mismos números aleatorios pero sin conflictos, ese
porcentaje baja al 4,38 %: los conflictos solo aportan 0,08 puntos (0,01), y el
tiempo medio de acceso apenas cambia (de 1,96 a 1,93 min). En el escenario base,
por tanto, la entrada tardía se debe casi por completo a la llegada en los
últimos minutos y al recorrido hasta el asiento, no a los conflictos.

# B1: Modelo implementado: asiento, conflictos, cierre de puerta, salida y evacuación

Autor: Pablo Pérez Molina (rol B). Texto final para la memoria de la Parte 2, sin referencias internas, para que encaje en el índice común. Los cambios de diseño comunes respecto a la Parte 1 (instante del cierre de puerta, nivel de 9 acomodadores y número de réplicas) se explican en el apartado de desviaciones de A1.

## Implementación de la ubicación en el asiento

Una vez supera el control de acceso, cada espectador se dirige al vomitorio de
su bloque, lo atraviesa y ocupa su asiento. Cada macrozona tiene 10 bloques, y
cada bloque un vomitorio con 8 plazas que se atienden por orden de llegada. Los
bloques 1 a 5 forman la grada inferior y los bloques 6 a 10 la superior.

El recorrido desde la puerta hasta el asiento mide entre 60 y 180 m, y cada
espectador lo hace a su propia velocidad: una normal de media 1,45 m/s y
desviación típica 0,23 m/s, truncada entre 0,6 y 2,2 m/s, multiplicada por 0,8
en las personas mayores y por 0,5 en las de movilidad reducida. Al llegar al
vomitorio espera plaza, si hace falta, y lo atraviesa en un tiempo
Triangular(5, 10, 20) s. Al salir se sienta. Se considera entrada tardía la de
quien llega antes del inicio del partido y se sienta después.

## Conflicto por asiento

Al llegar a su asiento, un espectador puede encontrarlo ocupado. Ocurre con
probabilidad 0,5 % en el escenario base y 1 % en el experimento de acomodadores.
Mientras dura el conflicto, el espectador no suelta su plaza del vomitorio:
pide un acomodador de su macrozona, espera a que quede uno libre si están todos
ocupados, y el conflicto se resuelve en un tiempo Triangular(1, 3, 10) min desde
que llega el acomodador. Cada macrozona tiene 6 acomodadores en el escenario
base.

Retener la plaza del vomitorio es lo que hace que un conflicto retrase también
al resto del bloque: con varios conflictos a la vez, el vomitorio pierde plazas
y quienes vienen detrás esperan más. Este efecto es el que mide la pregunta P6.

## Cierre de puerta

La puerta 1 de la macrozona A se cierra durante 10 min. Mientras está cerrada
nadie entra por ella. Quien llega a esa puerta se dirige a la puerta abierta de
su macrozona con menos cola, si la redirección está activa, o espera a que
reabra, si no lo está. Quienes esperan la reapertura entran después en el mismo
orden en que llegaron. Quien ya estaba en la cola de esa puerta cuando se cierra
sigue siendo atendido.

## Salida ordinaria

Al final del partido, en el minuto 105 (90 de juego y 15 de descanso), el
público abandona el estadio. Cada macrozona tiene 6 salidas de 4 m. Con una
capacidad de 66 personas por metro y minuto, cada salida deja pasar 264 personas
por minuto, es decir, una persona cada 0,227 s.

Cada espectador vuelve a recorrer la misma distancia que en la entrada y, al
llegar a la zona de salidas, elige la salida de su macrozona con menos personas
en ese momento. Se han simulado dos políticas: la salida simultánea, en la que
todo el público sale en el minuto 105, y la salida escalonada, en la que la grada
superior sale 3 min después que la inferior.

## Evacuación de emergencia

En el experimento de emergencia suena una alarma en el minuto 40 del partido. En
ese instante se cierran los accesos, las salidas se ensanchan un 30 % (de 4 a
5,2 m, una persona cada 0,175 s) y cada espectador actúa según dónde está:

* Quien aún no ha llegado al estadio ya no llega y no cuenta en la evacuación.
* Quien está en la cola de fuera, o pasando el torno, abandona y tampoco cuenta.
* Quien ya ha pasado el torno, esté caminando, en el vomitorio o sentado,
  evacúa: espera su tiempo de reacción, Triangular(30, 60, 120) s, camina un
  20 % más rápido hasta la salida de su macrozona con menos cola y la atraviesa.

En la variante con una salida bloqueada, una de las 6 salidas de la macrozona A
queda inutilizada y su público se reparte entre las otras 5.

## Números aleatorios comunes

Para comparar escenarios con menos réplicas, todos los escenarios usan los
mismos números aleatorios con la misma semilla. Para conseguirlo, cada variable
aleatoria propia de un espectador se sortea al empezar la réplica, para todos a
la vez, y queda asociada a ese espectador: el paso por el vomitorio, si tiene
conflicto y cuánto dura, el desempate entre salidas igual de cargadas y el
tiempo de reacción a la alarma.

Si estos valores se sortearan durante la simulación, el número que le tocara a
cada espectador dependería del orden en que el modelo lo atiende, y ese orden
cambia de un escenario a otro. Con el sorteo previo, la diferencia entre dos
escenarios se debe solo a lo que cambia en ellos. Por ejemplo, las tres
variantes del experimento de acomodadores tienen exactamente los mismos
conflictos en cada réplica.

## Hipótesis adoptadas

La Parte 1 no precisaba algunos aspectos de esta parte del modelo. En cada uno
se ha elegido la opción más sencilla y fiel al enunciado:

* **Distancia en la evacuación.** Quien está caminando hacia su asiento cuando
  suena la alarma recorre la distancia completa hasta la salida, como si
  saliera desde el asiento. No se conoce su posición exacta en el recorrido y
  la distancia completa es el caso más desfavorable.
* **Cola exterior al sonar la alarma.** Quien está fuera, en cola o pasando el
  torno, abandona y no cuenta en la evacuación, porque la alarma cierra los
  accesos.
* **Salida bloqueada.** Se bloquea la salida 1 de la macrozona A. La Parte 1
  habla de una salida de esa macrozona sin concretar cuál; como las 6 son
  iguales, la elección no cambia el resultado.
* **Elección de salida.** El espectador elige la salida al llegar a ella y no
  al levantarse, porque es entonces cuando ve las colas.
* **Conflicto en curso al sonar la alarma.** Se da por terminado en ese momento:
  el espectador deja el asiento para evacuar.
* **Cierre de puerta.** Solo afecta a quien llega mientras la puerta está
  cerrada; quien ya estaba en su cola sigue siendo atendido.

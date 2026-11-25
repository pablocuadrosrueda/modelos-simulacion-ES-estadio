# A1 · Modelo implementado: llegadas, entrada e incidencias del torno

> Borrador del rol A (Pablo Cuadros) para la memoria de la Parte 2 (T6.3).
> Módulos descritos: `config`, `rng`, `entities`, `arrivals` y `entry`. El asiento,
> la salida, la evacuación, I1 e I4 son de B; el runner, las métricas y el análisis,
> de C. Las referencias «Dn» remiten a `docs/DECISIONES.md`.

## 1. Organización general

El modelo se ha implementado en Python 3 con SimPy, como preveía la Parte 1
(§4.5). Cada réplica es un partido completo: empieza con la apertura de puertas
en t = −90 min y termina cuando sale (o queda a salvo) el último espectador. El
reloj de SimPy está en segundos con t = 0 en el inicio del partido; los
resultados se expresan en minutos respecto a ese instante (D6).

Todos los parámetros están en un fichero de configuración JSON
(`configs/base.json`). Cada experimento declara solo lo que cambia respecto a la
base (D3), lo que hace explícito el principio de la Parte 1 de «cambiar un solo
factor» (§5.1). La carga valida la configuración y rechaza claves desconocidas,
de modo que un error tipográfico no produce en silencio un escenario distinto
del previsto. Ningún parámetro del modelo está escrito en el código.

Cada espectador es un proceso SimPy único que recorre entrada, asiento,
permanencia y salida, y que la alarma puede interrumpir para pasar a la
evacuación. Al terminar, la réplica devuelve una fila por espectador con todos
sus instantes; los indicadores se calculan después a partir de esas filas.

## 2. Generación de espectadores y llegadas

En E0 se generan los N = 48.775 espectadores con todos sus atributos iniciales:

* **Hora de llegada.** Se sortea la franja de 15 min con las probabilidades del
  perfil activo (base o anticipado, tabla de la Parte 1, §4.3) y un instante
  uniforme dentro de ella. Los espectadores se ordenan por hora de llegada, de
  modo que su identificador crece con ella (D16).
* **Macrozona, puerta y bloque.** Macrozona con el reparto de la configuración
  (25 % cada una) y, dentro de ella, puerta (1–6) y bloque (1–10) uniformes. La
  grada (inferior o superior) se deduce del bloque.
* **Grupo.** Estándar (88 %), mayores (10 %) o personas con movilidad reducida
  (2 %), con su factor de velocidad (1; 0,8; 0,5).
* **Velocidad, distancia y servicio.** Velocidad Normal(1,45; 0,23) m/s truncada
  en [0,6; 2,2] (por inversión de la función de distribución, sin rechazo) y
  multiplicada por el factor del grupo; distancia Uniforme(60, 180) m; tiempo de
  servicio en el torno Triangular(2, 4, 6) s.

Cada atributo sale de su propio generador de números aleatorios (§4 de este
apartado), y todos se sortean de forma vectorizada.

## 3. Entrada: colas, tornos y prioridad

Cada puerta es un `simpy.PriorityResource` con tantas plazas como tornos (3 en
la base). Con ello se cumplen los requisitos RF03 y la implementación prevista en
la Parte 1 (§4.5). El proceso de entrada de cada espectador:

1. Espera hasta su hora de llegada (E1).
2. Elige puerta con `choose_gate` (apartado 3.1).
3. Pide un torno y espera su turno (E2). La espera en cola es
   `t_inicio_control − t_llegada`.
4. Ocupa el torno durante su tiempo de servicio y, si le toca, la relectura de
   I2 (E3). Después sigue hacia el vomitorio (módulo de B).

**Disciplina de cola (D20).** Con `fifo`, todos piden con el mismo nivel. Con
`priority` (X3), mayores y PMR piden con un nivel más alto y adelantan a los
demás en la cola de su puerta. La prioridad **no es expulsiva**: nunca
interrumpe un control ya iniciado (Parte 1, §1.3). Dentro de cada nivel se
mantiene el orden de llegada. Hay un tercer nivel, aún más alto, reservado para
las averías (I3).

### 3.1. Elección de puerta y cierre de puerta

`choose_gate` se evalúa una sola vez, al llegar, con el estado de ese instante
(D23):

* Si la puerta asignada está abierta, el espectador va a ella.
* Si está cerrada y la redirección está activa, va a la puerta abierta de su
  macrozona con menos cola. Se desempata por número de personas en servicio y,
  después, por número de puerta. Es una regla determinista, sin azar.
* Si está cerrada y no hay redirección (o no queda ninguna puerta abierta en su
  macrozona), espera a que reabra y entra después por su puerta, conservando el
  orden de llegada (D13).

Quien se redirige no recorre ninguna distancia adicional, porque el modelo no
representa el exterior del estadio (Parte 1, §1.3). El proceso que cierra y
reabre la puerta (I4) es de B; la puerta realmente usada se guarda en
`gate_used`, que puede diferir de la asignada.

## 4. Incidencias del torno: I2 e I3

Ambas actúan sobre el torno y por eso se implementaron en el módulo de entrada
(D8).

**I2 · Fallo de lectura (D26).** Con probabilidad 3 %, al terminar el servicio
la entrada se vuelve a leer durante Uniforme(5, 15) s más, **sin liberar el
torno**. La relectura no interrumpe ni es interrumpida. Cada relectura queda
registrada como incidencia con la puerta, el espectador y sus instantes.

**I3 · Avería de torno (D22).** Cada torno tiene su propio proceso, que alterna
periodos de funcionamiento Exponencial(media 240 min) y reparaciones
Uniforme(3, 10) min. El tiempo entre fallos se mide **en funcionamiento**: el
reloj se detiene durante la reparación, de modo que 240 min es el tiempo medio
de buen funcionamiento y un torno no puede averiarse mientras está parado. Al
vencer ese tiempo, la avería pide una plaza del recurso con la prioridad máxima
y sin expulsión: el torno termina el servicio en curso y después se para (Parte
1, §3.2, «cuando el torno queda libre»). La avería adelanta a toda la cola,
incluidos los grupos priorizados de X3.

## 5. Números aleatorios comunes

La Parte 1 pide mismas semillas en todos los escenarios (§5.3) y un generador
independiente por fuente de azar (§4.5). La implementación va un paso más allá,
porque las mismas semillas no bastan si los números se asignan en distinto orden:

* **Un generador por fuente (D2).** `RngStreams(semilla)` da un generador de
  NumPy para cada una de las 13 fuentes (llegadas, asignación, grupo, velocidad,
  distancia, servicio, I2, vomitorio, I1, I3, elección de salida, reacción y
  desempate de puerta), derivado de la semilla y de la posición fija de la
  fuente. Consumir más o menos números de una fuente no altera las demás.
* **Todo sorteo por espectador se hace en E0 (D17).** Si el servicio o la
  relectura se sortearan dentro del proceso, con un generador compartido, cada
  número caería en un espectador distinto según el orden en que el modelo los
  atiende, y ese orden cambia entre escenarios (por ejemplo, con 2 o 4 tornos).
  Por eso servicio, relectura I2 y su duración (D26), paso por el vomitorio
  (D18), conflicto I1 y su resolución (D21) y tiempo de reacción a la alarma
  (D28) se sortean una vez por espectador, al empezar la réplica. Además, el
  sorteo de I1 e I2 se hace comparando un uniforme con la probabilidad: al
  pasar de 0,5 % a 1 % (X5) los conflictos de la base se conservan y solo se
  añaden otros.
* **Un generador por torno para I3 (D22).** El calendario de averías del torno
  A-G1-T1 es el mismo con 2, 3 o 4 tornos por puerta y no depende de las demás
  macrozonas.
* **Semilla de cada réplica (D11):** `20261105 + nº de réplica`, igual en todos
  los escenarios.

El efecto se comprueba en los datos definitivos (apartado A2): cuando un
escenario no modifica la entrada (X4, X5, X7, S1 de velocidad), sus indicadores
de entrada son idénticos a los de X0 semilla a semilla, y el número de
relecturas coincide también en X1, X2, X3 y X6.

## 6. Desviaciones respecto a la Parte 1

Ninguna desviación cambia la lógica descrita en la Parte 1 salvo las indicadas
expresamente. Se distinguen tres tipos: correcciones de la Parte 1, cambios de
diseño decididos por el grupo e hipótesis que la Parte 1 no precisaba.

### 6.1. Correcciones de la Parte 1

**ρ del perfil anticipado (X2): 0,81, no 0,65 (§4.3).** La Parte 1 calculó ρ con
la franja de −30 a −15 min (19,6 %, 637 pers/min). Pero la franja más cargada del
perfil anticipado es la de −45 a −30 min (24,4 %, 793 pers/min), y con ella
ρ = 793 / 978 ≈ 0,81. El modelo y los parámetros no cambian; solo el número del
texto. Los datos definitivos lo confirman: la espera media de X2 queda entre la
del escenario con ρ = 0,70 y la del escenario con ρ = 0,84 (apartado A2).

**Redacción del caso de 2 tornos (§4.3).** «La cola crece sin parar» solo es
cierto mientras dura la punta con ρ > 1 (de −30 a 0 min). Después la cola se
vacía y todos entran. Se propone: «la cola crece sin cota durante la punta».

### 6.2. Cambios de diseño decididos

**D31 · Cierre de puerta en t = −30 min (la Parte 1 decía +20).** P7 pregunta por
un cierre «en hora punta», pero en t = +20 llega solo el 2 % del público. Un
estudio previo con 5 réplicas y semillas comunes (`docs/ESTUDIO_X6.md`) probó
seis instantes: con el cierre a +20 la diferencia sin − con redirección en la
espera media de los asignados a la puerta cerrada era de 4 ± 1 s, de modo que X6
no respondía a la pregunta. A −30, comienzo de la franja de máximas llegadas, la
diferencia es de 292 ± 24 s, la mayor de las probadas, y no hay cola formada al
cerrar, así que la hipótesis D23 no influye. Se mantienen la puerta (A-1) y la
duración (10 min).

**D33 · X5 con nueve acomodadores.** La Parte 1 preveía 3 y 6 acomodadores por
macrozona. Se conservan la probabilidad de conflicto del 1 % y la resolución
Triangular(1, 3, 10) min, y se añade un tercer nivel de 9 acomodadores. Con 3
la cola de conflictos se satura, y ese resultado se mantiene como respuesta a P6
en lugar de ajustar los parámetros. Su análisis es de B.

**D34 · Tamaño de muestra por precisión.** La Parte 1 preveía unas 30 réplicas
por escenario (§5.3). El piloto de 10 réplicas, con el criterio de la propia
Parte 1 (IC del 95 % con semianchura ≤ 5 % de la espera media), estimó tamaños
muy distintos según el escenario. La campaña definitiva usa al menos 30 réplicas
y el tamaño estimado de cada escenario, y comprueba la precisión al terminar:
2.965 réplicas en 19 escenarios, entre 30 y 247 por escenario, con una
semianchura relativa máxima del 4,9865 % (`docs/RESULTADOS_T5.3.md`). La
precisión se fijó para la espera media, no para cada indicador. Su análisis es
de C.

### 6.3. Hipótesis que la Parte 1 no precisaba

**D23 · A quién afecta el cierre de puerta (hipótesis del grupo, conservada).**
El cierre afecta solo a quien **llega** mientras dura. Quien ya estaba en la
cola o en un torno de esa puerta sigue siendo atendido. Es la lectura literal de
la Parte 1 («nadie entra por esa puerta», «las llegadas se redirigen o
esperan»), que no trata la cola existente. La alternativa (parar también esa
cola) daría un efecto mayor del cierre. Con el cierre a −30 la diferencia es
pequeña: en el estudio previo había 0 o 2 personas en cola al cerrar, frente a
unas 380 llegadas durante el cierre.

**D25 · Recuento de averías (definición literal, conservada).** El indicador de
averías cuenta todas las averías registradas en la réplica, también las que
ocurren cuando ya han entrado todos los espectadores. No equivale al número de
averías que perjudicaron a alguien. Se mantiene porque es la definición literal
de la Parte 1 y no se quiso aplicar un filtro sin acordarlo.

**D22 · Reloj de averías en funcionamiento.** Ver apartado 4. La Parte 1 decía
«tiempo entre fallos Exponencial(240)» sin precisar si contaba durante la
reparación; se eligió la definición de MTBF en sentido estricto.

**D26 y D20 · Relectura sin liberar el torno y prioridad no expulsiva.** Ambas
concretan lo que la Parte 1 dejaba implícito (§3.2 y §1.3) y no cambian ningún
parámetro.

**D12 · Utilización de tornos.** Se mide como en la Parte 1 (§4.4), con el
número nominal de tornos y desde la apertura hasta el último fin de control. Los
tornos averiados cuentan como disponibles y no ocupados. Por eso la utilización
de X0 (40 %) no es comparable con ρ en la punta (0,93): promedia unas dos horas,
de las que la punta ocupa media hora.

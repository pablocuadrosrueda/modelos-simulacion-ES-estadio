# C1. Ejecución del modelo y diseño estadístico

Parte del rol C (Chema). Texto para integrar en la memoria conjunta de la Parte 2.
Fecha de revisión: 25 de noviembre de 2026.

## 1. Unidad de simulación y ejecución

La unidad experimental es un partido completo. La réplica empieza con el estadio
vacío, al abrir las puertas en t = -90 min, y termina al concluir todos los
recorridos de espectadores. El inicio del partido es t = 0 y su final ordinario,
t = +105 min. SimPy trabaja en segundos; las tablas de resultados expresan los
instantes y las duraciones en minutos, salvo los indicadores definidos en segundos.

Es una simulación terminante, con un principio y un final naturales. No se elimina
un periodo de calentamiento: el estadio vacío es el estado inicial real del
sistema y la fase de entrada forma parte de las preguntas del estudio. Cada
espectador tiene un único proceso que encadena entrada, ubicación, permanencia y
salida. La alarma interrumpe ese recorrido y activa la evacuación según la
situación de la persona. Los procesos auxiliares de averías no determinan el fin
de la réplica, ya que se repiten indefinidamente.

El runner devuelve una fila por espectador, con sus atributos e instantes. El
límite temporal de configuración protege frente a una ejecución incompleta; no
se interpreta alcanzar ese límite como una salida. Los sucesos no ocurridos
permanecen ausentes (NaN), y los tiempos de vaciado solo se calculan cuando la
población correspondiente ha terminado. Las 2.965 réplicas definitivas terminaron
sin espectadores pendientes.

## 2. De los espectadores a los indicadores

Los KPIs se calculan primero dentro de cada partido. Después se analizan las
observaciones obtenidas entre partidos. Esto evita tratar a los miles de
espectadores, que comparten colas y recursos, como si fueran réplicas independientes.

| Indicador | Cálculo dentro de una réplica | Unidad |
|---|---|---|
| Espera media y P95 | Inicio de control menos llegada a la cola; media y percentil de las esperas observadas | min |
| Espera menor de 10 min | Porcentaje de personas con espera estrictamente menor de diez minutos | % |
| Cola máxima de puerta | Mayor cola simultánea en una puerta realmente utilizada, entre todas las puertas | personas |
| Utilización nominal | Tiempo de servicio acumulado dividido entre tornos nominales por tiempo desde apertura hasta el último fin de control | fracción; se dibuja en % |
| Tiempo de acceso | Instante de asiento menos llegada | min |
| Entrada tardía | Entre quienes llegan antes de t = 0, porcentaje que se sienta después de t = 0 | % |
| Retraso al resto por I1 | Diferencia de tiempo vomitorio-asiento entre otros espectadores expuestos y no expuestos a un I1 de su bloque; excluye causantes | s/persona |
| Vaciado ordinario | Última salida menos final del partido | min |
| Máximo en una salida | Mayor número simultáneo en una salida, incluida la persona que está cruzando | personas |
| Evacuación | Último instante en zona segura menos alarma; porcentaje seguro a los ocho minutos | min; % |

La entrada tardía incluye control, marcha, vomitorio y posibles conflictos. Su
nombre no demuestra que el retraso se deba exclusivamente a la cola del torno.
La utilización nominal media desde la apertura tampoco es la carga en la hora
punta: en X0 es aproximadamente 40,43 %, mientras la carga analítica de la franja
pico es aproximadamente 0,93. Son ventanas temporales y magnitudes distintas.

El P95 publicado es la media entre réplicas de los percentiles de cada partido.
No se han mezclado todos los espectadores para calcular un único percentil.
Igualmente, las colas dibujadas son medias de máximos por réplica; no sumas de
colas del estadio ni series temporales reconstruidas a partir de los agregados.

### 2.1. Colectivos y denominadores

En P4, mayores y personas con movilidad reducida se identifican con los mismos
criterios en FIFO y prioridad. Se usa la tabla de colectivos comparables,
`groups.csv`, también para el contraste con X0 (D32). Los KPIs originales de X0
no se sobrescriben: sin grupos prioritarios configurados, no ofrecen por sí
solos esa clasificación.

En P7 se distinguen la espera global y la del colectivo asignado a A-1 que llega
durante el cierre [-30,-20) min. Esta última procede de `audit.csv`.

En P8, el denominador del porcentaje seguro es la población que estaba dentro
cuando sonó la alarma, aunque hubiera personas todavía en tránsito o sin asiento.
Quienes siguen fuera y abandonan, o aún no han llegado, no se cuentan como
personas evacuadas. Se separa el porcentaje medio de personas seguras a ocho
minutos de la frecuencia de partidos completamente vaciados en ese plazo.

## 3. Réplicas y números aleatorios comunes

Cada fuente de azar usa su propio flujo y la semilla de la réplica r, numerada
desde cero, es `20261105 + r`. Las fuentes y los sorteos por espectador mantienen
la correspondencia entre escenarios. Distintas semillas representan distintas
réplicas; dos escenarios con la misma semilla se comparan como pareja. Repetir
una ejecución con la misma configuración y semilla comprueba reproducibilidad,
pero no aumenta el número de réplicas de la campaña.

Para la sensibilidad de aforo, los escenarios tienen distinto número de
espectadores. Se conserva el protocolo de semillas y flujos; no se supone que
los espectadores formen una muestra de tamaño idéntico en todos los escenarios.

## 4. Media e intervalo de confianza

Para un indicador Y, sean Y1,...,Yn sus valores por réplica. Se calcula la media
muestral y el intervalo t-Student nominal del 95 %, con n-1 grados de libertad:

```text
media = suma(Yr) / n
s² = suma((Yr - media)²) / (n - 1)
h = t(0,975; n-1) * s / sqrt(n)
IC = [media - h, media + h]
```

Las tablas expresan media ± h. La semianchura h describe la incertidumbre de la
media entre réplicas, no la dispersión individual de los espectadores ni un
límite que todos los partidos deban respetar. Los indicadores no aplicables se
mantienen en NaN y no cuentan en n; con una observación no se calcula un IC.

Las diferencias se calculan antes de construir el intervalo. Para cada semilla
común se obtiene Dr = Yalternativa,r - Yreferencia,r, y se aplica la misma
fórmula a los Dr. El n del contraste es el número de parejas válidas, que puede
ser menor que el tamaño de una de las muestras. Por ejemplo, X6 con redirección
usa 199 réplicas y sin redirección, 45; su contraste usa las 45 parejas comunes.
Restar las dos medias completas no proporciona el mismo estimador emparejado.

Las referencias de los contrastes son X0 para X1-X4 y S1, seis acomodadores para
X5, sin redirección para X6 y todas las salidas para X7. Una diferencia negativa
reduce el indicador. Los IC son individuales para cada comparación, con nivel
nominal del 95 %; no constituyen una garantía simultánea para todos los KPIs.

## 5. Piloto, tamaño de muestra y campaña definitiva

Se parte de diez réplicas piloto por escenario. Se estima el tamaño necesario
para que la semianchura sea, como máximo, el 5 % del valor absoluto de la espera
media:

```text
h_objetivo = 0,05 * abs(media_piloto)
n_estimado = techo((t_piloto * s_piloto / h_objetivo)²)
```

Se impone un mínimo de treinta réplicas. Esta estimación no garantiza alcanzar
la precisión: al terminar se recalcula el intervalo y se amplía la muestra si
h supera el objetivo. Los tamaños ya planificados no se reducen al reanudar.
La precisión se ha fijado para la espera media de entrada, no de forma separada
para la duración de conflictos, el vaciado u otros indicadores.

| Escenario | Réplicas definitivas | Semianchura relativa de espera (%) |
|---|---:|---:|
| X0 base | 180 | 4,3426 |
| X1, 2 tornos | 30 | 1,9320 |
| X1, 4 tornos | 183 | 4,6893 |
| X2, llegada anticipada | 138 | 4,9657 |
| X3, prioridad | 181 | 4,3205 |
| X4, salida escalonada | 180 | 4,3426 |
| X5, 3 acomodadores | 180 | 4,3426 |
| X5, 6 acomodadores | 180 | 4,3426 |
| X5, 9 acomodadores | 180 | 4,3426 |
| X6, sin redirección | 45 | 4,3704 |
| X6, con redirección | 199 | 3,7112 |
| X7, todas las salidas | 180 | 4,3426 |
| X7, una salida bloqueada | 180 | 4,3426 |
| S1, aforo -10 % | 247 | 4,1906 |
| S1, aforo +10 % | 73 | 4,5030 |
| S1, velocidad -15 % | 180 | 4,3426 |
| S1, velocidad +15 % | 180 | 4,3426 |
| S1, servicio -25 % | 219 | 4,9865 |
| S1, servicio +25 % | 30 | 3,5584 |

La campaña suma 2.965 réplicas en diecinueve escenarios: trece configuraciones
principales y seis de sensibilidad. Todas cumplen el criterio, con una
semianchura relativa máxima de 4,9865 %. Los 190 partidos del piloto actualizado
forman parte del total: se reutilizan las primeras diez semillas de cada
escenario, sin contarlas dos veces. El antiguo piloto de X6 con cierre en +20
es histórico y no se mezcla con la campaña en -30.

## 6. Trazabilidad y verificación

El cálculo definitivo se realizó con el código identificado por el commit
`fd6475cdf4982b4f2ff9c7dd03dccd8a848f52cb`. El manifiesto conserva las
configuraciones resueltas, versiones, semillas y hashes. Las mejoras posteriores
de las herramientas no reescriben esa procedencia.

La verificación de C contrasta identidad entre tablas, recuentos terminales,
reparto, relojes, rangos de KPIs y ausencia de resultados ficticios en fases no
aplicables. Recalcula resúmenes, contrastes y precisión a partir de las réplicas.
Además se reprodujo una réplica de cada escenario con su semilla original:
los 21 KPIs y los metadatos de auditoría coinciden en los diecinueve casos.

Los CSV agregados no permiten volver a reconstruir cada transición individual
de todos los recorridos de las 2.965 réplicas. Esa evidencia procede de la auditoría al
simular, las pruebas de conservación y orden temporal y las reproducciones
individuales. La repetición no sustituye la validación frente al sistema real.

Fuentes de esta sección: `results/final/{kpis,audit,groups,summary,comparisons,precision}.csv`,
`results/final/manifest.json`, `docs/RESULTADOS_T5.3.md` y
`docs/VERIFICACION_C_T6.2.md`. Definiciones: `docs/CONTRATOS.md`.

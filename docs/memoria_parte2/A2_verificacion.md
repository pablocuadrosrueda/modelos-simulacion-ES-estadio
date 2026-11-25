# A2 · Verificación y validación de la entrada y la capacidad

> Borrador del rol A para la memoria de la Parte 2 (T6.3). Resume la parte de A
> de `docs/VERIFICACION.md` (T2.1 y T6.2). La verificación de salida, evacuación
> e I1 es de B y la de métricas y runner, de C.

## 1. Planteamiento

La Parte 1 (§5.3) fijó cinco criterios: conservación, orden temporal,
capacidad de los recursos, casos límite y validación del ritmo por torno. Como
no hay datos reales de colas ni de salidas, la validación consiste en comprobar
que el modelo reproduce la comprobación previa de capacidad de la Parte 1 (§4.3)
y las distribuciones de entrada que esta fija, y que su comportamiento es el que
predice la teoría de colas.

Fuentes de las cifras:

* **Datos definitivos** de `results/final` (2.965 réplicas de 19 escenarios,
  calculadas con el commit `fd6475c`). Para esta verificación no se han
  regenerado: se han leído y contrastado. Solo se han rehecho dos réplicas ya
  publicadas, para comprobar la reproducibilidad.
* **Cálculos analíticos** de `src/sanmames/capacity.py`, con los parámetros de
  la configuración.
* **Casos límite** simulados en una macrozona (N/4, con la misma carga por
  puerta que el estadio completo), fijados como tests automáticos.

Todas las cifras van con su intervalo de confianza del 95 % (media ±
semianchura, t de Student, una observación por réplica) y su número de
réplicas n. Cuando el valor teórico queda fuera del intervalo, se indica la
desviación relativa.

## 2. Capacidad de los tornos

La Parte 1 estima la capacidad real de un torno en 13,6 pers/min: servicio
medio de 4 + 0,03 × 10 = 4,3 s con la relectura de I2, y un 97,4 % del tiempo
operativo por las averías de I3 (240 / (240 + 6,5)). La comprobación analítica
reproduce las cifras de la Parte 1: E[S] = 4,30 s, disponibilidad 0,974,
13,59 pers/min por torno y 978 pers/min con los 72 tornos.

En los datos definitivos de X0 (n = 180) se comprueban los dos componentes por
separado:

| Componente | Teórico | Modelo (IC 95 %) |
|---|---|---|
| Espectadores con relectura I2 | 3,00 % | 3,001 ± 0,011 % |
| Averías I3 por réplica (72 tornos, de la apertura al final) | 59,4 | 60,1 ± 1,0 |

Ambos valores teóricos quedan dentro del intervalo.

El ritmo resultante se mide en los periodos con cola sostenida, donde los tornos
no paran por falta de público. En la réplica 0 de X1 con 2 tornos (idéntica a la
publicada en `results/final`) salen **13,54 pers/min** por torno, un 0,4 % por
debajo de los 13,59 teóricos. Con dos réplicas propias de una macrozona, T2.1
obtuvo 13,58 pers/min con todas las incidencias y 14,98 sin ellas (teórico 15,00).

## 3. Intensidad de tráfico y espera

La intensidad de tráfico es ρ = λ_pico / capacidad, con λ_pico la tasa de
llegadas en la franja más cargada del perfil. Para contrastar ρ con la espera
observada se construyó un **modelo fluido** de cada puerta: llegadas y servicio
como caudales continuos, con la capacidad media de 13,59 pers/min por torno. El
modelo fluido ignora la variabilidad. Con ρ < 1 predice espera nula; con ρ > 1,
una espera que crece a ritmo ρ − 1 (minutos de espera por minuto de reloj)
mientras dura la sobrecarga y que después se reduce hasta vaciarse. La
simulación debe quedar algo por encima.

| Escenario | n | ρ | Espera media fluida (min) | Espera media observada (min) | P95 observado (min) |
|---|---|---|---|---|---|
| X1, 4 tornos | 183 | 0,70 | 0 | 0,016 ± 0,001 | 0,076 ± 0,002 |
| X2, perfil anticipado | 138 | 0,81 | 0 | 0,050 ± 0,003 | 0,209 ± 0,012 |
| S1, N − 10 % | 247 | 0,84 | 0 | 0,090 ± 0,004 | 0,489 ± 0,032 |
| X0, base | 180 | 0,93 | 0 | 0,192 ± 0,008 | 1,150 ± 0,068 |
| S1, N + 10 % | 73 | 1,02 | 0,205 | 0,486 ± 0,022 | 2,438 ± 0,130 |
| S1, servicio + 25 % | 30 | 1,15 | 1,304 | 1,402 ± 0,050 | 4,919 ± 0,211 |
| X1, 2 tornos | 30 | 1,40 | 3,826 | 4,016 ± 0,078 | 11,764 ± 0,266 |

* **La espera crece con ρ.** En los ocho escenarios sin cierre y con entrada
  distinta el orden de las esperas medias es exactamente el de ρ (Spearman = 1).
* **Con ρ muy por debajo de 1** (X1 con 4 tornos, X2) la espera media es de 1 a
  3 s; lo observado es solo la variabilidad.
* **Con ρ ≈ 0,93 (X0)** la espera media es de 11,5 s y el P95 de 1,15 min. La
  variabilidad pesa (hasta 135 ± 6 personas en la cola de una puerta), pero no
  hay acumulación sostenida.
* **Con ρ ≈ 1 (S1, N + 10 %)** el fluido predice 0,21 min y se observan 0,49 min.
  En el entorno de ρ = 1 domina la variabilidad, como predice la teoría de
  colas, y el fluido es solo una cota inferior.
* **Caso límite saturado, X1 con 2 tornos (ρ = 1,40).** La espera crece sin cota
  durante la punta (−30 a 0 min) y se vacía después. El fluido predice una
  espera máxima de (ρ − 1) × 30 ≈ 11,9 min, que coincide con el P95 observado
  (11,76 ± 0,27 min, dentro del intervalo). La espera media coincide con una
  desviación del 5 % (3,83 fluido frente a 4,02 ± 0,08 observado). Con el
  servicio + 25 % (ρ = 1,15), la desviación es del 7 % (1,30 frente a
  1,40 ± 0,05). En los dos casos lo observado queda por encima, que es lo
  esperado porque el fluido no tiene variabilidad.
* Que un modelo construido con 13,59 pers/min reproduzca la espera de los
  escenarios saturados confirma de forma independiente la capacidad efectiva
  del apartado 2.

**ρ de X2 = 0,81.** La Parte 1 daba 0,65, pero la franja más cargada del perfil
anticipado es la de −45 a −30 min (793 pers/min), no la de −30 a −15 (apartado
A1, 6.1). La espera observada en X2 (0,050 min) queda entre la del escenario con
ρ = 0,70 (0,016) y la del escenario con ρ = 0,84 (0,090), coherente con 0,81 y
no con 0,65.

**Cierre de puerta en t = −30 (X6).** Para quienes llegan a la puerta A-1
durante el cierre, el fluido predice 9,66 min de espera sin redirección y se
observan 9,63 ± 0,12 min (n = 45, dentro del intervalo). Con redirección
predice 0,59 min y se observan 0,54 ± 0,03 min (n = 199): coincide con una
desviación del 8 %, en este caso por debajo del fluido, porque la regla de ir a
la puerta con menos cola reparte mejor que el reparto igual que supone el
fluido.

**Vomitorios.** Admiten 411 pers/min por macrozona frente a los 245 que dejan
pasar los tornos, de modo que no son un cuello de botella en la entrada sin
conflictos (cálculo analítico; el efecto de los conflictos lo analiza B).

## 4. Distribuciones de entrada

Se regeneraron los espectadores con las semillas de las réplicas de X0 (180) y
X2 (138) de `results/final`, sin simular, y se contrastaron con las
proporciones de la Parte 1 mediante χ²:

| Reparto | Réplicas | Desviación máxima | p (χ² agregado) | Réplicas con p < 0,05 |
|---|---|---|---|---|
| Perfil por franjas, X0 | 180 | 0,010 p. p. | 0,62 | 3,3 % |
| Perfil por franjas, X2 | 138 | 0,018 p. p. | 0,37 | 3,6 % |
| Grupos 88/10/2 %, X0 | 180 | 0,015 p. p. | 0,28 | 5,0 % |
| Macrozonas 25 %, los 19 escenarios | 2.965 | 0,006 p. p. | 0,21 | 5,5 % |

Ningún reparto se rechaza y la fracción de réplicas rechazadas al 5 % ronda el
5 %, que es lo esperado si las proporciones son las de la Parte 1. Las 318
réplicas regeneradas dan exactamente los recuentos por macrozona guardados en
`results/final`.

## 5. Conservación, orden temporal y capacidad

* **Conservación.** En las 2.605 réplicas sin alarma, todos los espectadores
  generados entran, se sientan y salen, y no queda ninguno pendiente. En las 360
  réplicas de X7, todos quedan a salvo (la alarma suena en t = +40, cuando ya no
  hay cola exterior y nadie abandona). Además, los tests comprueban que cada
  espectador está en un único estado en cada transición, que es la igualdad de
  la Parte 1 (§3.3) persona a persona y no solo en la suma
  (`tests/test_conservacion.py`, `tests/test_verificacion_entrada.py`).
* **Orden temporal.** `tests/test_orden_temporal.py` comprueba
  t_llegada ≤ t_inicio_control ≤ t_fin_control ≤ t_sentado ≤ t_salida.
* **Capacidad.** Ningún torno atiende a más personas que su capacidad, también
  con averías (`tests/test_entry.py::test_turnstile_capacity_respected`,
  `tests/test_turnstile_failure.py::test_capacity_and_gate_keeps_serving_with_failures`).

## 6. Casos límite

| Caso | Resultado |
|---|---|
| Muchos tornos, sin incidencias | Espera prácticamente nula (P95 < 0,01 min) y exactamente 0 con la misma demanda |
| 2 tornos (ρ = 1,40) | La espera crece en la punta con pendiente ρ − 1 ≈ 0,40 min por minuto (tolerancia 15 %) |
| 4 tornos (ρ = 0,70) | Sin tendencia en la punta y espera media < 0,1 min |
| 2, 3 y 4 tornos | El P95 y la utilización decrecen con el número de tornos |
| Cierre a −30 sin redirección | Espera de los afectados próxima al fluido (≈ 9,7 min) |
| Cierre a −30 con redirección | Espera < 1,5 min y al menos 5 veces menor que sin ella |

Todos son tests automáticos rápidos (`tests/test_capacity.py`,
`tests/test_verificacion_entrada.py`, `tests/test_validacion_entrada.py`).

## 7. Reproducibilidad y números aleatorios comunes

* **Misma semilla, mismos resultados.** Las réplicas 0 de X0 y de X1 con 2
  tornos, rehechas, reproducen los 21 indicadores publicados con diferencias de
  4·10⁻¹⁵ como máximo, atribuibles al redondeo de coma flotante entre versiones
  de Python (3.12 en la campaña, 3.13 en la comprobación).
* **Números comunes.** En los escenarios que no modifican la entrada (X4, X5 con
  3/6/9 acomodadores, las dos variantes de X7 y S1 de velocidad), los
  indicadores de entrada (espera media, P95, cola máxima, relecturas) son
  idénticos a los de X0 en las 180 semillas comunes. El número de relecturas
  coincide también en X1, X2, X3 y X6 con redirección.
* **Efecto sobre la precisión.** La correlación entre escenarios emparejados por
  semilla es siempre positiva, de modo que emparejar nunca empeora el intervalo
  de una diferencia. La ganancia depende del contraste: en X6 (con frente a sin
  redirección, correlación 0,94) la varianza de la diferencia baja al 7 % de la
  que tendría con muestras independientes, y el intervalo se estrecha 3,7
  veces; en X1 y X2 frente a X0 la ganancia es pequeña (intervalos de 1,07 a 1,20
  veces más estrechos), porque las varianzas de los dos escenarios son muy
  distintas.

## 8. Validación frente a la Parte 1

| Magnitud | Parte 1 | Modelo | ¿Coincide? |
|---|---|---|---|
| Servicio medio con I2 | 4,3 s | 4,30 s; I2 en el 3,001 ± 0,011 % | Sí |
| Torno operativo | 97 % | 97,4 %; averías 60,1 ± 1,0 frente a 59,4 | Sí |
| Capacidad por torno | 13,6 pers/min | 13,59; 13,54 medido con cola | Sí |
| Capacidad total | 978 pers/min | 978 | Sí |
| ρ, X0 | 0,93 | 0,931 | Sí |
| ρ, 2 tornos | 1,40 | 1,396; la espera crece durante la punta y se vacía después | Sí (matizar redacción) |
| ρ, 4 tornos | 0,70 | 0,698 | Sí |
| ρ, X2 | 0,65 | 0,811 | No: error de cálculo de la Parte 1 |
| Vomitorios frente a tornos | 411 frente a 245 pers/min | 411 y 245 | Sí |
| Repartos por macrozona, franja y grupo | 25 %; tabla de §4.3; 88/10/2 % | χ², p ≥ 0,21 | Sí |
| Instante del cierre I4 | t = +20 min | t = −30 min | No: cambio decidido (D31) |
| Ritmo por torno frente a F2 | unos 4 s, 15 pers/min | 14,98 pers/min sin incidencias | Sí con la cifra que cita la Parte 1 (ver limitaciones) |

## 9. Limitaciones

* **Fuente F2.** La Parte 1 pide comprobar que el ritmo por torno coincide con
  F2 (García et al., 2026). El artículo no está en el repositorio y no se ha
  consultado para esta verificación. El contraste se ha hecho con la cifra que
  la Parte 1 atribuye a F2 (unos 4 s por persona, 15 pers/min por torno): el
  modelo sin incidencias da 14,98 pers/min. Antes de entregar conviene
  comprobar esa cifra en el artículo original.
* **Validación de coherencia, no de predicción.** Sin datos reales de colas ni
  de salidas, la validación comprueba que el modelo hace lo que la Parte 1
  especifica y lo que predice la teoría de colas. No demuestra que reproduzca
  las colas reales de San Mamés. Los resultados deben leerse como comparaciones
  entre escenarios, como ya advertía la Parte 1 (§5.3).
* **Parámetros sin datos.** El perfil de llegadas es una hipótesis inspirada en
  F2, y las probabilidades y duraciones de las incidencias son hipótesis (Parte
  1, §3.2). La verificación comprueba que el modelo las aplica bien, no que
  sean ciertas.
* **Modelo fluido.** Es una aproximación determinista. Sirve para contrastar el
  orden de magnitud y la forma de la espera, no para predecirla cuando ρ ≈ 1.

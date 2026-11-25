# Verificación y validación del modelo

Material para el apartado de verificación y validación de la memoria (Parte 2).
Partes de T2.1 (capacidad y tiempo de réplica), T5.4 (rendimiento) y T6.2
(contraste con los datos definitivos y con la memoria; parte de A al final, con
lo pendiente de B y C). Se regenera con:

```bash
python scripts/validate_capacity.py          # T2.1: 10 réplicas de X0; ≈ 1,5 min
python scripts/validate_final.py             # T6.2: lee results/final; ≈ 1 min
pytest tests/test_capacity.py tests/test_validacion_entrada.py   # rápidos
RUN_SLOW=1 pytest tests/test_capacity.py tests/test_validacion_entrada.py
```

## T2.1 · Capacidad y tiempo de réplica

**Ejecución:** 2026-11-23 · Python 3.13.2 · macOS (x86_64) · `main` en `5a17685`
(con T4.3, el runner ya admite I2) más la rama `feat/cuadros-T2.1-capacity`.
Semillas 20261105 + i (D11). Los resultados son deterministas.

### Parte A · comprobación analítica (memoria §4.3)

Fórmulas en `src/sanmames/capacity.py`; todos los parámetros salen de
`configs/base.json`.

| Comprobación | Esperado | Obtenido | ok |
|---|---|---|---|
| E[S] con I2 (s) = Tri(2,4,6) + 3 % × U(5,15) | 4,30 | 4,30 | ✓ |
| E[S] sin I2 (s) | 4,00 | 4,00 | ✓ |
| Disponibilidad del torno = 240 / (240 + 6,5) | 0,974 | 0,974 | ✓ |
| Capacidad por torno (pers/min) = 60 / E[S] × disp. | 13,6 | 13,59 | ✓ |
| Capacidad de los 72 tornos (pers/min) | 978 | 978 | ✓ |
| ρ perfil base, 2 tornos por puerta | 1,40 | 1,40 | ✓ |
| ρ perfil base, 3 tornos por puerta | 0,93 | 0,93 | ✓ |
| ρ perfil base, 4 tornos por puerta | 0,70 | 0,70 | ✓ |
| λ pico, perfil anticipado (pers/min) | 793,4 | 793,4 | ✓ |
| ρ perfil anticipado | 0,81 (memoria: 0,65) | 0,81 | ✓ |
| Vomitorios por macrozona (pers/min) = 80 plazas / 11,7 s | 411 | 411 | ✓ |
| Tornos por macrozona (pers/min) = 18 × 13,6 | 245 | 245 | ✓ |
| Vaciado de una macrozona (min) = 12.194 / (6 × 4 m × 66) | 7,7 | 7,70 | ✓ |
| Evacuación, todas las salidas (min, anchura × 1,3) | 5,9 | 5,92 | ✓ |
| Evacuación, una salida bloqueada (min) | 7,1 | 7,11 | ✓ |

**ρ del perfil anticipado.** La memoria da 0,65, pero su franja más cargada es
−45 a −30 min (24,4 % del público, ≈ 793 pers/min), no −30 a −15 (19,6 %). Con el
pico real, ρ = 793 / 978 ≈ 0,81. Es un error de la memoria, no del modelo; el test
fija 0,81.

Los vomitorios (≈ 411 pers/min por macrozona) admiten bastante más de lo que dejan
pasar los tornos (≈ 245), así que no son un cuello de botella en la entrada.

### Parte B · comprobación con simulación

X0 tal cual (I1, I2 e I3 activas, salida ordinaria encadenada), 10 réplicas;
los casos de 2/3/4/10 tornos y el ritmo, con 2 réplicas en el estadio completo.

| Comprobación | Esperado | Obtenido | ok |
|---|---|---|---|
| X0 con todas las incidencias se ejecuta | sí | sí | ✓ |
| Reparto por macrozona: máxima desviación del 25 % | ≈ 0 | 0,0036 | ✓ |
| Grupos 88/10/2 %: máxima desviación | ≈ 0 | 0,0006 | ✓ |
| Utilización de tornos (D12) frente a trabajo ofrecido | 0,404 | 0,404 | ✓ |
| Tiempo de vaciado (min) frente a la capacidad pura | 7,70 | 8,34 | ✓ (tol. 1 min) |
| Ritmo por torno con cola, 2 tornos, todas las incidencias (pers/min) | 13,59 | 13,58 | ✓ |
| Ritmo por torno con cola, 2 tornos, sin incidencias | 15,00 | 14,98 | ✓ |
| 10 tornos sin incidencias: p95 de la espera (min) | < 0,01 | 0,000 | ✓ |
| 4 tornos: p95 de la espera (min) | < 0,2 | 0,067 | ✓ |
| 3 tornos (X0): p95 de la espera (min) | < 2 | 0,793 | ✓ |
| 2 tornos (ρ = 1,40): p95 de la espera (min) | > 10 | 11,34 | ✓ |

Notas:

* **Ritmo por torno:** servicios por torno y minuto en periodos de cola de 5 min o
  más (con 2 tornos la cola es sostenida). Confirma a la vez el servicio medio con
  relectura (4,3 s) y la disponibilidad por averías (97,4 %). En periodos cortos
  domina el efecto de borde: en X0, con miles de periodos de ≈ 5 s, la medida sale
  entre 11,9 y 15,7 según se cuente o no el fin que cierra cada periodo.
* **Utilización:** es baja (0,40) aunque ρ en punta sea 0,93 porque D12 promedia
  desde la apertura hasta el último fin de control (≈ 2 h), con una punta de solo
  30 min. X0: espera media 0,15 min y p95 0,83 min; cola máxima en una puerta 111.
* **Vaciado:** 8,3 min frente a 7,7. La cifra de la memoria es solo la capacidad de
  las salidas; la simulación añade la marcha hasta la salida y la cola. Es lo
  esperado.
* **2 tornos:** sin I2 (ρ = 1,30) el p95 era 8,6 min; con I2 (ρ = 1,40) pasa de 10,
  como anticipa la memoria (§5.3).

### Tiempo de réplica (D15)

| Caso | Tiempo de pared |
|---|---|
| 1 réplica completa de X0 (N = 48.775; entrada, asiento y salida; I1, I2 e I3) | 3,0 s |
| 10 réplicas seguidas | 30,2 s |
| Igual, sin I2 | 2,9 s |
| Referencia previa: solo entrada + asiento, sin incidencias | ≈ 2,2 s |
| Memoria pico del proceso (10 DataFrames en memoria) | ≈ 690 MB |

Con todo activado y la salida encadenada, una réplica pasa de ≈ 2,2 a ≈ 3,0 s
(+35 %); I2 apenas cuenta (+0,1 s). Con 13 escenarios y unas 30 réplicas, la
campaña completa son ≈ 20 min en un núcleo.

## T5.4 · Tiempo de réplica por escenario

Medido el 2026-11-23 en un portátil Intel con Python 3.13.2: 3 réplicas
completas de cada escenario (N = 48.775, todas las incidencias del escenario),
semillas 20261105 a 20261107. Tiempo medio de pared por réplica.

| Escenario | Antes de T5.4 (s) | Después de T5.4 (s) |
|---|---|---|
| X0 base | 3,4 | 3,4 |
| X1 con 2 y con 4 tornos | 4,3 y 3,7 | sin cambio |
| X2 a X6 | 3,4 a 3,8 | sin cambio |
| X7 con todas las salidas | 6,9 | 4,7 |
| X7 con una salida bloqueada | 6,9 | 4,8 |

En X7 el mayor coste propio era `emergency._close_open_conflict`: se llamaba
para los 48.775 espectadores y cada vez recorría todas las incidencias (unas
1.750), unos 2 s por réplica. Ahora solo busca en quien tiene un conflicto
abierto. Los resultados son idénticos antes y después (misma huella de las
tablas de espectadores e incidencias en X0, X5 con 3 acomodadores y las dos
variantes de X7).

Tras el cambio, el perfil de una réplica de X0 o X7 no muestra ningún cuello de
botella en los módulos de B: el tiempo se reparte entre el motor de SimPy y los
procesos de entrada, asiento, salida y evacuación, en torno a 0,3 s de tiempo
propio cada uno con el perfilador activado. Con 13 escenarios y unas 30
réplicas, la campaña completa son unos 25 min en un núcleo.

## T6.2 (A) · Entrada y capacidad frente a los datos definitivos

**Fuente:** `results/final` (T5.3: 2.965 réplicas, 19 escenarios, código
`fd6475c`, Python 3.12.14). Los datos **no se han regenerado ni modificado**;
`src/` y `configs/` no han cambiado desde `fd6475c`. Medias ± semianchura del IC
del 95 % (t de Student, una observación por réplica). Solo se ha simulado para
rehacer dos réplicas ya publicadas (reproducibilidad) y para los casos límite
de una macrozona; las entradas aleatorias se regeneran con `generate_spectators`
sin simular. Tablas producidas por `scripts/validate_final.py` (2026-11-25,
Python 3.13.2, macOS) y fijadas en `tests/test_validacion_entrada.py`.

**Modelo fluido.** Para contrastar ρ con la espera se añade a `capacity.py` una
cola fluida por puerta (`fluid_waits`, `fluid_entry_wait`, `fluid_closure_wait`):
llegadas λ(t) del perfil entre 24 puertas y servicio a la capacidad media
(13,59 pers/min por torno). Ignora la variabilidad, así que con ρ < 1 predice
espera nula y con ρ > 1 una espera que crece a ritmo ρ − 1 mientras dura la
sobrecarga y después se vacía. La simulación debe quedar algo por encima.

### Capacidad: 13,6 pers/min por torno

La capacidad es 60 / E[S] × disponibilidad, con E[S] = 4,3 s (I2) y
disponibilidad 97,4 % (I3). Se contrastan sus dos componentes en los datos de X0
y el ritmo resultante en una réplica de `results/final` con cola sostenida:

| Componente (X0, n = 180) | Teórico | results/final, IC 95 % |
|---|---|---|
| Fallos de lectura I2 (% de espectadores) → E[S] = 4 + 0,03 × 10 | 3,00 | 3,001 ± 0,011 |
| Averías I3 por réplica, 72 tornos en [apertura, fin] (D25) → disponibilidad | 59,4 (72·T / (240 + 6,5)) | 60,1 ± 1,0 |

| Réplica rehecha | Máx. diferencia de KPI frente a `kpis.csv` | Ritmo por torno con cola (pers/min) | Capacidad teórica |
|---|---|---|---|
| X1_2tornos, réplica 0 (semilla 20261105) | 1,8e-15 | 13,54 | 13,59 |
| X0_base, réplica 0 (semilla 20261105) | 3,6e-15 | 12,89 | 13,59 |

* Con 2 tornos (cola de 30 min seguidos en cada puerta) el ritmo observado es
  13,54 pers/min, un 0,4 % por debajo de 13,59. En X0 apenas hay colas de 5 min
  o más y las que hay suelen deberse a una avería I3 en esa puerta, así que el
  ritmo medido en ellas (12,89) está sesgado a la baja; no es un contraste válido
  y se da solo por completitud. T2.1 obtuvo 13,58 con dos réplicas propias.
* Capacidad total: 72 × 13,59 = 978 pers/min (X0); 652 con 2 tornos; 1.304 con 4.

### ρ anticipado y espera observada

ρ = λ en la franja más cargada del perfil / capacidad total de los tornos.
Ordenado por ρ (los escenarios con la misma entrada que X0 dan idéntica espera
por los números comunes y se agrupan):

| Escenario | n | λ pico (pers/min) | Capacidad (pers/min) | ρ | Espera media fluida (min) | Espera media observada (min) | Espera máx. fluida (min) | P95 observado (min) | Cola máx. en una puerta |
|---|---|---|---|---|---|---|---|---|---|
| X1_4tornos | 183 | 910,5 | 1.304 | 0,698 | 0 | 0,016 ± 0,001 | 0 | 0,076 ± 0,002 | 38 ± 3 |
| S1_serv_-25 | 219 | 910,5 | 1.275 | 0,714 | 0 | 0,031 ± 0,002 | 0 | 0,129 ± 0,006 | 62 ± 4 |
| **X2_anticipado** | 138 | **793,4** | 978 | **0,811** | 0 | 0,050 ± 0,003 | 0 | 0,209 ± 0,012 | 72 ± 5 |
| S1_N_-10 | 247 | 819,4 | 978 | 0,838 | 0 | 0,090 ± 0,004 | 0 | 0,489 ± 0,032 | 90 ± 4 |
| X0_base (y X4, X5, X7, S1_vel) | 180 | 910,5 | 978 | 0,931 | 0 | 0,192 ± 0,008 | 0 | 1,150 ± 0,068 | 135 ± 6 |
| X3_prioridad | 181 | 910,5 | 978 | 0,931 | 0 | 0,192 ± 0,008 | 0 | 1,161 ± 0,072 | 135 ± 6 |
| X6_con_redireccion | 199 | 910,5 | 978 | 0,931 | 0 | 0,243 ± 0,009 | 0 | 1,360 ± 0,058 | 140 ± 6 |
| X6_sin_redireccion | 45 | 910,5 | 978 | 0,931 | 0 | 0,403 ± 0,018 | 0 | 1,774 ± 0,193 | 395 ± 7 |
| S1_N_+10 | 73 | 1.001,5 | 978 | 1,024 | 0,205 | 0,486 ± 0,022 | 0,72 | 2,438 ± 0,130 | 204 ± 10 |
| S1_serv_+25 | 30 | 910,5 | 794 | 1,147 | 1,304 | 1,402 ± 0,050 | 4,42 | 4,919 ± 0,211 | 276 ± 14 |
| **X1_2tornos** | 30 | 910,5 | 652 | **1,396** | 3,826 | 4,016 ± 0,078 | 11,89 | 11,764 ± 0,266 | 458 ± 13 |

* **La espera crece con ρ** de forma monótona en los escenarios sin cierre
  (Spearman 1 en los ocho de entrada distinta; 0,977 incluyendo X3 y X6, cuya
  espera depende también de la prioridad y del cierre).
* **ρ << 1** (X1_4tornos, X2, S1_serv_-25): espera media de 1 a 3 s y P95 por
  debajo de 13 s. El fluido da 0; lo observado es solo la variabilidad.
* **ρ ≈ 0,93** (X0): espera media 11,5 s y P95 1,15 min. Con ρ cerca de 1 la
  variabilidad pesa (cola máxima 135 en una puerta), pero no hay acumulación.
* **ρ ≈ 1** (S1_N_+10): el fluido predice 0,21 min y se observan 0,49 min. En
  ρ ≈ 1 domina la variabilidad, como espera la teoría de colas; el fluido es
  solo una cota inferior.
* **ρ > 1, caso límite saturado (X1_2tornos, ρ = 1,40):** la espera crece sin
  cota mientras dura la punta (−30 a 0) y se vacía después. El fluido predice
  una espera máxima de (ρ − 1) × 30 = 11,9 min y media de 3,83 min; se observan
  P95 11,76 ± 0,27 y media 4,02 ± 0,08 min (5 % por encima del fluido por la
  variabilidad). S1_serv_+25 (ρ = 1,15): 1,30 fluido frente a 1,40 ± 0,05.
  Que el fluido construido con 13,59 pers/min reproduzca la espera de los
  escenarios saturados confirma de forma independiente la capacidad efectiva.
* **ρ de X2 = 0,81** (no 0,65): la franja más cargada del perfil anticipado es
  −45 a −30 (24,4 % → 793 pers/min), no −30 a −15. Lo observado lo confirma: la
  espera de X2 (0,050) queda entre la de ρ = 0,70 (0,016) y la de ρ = 0,84
  (0,090). Con ρ = 0,65 cabría esperar una espera menor que la de X1_4tornos.

### Cierre I4 en t = −30 (D31)

Colectivo: asignados a A-1 que llegan durante [−30, −20). Fluido: sin
redirección, quien llega en el instante s del cierre espera (10 − s) + ρ·s;
con redirección las cinco puertas restantes reciben 6/5 de su caudal.

| Escenario | n | Llegadas en el cierre (teórico) | Observadas | Espera fluida (min) | Espera observada (min) |
|---|---|---|---|---|---|
| X6_sin_redireccion | 45 | 379 | 383,3 ± 5,6 | 9,659 | 9,626 ± 0,120 |
| X6_con_redireccion | 199 | 379 | 382,5 ± 2,7 | 0,590 | 0,543 ± 0,026 |

Sin redirección el fluido cae dentro del IC; con redirección lo observado queda
un 8 % por debajo (la regla «puerta con menos cola» reparte mejor que un reparto
igual). Es coherente con `docs/ESTUDIO_X6.md`, que medía otro colectivo (todos
los asignados a A-1, unos 2.000) con 5 réplicas: allí +292 ± 24 s de diferencia
sin − con redirección; aquí, solo para quienes llegan durante el cierre, 9,08
min de diferencia de medias.

### Repartos de entrada frente a la memoria

Espectadores regenerados con las semillas de las réplicas de X0 y X2 en
`results/final` (sin simular; mismas entradas que en la campaña). Contraste
χ² con las proporciones de la memoria sobre el total de réplicas y por réplica:

| Reparto | Réplicas | Máx. desviación (p. p.) | χ² agregado | p agregado | % réplicas con p < 0,05 |
|---|---|---|---|---|---|
| Perfil de llegadas (8 franjas) · X0_base | 180 | 0,010 | 5,30 (gl 7) | 0,623 | 3,3 |
| Perfil de llegadas (8 franjas) · X2_anticipado | 138 | 0,018 | 7,62 (gl 7) | 0,368 | 3,6 |
| Grupos 88/10/2 % · X0_base | 180 | 0,015 | 2,57 (gl 2) | 0,276 | 5,0 |
| Grupos 88/10/2 % · X2_anticipado | 138 | 0,014 | 2,26 (gl 2) | 0,323 | 5,1 |
| Macrozonas 25 % · X0_base (`zones.csv`) | 180 | 0,010 | 0,58 (gl 3) | 0,901 | 5,6 |
| Macrozonas 25 % · 19 escenarios (`zones.csv`) | 2.965 | 0,006 | 4,57 (gl 3) | 0,206 | 5,5 |

Ningún reparto se rechaza (p agregado ≥ 0,2) y la fracción de réplicas
rechazadas al 5 % ronda el 5 %, lo esperado si las proporciones son las de la
memoria. Las 318 réplicas regeneradas dan exactamente los recuentos por zona de
`zones.csv`. Tests: `tests/test_arrivals.py` (χ² con α = 0,001) y
`test_validacion_entrada.py::test_final_zone_shares`.

### Conservación

| Comprobación en `audit.csv` | Réplicas | Cumplen |
|---|---|---|
| Sin alarma: generados = entran = se sientan = salen, sin pendientes | 2.605 | 2.605 |
| Con alarma (X7): a salvo + abandonan = generados, sin pendientes | 360 | 360 |

En X7 (alarma en t = +40) todos habían entrado; en 4 de 360 réplicas una persona
aún no se había sentado (vomitorio o conflicto) y también queda a salvo. Nadie
abandona porque no queda cola exterior a +40. Tests:
`tests/test_conservacion.py` (un estado por persona en cada transición, con
salida simultánea y escalonada, con y sin incidencias, y con límite de tiempo),
`tests/test_verificacion_entrada.py::test_one_state_per_spectator_at_every_transition`
y `test_validacion_entrada.py::test_final_conservation` sobre `results/final`.

### Reproducibilidad y números aleatorios comunes (D17)

* **Mismas semillas, mismos KPIs:** las dos réplicas rehechas reproducen los 21
  KPIs de `kpis.csv` con diferencias ≤ 4e-15 (redondeo de coma flotante entre
  Python 3.12 y 3.13). Tests: `tests/test_experiments_cli.py::test_experiment_reproducible`,
  `tests/test_rng.py` y, con `RUN_SLOW=1`,
  `test_validacion_entrada.py::test_final_replica_is_reproduced`.
* **Números comunes entre X0 y las variantes:** cada fuente de azar tiene su
  flujo y los sorteos por espectador se hacen en E0 (D17, D21, D22, D26). En
  `results/final`:

| Comprobación | Semillas comunes | Idénticas |
|---|---|---|
| X4, X5 (3/6/9), X7 (2 variantes), S1_vel ±15 = X0 en KPIs de entrada (espera media y P95, cola máxima, nº de I2) | 180 cada uno | 180 cada uno |
| X1_2tornos, X1_4tornos, X2, X3, X6_con = X0 en nº de fallos I2 | 30 / 180 / 138 / 180 / 180 | todas |

| Diferencia de espera media | Parejas | Correlación | Var. emparejada / independiente (%) | Estrechamiento del IC |
|---|---|---|---|---|
| X1_4tornos − X0 | 180 | 0,70 | 87 | × 1,07 |
| X2_anticipado − X0 | 138 | 0,35 | 84 | × 1,09 |
| X1_2tornos − X0 | 30 | 0,65 | 69 | × 1,20 |
| X6_con − X6_sin | 45 | 0,94 | 7 | × 3,74 |

La correlación entre escenarios es siempre positiva, así que el emparejamiento
por semilla nunca empeora el IC. Entre X0 y X1/X2 la ganancia es pequeña porque
la varianza de la variante es muy distinta de la de X0 (X1_4tornos casi no
tiene espera; X1_2tornos tiene mucha), no porque fallen los números comunes. En
X6 reduce la varianza de la diferencia al 7 %.

### Casos límite de la entrada

| Caso | Resultado | Test |
|---|---|---|
| Muchos tornos (10 por puerta, o 60 en una puerta con ráfaga) | P95 < 0,01 min; espera exactamente 0 con la misma demanda | `test_capacity.py::test_many_turnstiles_no_queue`, `test_verificacion_entrada.py::test_many_turnstiles_remove_entry_wait` (ya existían) |
| 2 tornos, ρ = 1,40 (una macrozona) | La espera crece en la punta a la pendiente ρ − 1 ≈ 0,40 min por minuto (±15 %) | `test_validacion_entrada.py::test_queue_grows_at_rho_minus_one_with_two_turnstiles` |
| 4 tornos, ρ = 0,70 | Sin tendencia en la punta (pendiente < 0,005) y espera media < 0,1 min | `test_validacion_entrada.py::test_queue_stays_flat_with_four_turnstiles` |
| Orden 2 > 3 > 4 tornos | P95 y utilización decrecen; P95 > 10 min con 2 | `test_capacity.py::test_capacity_ordering_2_3_4_turnstiles` (ya existía) |
| Cierre I4 en −30 sin redirección | Espera de los afectados ≈ fluido (≈ 9,7 min), > 80 % del cierre | `test_validacion_entrada.py::test_closure_without_redirect_costs_almost_the_whole_closure` |
| Cierre I4 en −30 con redirección | Espera < 1,5 min y 5 veces menor que sin ella; todos redirigidos | `test_validacion_entrada.py::test_closure_with_redirect_is_small` |
| Cierre con 2 tornos (saturado) | La redirección baja la espera máxima de la puerta cerrada | `test_choose_gate.py::test_x6_redirect_lowers_max_wait_at_closed_gate` (ya existía) |

Todos tardan menos de 2 s; el único lento (`RUN_SLOW=1`) es la réplica completa
que reproduce `kpis.csv`.

## Validación frente a la memoria

Sin datos reales de colas ni salidas, la validación es de coherencia con la
comprobación previa de la memoria (§4.3), sus repartos (§3) y los criterios de
verificación (§6). «Modelo» = analítico (`capacity.py`) y, cuando hay cifra
simulada, `results/final`.

| Magnitud | Memoria | Modelo | ¿Cuadra? |
|---|---|---|---|
| Servicio medio en torno con I2 | 4,3 s | 4,30 s; I2 en el 3,001 ± 0,011 % de los espectadores | ✓ |
| Torno operativo | 97 % | 97,4 %; averías I3 60,1 ± 1,0 por réplica frente a 59,4 teóricas | ✓ |
| Capacidad por torno | 13,6 pers/min | 13,59; 13,54 medido con cola sostenida (X1_2tornos) | ✓ |
| Capacidad de los 72 tornos | ≈ 978 pers/min | 978 | ✓ |
| Llegadas en punta, perfil base | 910 pers/min | 910,5 | ✓ |
| ρ, X0 (3 tornos) | 0,93 | 0,931; espera media 0,192 ± 0,008 min, sin acumulación | ✓ |
| ρ, 2 tornos | 1,40, «la cola crece sin parar» | 1,396; crece a 0,40 min/min durante la punta, P95 11,76 ± 0,27 min (fluido 11,9) y se vacía después | ✓ (ver redacción) |
| ρ, 4 tornos | 0,70 | 0,698; espera media 0,016 ± 0,001 min | ✓ |
| ρ, perfil anticipado (X2) | 0,65 | **0,811** (pico −45 a −30, 793 pers/min); espera 0,050 ± 0,003 min, coherente con 0,81 | ✗ error de la memoria |
| Vomitorios frente a tornos por macrozona | 411 frente a 245 pers/min | 411 y 245 | ✓ |
| Reparto por macrozona | 25 % (12.194) | máx. desviación 0,006 p. p.; χ² p = 0,21 | ✓ |
| Perfil por franjas (base y X2) | tabla de §3 | máx. desviación ≤ 0,018 p. p.; χ² p = 0,62 y 0,37 | ✓ |
| Grupos | 88 / 10 / 2 % | máx. desviación 0,015 p. p.; χ² p = 0,28 | ✓ |
| Instante del cierre I4 | t = +20 min | t = −30 min (D31) | ✗ desviación decidida |
| Conservación (§6) | suma de estados = N | 2.965 de 2.965 réplicas | ✓ |
| Casos límite (§6) | muchos tornos ≈ 0; 2 tornos crece | ver tabla anterior | ✓ |
| Mismas semillas en todos los escenarios (§5) | sí | KPIs de entrada idénticos semilla a semilla donde la entrada no cambia | ✓ |
| Ritmo por torno frente a F2 (§6) | debe coincidir con F2 | 13,54–13,59, igual al derivado de los parámetros de la memoria | ✓ con la memoria; F2 no consultada |
| Salida 7,7 min; evacuación 5,9 / 7,1 min | §4.3 | pendiente de B (ver abajo) | — |

### Discrepancias que hay que corregir en el PDF (Parte 2)

No se modifica la memoria PDF; se corrige en la redacción de la Parte 2:

1. **§4.3, ρ del perfil anticipado: 0,81, no 0,65.** La franja más cargada de X2
   es −45 a −30 (24,4 %, 793 pers/min); 793 / 978 = 0,81. Ni el modelo ni los
   parámetros cambian; solo el número del texto.
2. **§3.2 (I4), instante del cierre: t = −30 min, no t = +20** (D31; ver
   `docs/ESTUDIO_X6.md`). A +20 llega el 2 % del público y X6 no respondería a
   P7.
3. **§4.3, redacción del caso de 2 tornos (menor):** «la cola crece sin parar» es
   cierto solo mientras dura la punta con ρ > 1 (−30 a 0). Después se vacía y
   todos entran: espera máxima ≈ 12 min y media 4,0 min. Sugerencia: «la cola
   crece sin cota durante la punta, a ≈ 0,4 min de espera por minuto».

No hacen falta decisiones nuevas: ninguna comprobación obliga a cambiar
hipótesis ni parámetros.

## Pendiente de B y C (T6.2)

Lo siguiente no es de A y queda para sus responsables. Se dan las cifras de
`results/final` como punto de partida, sin interpretarlas.

**B (salida, evacuación, I1, I4):**

* **Salida ordinaria frente a 7,7 min.** Capacidad pura de una macrozona: 7,70
  min (`capacity.zone_exit_time_min`, ya fijado en `test_capacity.py` y
  `test_exit.py`). En `results/final`: X0 8,367 ± 0,019 min; X4 escalonada
  9,591 ± 0,108. Falta descomponer la diferencia (marcha hasta la salida y cola)
  y decidir la tolerancia.
* **Evacuación frente a 5,9 / 7,1 min (+ reacción + recorrido).** X7 todas las
  salidas 7,469 ± 0,052 min; con una bloqueada 8,420 ± 0,014. Vaciado ≤ 8 min en
  163/180 y 0/180 réplicas. El vaciado máximo es 9,3576 min **en las dos
  variantes**; conviene comprobar qué espectador lo fija (probablemente
  reacción + marcha lenta, no las salidas) para explicarlo en la memoria.
* **I1, dispersión.** Número de conflictos en X0: 243,4 ± 2,5 por réplica
  (0,5 % × 48.775 = 243,9). Duración media en X0 5,32 ± 0,06 min, P95 9,54, máximo
  19,6 min, frente a Triangular(1, 3, 10) de media 4,67: la diferencia es la
  espera por acomodador. X5 (1 %): 44,60 / 13,74 / 6,64 min con 3 / 6 / 9
  acomodadores. Falta separar espera y resolución y contrastar la dispersión de
  la resolución con la triangular.
* **I4 desde el lado de B.** La entrada (A) ya cuadra con el fluido; queda que B
  confirme en `incidents.gate_closure_process` los instantes de cierre y
  reapertura registrados (−30 y −20) en las réplicas de X6.

**C (métricas, runner, análisis):**

* `turnstile_util` (D12) frente a ρ: la utilización promediada desde la apertura
  (≈ 0,40 en X0) no es ρ en punta; validar la definición con los datos finales.
* KPIs de evacuación (`evac_time_min`, `evac_pct_ref`, `n_abandoned`) y E8 en el
  runner; `conflict_delay_s` (D25) y cohortes de P4 (D32).
* Revisar los IC de `summary.csv` y `comparisons.csv` para el resto de KPIs. Los
  recalculados aquí (espera media, P95, cierre) coinciden con
  `docs/RESULTADOS_T5.3.md`.

No se ha encontrado ningún error en los módulos de B ni de C durante esta
verificación.

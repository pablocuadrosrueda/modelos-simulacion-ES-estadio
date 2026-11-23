# Verificación de capacidad y rendimiento (T2.1)

Material para el apartado de verificación de la memoria (Parte 2). Se regenera
con:

```bash
python scripts/validate_capacity.py          # 10 réplicas de X0; ≈ 1,5 min
pytest tests/test_capacity.py                # versión rápida (una macrozona)
RUN_SLOW=1 pytest tests/test_capacity.py     # incluye la réplica completa
```

**Ejecución:** 2026-11-23 · Python 3.13.2 · macOS (x86_64) · `main` en `5a17685`
(con T4.3, el runner ya admite I2) más la rama `feat/cuadros-T2.1-capacity`.
Semillas 20261105 + i (D11). Los resultados son deterministas.

## Parte A · comprobación analítica (memoria §4.3)

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

## Parte B · comprobación con simulación

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

## Tiempo de réplica (D15)

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

## Tiempo de réplica por escenario (T5.4)

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

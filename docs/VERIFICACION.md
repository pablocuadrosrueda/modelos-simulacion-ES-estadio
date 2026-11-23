# Verificación de capacidad y rendimiento (T2.1)

Material para el apartado de verificación de la memoria (Parte 2). Se regenera
con:

```bash
python scripts/validate_capacity.py          # 10 réplicas de X0; ≈ 1,5 min
pytest tests/test_capacity.py                # versión rápida (una macrozona)
RUN_SLOW=1 pytest tests/test_capacity.py     # incluye la réplica completa
```

**Ejecución:** 2026-11-23 · Python 3.13.2 · macOS (x86_64) · `main` en `88408d0`
más la rama `feat/cuadros-T2.1-capacity` (código en `36ff40f`). Semillas
20261105 + i (D11). Los resultados son deterministas.

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

El runner aún rechaza I2 con `NotImplementedError`, así que **X0 con todas las
incidencias no se puede ejecutar**. Las comprobaciones usan X0 sin I2 (I1 e I3
activas, salida ordinaria encadenada) y el teórico correspondiente sin I2
(E[S] = 4,0 s; 14,6 pers/min por torno con averías).

| Comprobación | Esperado | Obtenido | ok |
|---|---|---|---|
| X0 con todas las incidencias se ejecuta | sí | no (I2 rechazada por el runner) | ✗ |
| Reparto por macrozona: máxima desviación del 25 % | ≈ 0 | 0,0036 | ✓ |
| Grupos 88/10/2 %: máxima desviación | ≈ 0 | 0,0006 | ✓ |
| Utilización de tornos (D12) frente a trabajo ofrecido | 0,376 | 0,376 | ✓ |
| Tiempo de vaciado (min) frente a la capacidad pura | 7,70 | 8,34 | ✓ (tol. 1 min) |
| Ritmo por torno con cola, 2 tornos, con I3 (pers/min) | 14,60 | 14,60 | ✓ |
| Ritmo por torno con cola, 2 tornos, sin incidencias | 15,00 | 14,98 | ✓ |
| 10 tornos sin incidencias: p95 de la espera (min) | < 0,01 | 0,000 | ✓ |
| 4 tornos: p95 de la espera (min) | < 0,2 | 0,043 | ✓ |
| 3 tornos (X0 sin I2): p95 de la espera (min) | < 2 | 0,316 | ✓ |
| 2 tornos (ρ > 1): p95 de la espera (min) | > 10 (con I2) | 8,62 (sin I2) | ✗ |

Notas:

* **Ritmo por torno:** servicios por torno y minuto en periodos de cola de 5 min o
  más (con 2 tornos la cola es sostenida). En periodos cortos domina el efecto de
  borde: en X0, con 5.358 periodos de ≈ 5 s, la medida sale entre 11,9 y 15,7
  según se cuente o no el fin que cierra cada periodo.
* **Utilización:** es baja (0,38) aunque ρ en punta sea 0,87–0,93 porque D12
  promedia desde la apertura hasta el último fin de control (≈ 2 h), con una punta
  de solo 30 min.
* **Vaciado:** 8,3 min frente a 7,7. La cifra de la memoria es solo la capacidad de
  las salidas; la simulación añade la marcha hasta la salida y la cola. Es lo
  esperado.
* **2 tornos, p95 = 8,6 min y no > 10:** se mide sin I2 (ρ = 1,30). Con I2, ρ = 1,40
  y una aproximación de fluido da una espera máxima de ≈ 12 min, así que el p95
  probablemente superaría los 10 min. Queda pendiente de que el runner admita I2.

## Tiempo de réplica (D15)

| Caso | Tiempo de pared |
|---|---|
| 1 réplica completa X0 sin I2 (N = 48.775, entrada + asiento + salida, I1 e I3) | 2,9 s |
| 10 réplicas seguidas | 28,8 s |
| Referencia previa: solo entrada + asiento, sin incidencias | ≈ 2,2 s |
| Memoria pico del proceso (10 DataFrames en memoria) | ≈ 690 MB |

Activar I1 e I3 y encadenar la salida sube el tiempo de ≈ 2,2 a ≈ 2,9 s por réplica
(+30 %). Con 13 escenarios y unas 30 réplicas, la campaña completa son ≈ 20 min en
un núcleo. El coste de I2 aún no se puede medir; debería ser pequeño, porque solo
añade un `timeout` al 3 % de los espectadores.

## Pendiente

* Repetir la parte B con X0 completo (I2 activa) cuando el runner deje de
  rechazarla. `tests/test_capacity.py::test_full_x0_with_all_incidents_runs` es un
  xfail estricto que falla en cuanto eso ocurra, para recordarlo.
* Evacuación (emergencia) con simulación: depende de T4.1–T4.3.

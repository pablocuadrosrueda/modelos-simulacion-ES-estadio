# Informe de coherencia de la memoria de la Parte 2 (T6.3, integración)

Revisión de A1–A3, B1–B3 y C1–C3 antes de unirlos en una sola memoria. Las
cifras se han contrastado **leyendo** `results/final` (`summary.csv`,
`comparisons.csv`, `kpis.csv`, `audit.csv`) y `docs/RESULTADOS_T5.3.md`, sin
regenerar ni modificar nada. En esta fase no se corrige ningún Markdown.

Formato de las cifras: media ± semianchura del IC del 95 %, n réplicas o parejas.

## 1. Cifras repetidas que no coinciden

| # | Magnitud | Dónde y valor | Valor en `results/final` | Veredicto |
|---|---|---|---|---|
| 1 | Entrada tardía de X0 | A3, C1, C3: 4,578 ± 0,052 % (n = 180). B2: «4,46 %» | 4,578 ± 0,052 % (n = 180). Las 20 primeras réplicas dan 4,461 ± 0,133 % | **Correcta: 4,578 ± 0,052 %.** El 4,46 % de B2 no es un error: es la media de las 20 primeras réplicas, que B usa para su contraste sin conflictos. En la memoria debe darse la cifra oficial y el contraste de B como diferencia emparejada |
| 2 | Entrada tardía de X0 sin conflictos | B2: 4,38 %; diferencia 0,08 (0,01) puntos, 20 réplicas | No está en `results/final` ni lo reproduce ningún script del repo (`scripts/validate_b.py` no lo calcula) | **PENDIENTE DE CONFIRMAR** (B). La conclusión cualitativa (los conflictos pesan poco) es coherente con el resto |
| 3 | Tiempo de acceso de X0 | A3: 1,972 ± 0,008 min. B2: «de 1,96 a 1,93 min» | 1,972 ± 0,008 min (180). Las 20 primeras: 1,964 ± 0,027 | Igual que el n.º 1: el 1,96 es la submuestra de 20. Oficial: 1,972 ± 0,008. El 1,93 sin conflictos, PENDIENTE (B) |
| 4 | P8, vaciado | B3: 7,47 (0,05) y 8,42 (0,01) min. C3: 7,4694 ± 0,0516 y 8,4200 ± 0,0140 | 7,4694 ± 0,0516 y 8,4200 ± 0,0140 (n = 180 cada una) | Coinciden; solo cambian el redondeo y la notación de la semianchura. 163/180 y 0/180 coinciden. 98,56 % (B3) = 98,5607 ± 0,0284 % ✓ |
| 5 | X6, espera de los afectados | A3: 9,626 ± 0,120 (45) y 0,543 ± 0,026 (199). C3: 9,626 y 0,543, sin IC | Igual que A3 (`audit.csv`) | Coinciden. Usar las de A3, con IC y n |
| 6 | X6, diferencia global con − sin | A3: −0,160 ± 0,007. C3: −0,1596 ± 0,0072 (45 parejas) | −0,15959 ± 0,00724 (45) | Coinciden (redondeo) |
| 7 | X6 con redirección − X0 | A3: «PENDIENTE DE CONFIRMAR» y una comparación de medias no emparejadas (0,243 frente a 0,192). C3 y `LEEME_C.md`: +0,04989 ± 0,00346 min (180 parejas) | Leído de `kpis.csv` con 180 semillas comunes: +0,04989 ± 0,00346 min | **Correcta la de C.** Cierra el pendiente de A3; la comparación de medias de A3 debe sustituirse por esta diferencia emparejada |
| 8 | P2, 2 y 3 tornos | A3: 88,96 ± 0,74 % (30) y 100,0 % (180). C3: 88,9583 ± 0,7353 % | 88,9583 ± 0,7353 % (30); 100,0 % (180) | Coinciden (redondeo) |
| 9 | P6, retraso al resto del bloque | B3: 292 / 37 / 7 s por persona, sin IC. C3: 291,726 / 36,839 / 6,667 s, sin IC | 291,73 ± 11,92 / 36,84 ± 2,39 / 6,67 ± 0,55 s (180 cada uno) | Coinciden, pero ninguno da el IC. En la memoria, con IC |
| 10 | P6, entrada tardía con 3/6/9 acomodadores | B3: 14,5 / 7,2 / 5,1 %, sin IC | 14,549 ± 0,281 / 7,195 ± 0,139 / 5,132 ± 0,069 % (180) | Coinciden; falta el IC |
| 11 | P5, máximo en una salida | B3 y C3: de 1.460 a 746 personas, sin IC | 1.459,95 ± 1,33 y 746,07 ± 1,39 (180); diferencia −713,878 ± 0,573 | Coinciden; falta el IC de los niveles |
| 12 | P5, vaciado | B3: +1,22 (0,11) min, de 8,37 a 9,59. C3: +1,224 ± 0,105 | 8,3668 ± 0,0188 → 9,5907 ± 0,1077; diferencia +1,224 ± 0,105 (180) | Coinciden |
| 13 | S1, velocidad +15 %, vaciado | C2: −0,0862 ± 0,0182 min | −0,08615 ± 0,01820 (180) | Error de redondeo en C2: es **−0,0861**. Sin efecto en la conclusión |
| 14 | Población de una macrozona en la validación de salida | B2: 12.195 personas. A2 y la Parte 1: 12.194 | N / 4 = 12.193,75 | Diferencia de una persona por redondeo en el test de B; irrelevante para 7,7 / 5,9 / 7,1 min. En la memoria: «una macrozona (N/4, unas 12.194 personas)» |
| 15 | Acomodadores casi ilimitados | B2: 4,62 min, sin n | `docs/VALIDACION_T6.2.md`: 5 réplicas, rango 4,51–4,68 | Coincide; añadir n = 5 en la memoria |

**Tamaños de muestra.** Los n de A3, B3 («180 por escenario» en P5, P6 y P8) y la
tabla de C1 coinciden con `precision.csv` y con `docs/RESULTADOS_T5.3.md`. Los
contrastes emparejados usan el n de parejas (por ejemplo, 45 en X6 y 180 en X1
con 4 tornos), no el de la muestra mayor: A3 y C1 lo dicen igual.

## 2. Terminología

| Aspecto | A | B | C | Regla para la memoria |
|---|---|---|---|---|
| Decisiones | Cita D-números (D17, D23, D31…) | Ninguna; «hipótesis adoptadas» | D-números en tablas (D31, D33, D34, D32) | **No citar D-números.** Citar por su contenido: «hipótesis adoptada: …», «cambio decidido: …» |
| Código y ficheros | `choose_gate`, `PriorityResource`, `RngStreams`, rutas `tests/…`, `results/…` | Ninguno | `groups.csv`, `audit.csv`, NaN, hash del commit | **Ningún nombre de código ni fichero del repo.** Se describe el mecanismo («la tabla de colectivos comparables», «sin valor»). Las figuras se citan por número de figura |
| Escenarios | «X1 con 2 tornos», «X6 con redirección» | Sin códigos («experimento de acomodadores») | «X1, 2 tornos», «X5, 6 acomodadores» | Código y descripción: «X1 (2 tornos)». La Parte 1 numeraba X0–X7 y S1, y los lectores los conocen |
| ρ | «intensidad de tráfico ρ» | — | «carga analítica» | **«intensidad de tráfico ρ»**, como en la Parte 1 |
| Entrada tardía | «entrada tardía» (propone renombrar el «% entrada tardía por colas» de la Parte 1) | «entrada tardía» | «entrada tardía» | «entrada tardía», con su definición una sola vez. Las figuras ya dicen «Entrada tardía (incluye recorrido)» |
| Incidencias | Nombre e «I2», «I3» | Solo el nombre | «duración media I1» | Nombre y código en la primera mención: «conflicto por asiento (I1)» |
| Colectivo | «mayores y personas con movilidad reducida» | Igual | «PMR» | Definir «personas con movilidad reducida (PMR)» una vez |
| Semianchura | «± h» | «(h)» entre paréntesis | «± h» | **«± h»** y n explícito |
| Decimales | 3 en min, 2–3 en % | 1–2 | 4 | Mismo número de decimales en media y semianchura; 3 en minutos y 2 en %, salvo cuando haga falta más para no redondear a 100 % (P8) |
| Unidades | «s por persona» | «s por persona» | «s/persona» | «s por persona»; minutos «min» |
| Zona | «macrozona» | «macrozona» | «por zona» | «macrozona» |

A3 todavía dice que el panel de P3 se titula «atribuible a colas». Ya no es
cierto: C corrigió las figuras P3 y P6 en el PR #36 y ahora dicen «Entrada
tardía (incluye recorrido)». La frase se elimina en la integración.

## 3. Contradicciones y solapes

### Contradicciones

| Tema | Qué dice cada uno | Resolución |
|---|---|---|
| Hipótesis del cierre (la cola ya formada sigue atendiéndose) | A1: «hipótesis del grupo, conservada». B1: «hipótesis adoptada». C3: aparece como aclaración, sin decir que esté pendiente. El registro de decisiones del repo aún la tiene como «pendiente de confirmar por el grupo» | **Hipótesis adoptada**, con su limitación (redirección optimista) y un comentario `% DECIDIR` en el LaTeX. Nadie la da por confirmada hasta que el grupo lo diga |
| P7 frente a X0 | A3: comparación de medias de muestras distintas y «PENDIENTE». C1 prohíbe expresamente restar medias de muestras distintas; C3 da la diferencia emparejada | Se usa la de C (+0,04989 ± 0,00346 min, 180 parejas) |
| Título del panel de P3 | A3 lo critica; C ya lo corrigió | Se elimina la crítica |

No hay afirmaciones opuestas sobre resultados. P8 se interpreta igual en B3 y C3:
sin bloqueo falla la marcha de una persona con movilidad reducida, y con
bloqueo falla la capacidad.

### Solapes y sección que se queda con cada tema

| Tema | Aparece en | Sección de la memoria |
|---|---|---|
| Atributos del espectador (velocidad, grupos, distancia) | A1 §2, B1 | Modelo · Llegadas y espectadores (A1) |
| Cierre de puerta y redirección | A1 §3.1, B1 | Modelo · Entrada (A1, con lo de B1 sobre el orden de reapertura) |
| Números aleatorios comunes | A1 §5, B1, C1 §3 | Modelo · un solo apartado (A1 + B1); C1 solo para su uso estadístico |
| Hipótesis no precisadas en la Parte 1 | A1 §6.3, B1, C3 §2 | Una tabla en «Desviaciones respecto a la Parte 1» |
| Cambios de diseño (cierre en −30, nueve acomodadores, n por precisión, ρ de X2) | A1 §6.1–6.2, C3 §2 | Misma tabla de desviaciones |
| Definición de entrada tardía y de utilización frente a ρ | A3 P1, B1, C1 §2 | Verificación · Indicadores (C1), una vez |
| Conservación, orden temporal, capacidad | A2 §5, B2, C1 §6 | Verificación · un apartado común |
| Reproducibilidad | A2 §7, C1 §6 | Verificación · Campaña (C1) con los datos de A2 |
| Respuestas P1–P8 | A3, B3 (detalladas) y C3 §1 (resumen) | Resultados, en orden P1…P8; las conclusiones resumen sin repetir cifras |
| Peso de los conflictos en la entrada tardía | A3 P1 (pendiente de B), B2 | Resultados P1, con la cifra de B (pendiente) |
| F2 | A2 §9, C3 §3 | Limitaciones (una vez) |

## 4. Cifras sin comprobar

| Cifra | Dónde | Estado |
|---|---|---|
| X6 con redirección − X0 | A3 | **Cerrada**: +0,04989 ± 0,00346 min, 180 parejas (C3, comprobada leyendo `kpis.csv`) |
| Entrada tardía y acceso de X0 sin conflictos (4,38 %, 1,93 min; diferencia 0,08 ± 0,01 puntos) | B2 | **Sigue pendiente**: no la reproduce ningún script del repo. B debe añadir su cálculo a `scripts/validate_b.py` o a `docs/VALIDACION_T6.2.md` |
| Ritmo por torno según F2 | A2, C3 | **Sigue pendiente**: el artículo no está en el repo. Es una limitación, no una cifra del modelo |
| Duración con acomodadores casi ilimitados (4,62 min) | B2 | Comprobada en `docs/VALIDACION_T6.2.md` (5 réplicas) |
| Vaciado sin PMR ≤ 7,36 min | B2, B3 | Comprobada en `docs/VALIDACION_T6.2.md` |

## 5. Qué decide cada uno

* **Grupo:** confirmar o no la hipótesis del cierre (cola ya formada). Hasta
  entonces la memoria la presenta como hipótesis adoptada.
* **B:** hacer reproducible el contraste sin conflictos (n.º 2 y 3) o retirarlo.
  Opcional: añadir los IC de P5 y P6 a B3 (n.º 9 a 11) y n = 5 al caso de
  acomodadores ilimitados (n.º 15).
* **C:** corregir el redondeo de C2 (n.º 13). Opcional: dar los IC de X6 en C3.
* **A (integración):** aplicar la regla de terminología, quitar de A3 la crítica
  al título de P3 y sustituir la comparación de medias de P7 por la diferencia
  emparejada de C. Los Markdown de A se actualizarán en otro PR si el grupo lo
  pide; la memoria en LaTeX ya lo incorpora.

## 6. Cierre (feat/cuadros-T6.3-entrega)

Tras los cierres de B (PR #42) y C (PR #41), cada cifra de la memoria se ha
comprobado de nuevo en `results/final` o en `results/figures/statistics.csv`
antes de escribirla:

| Cifra | Markdown | `results/` | Memoria |
|---|---|---|---|
| Entrada tardía y acceso de X0 con conflictos | B2: 4,578 % y 1,972 min | `summary.csv`: 4,578 ± 0,052 % y 1,972 ± 0,008 min (180) | Igual |
| X0 sin conflictos (4,488 %, 1,941 min; diferencias 0,090 ± 0,006 puntos y 0,032 ± 0,001 min, 180 parejas) | B2 y `docs/VALIDACION_T6.2.md` §3 | No está en `results/final`: es una simulación adicional de B, reproducible con `scripts/validate_b.py` (180 semillas de la campaña). Los valores con conflictos sí coinciden con `results/final` | Se usa la de B; deja de estar pendiente |
| P5, máximo en una salida | B3: 1.460 (1,3) y 746 (1,4); −714 (0,6) | `statistics.csv`: 1.459,95 ± 1,33 y 746,07 ± 1,39; `comparisons.csv`: −713,878 ± 0,573 | 1.460,0 ± 1,3; 746,1 ± 1,4; −713,9 ± 0,6 |
| P5, vaciado | B3: 8,37 (0,02) y 9,59 (0,11); +1,22 (0,11) | 8,3668 ± 0,0188 y 9,5907 ± 0,1077; +1,224 ± 0,105 | Igual, con 3 decimales |
| P6, entrada tardía con 6 acomodadores | B3: **7,20 %** (0,14) | `statistics.csv`: 7,1947 ± 0,1389 | **7,19 ± 0,14 %**. Redondeo de B3; se avisa a B |
| P6, resto de cifras y P8 | B3 | `statistics.csv` | Coinciden |
| S1, velocidad +15 %, vaciado | C2: −0,0861 ± 0,0182 | −0,08615 ± 0,01820 | Igual (corregido por C) |
| X6, colectivo afectado | C3: 9,6259 ± 0,1204 (45) y 0,5433 ± 0,0260 (199) | `audit.csv` | 9,626 ± 0,120 y 0,543 ± 0,026 |
| X6 con redirección − X0 | C3: +0,04989 ± 0,00346 (180) | Leído de `kpis.csv` con 180 semillas comunes | +0,050 ± 0,003 |

Pendientes que quedan en la memoria: la fecha de entrega (la pone Pablo
Cuadros) y la comprobación directa con F2, que no puede hacerse con el repo.

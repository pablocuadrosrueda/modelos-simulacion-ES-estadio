# T6.2 · Verificación del rol C

**Alcance:** integración del runner, KPIs y consistencia de los resultados definitivos. No cierra la revisión de capacidad y supuestos de A y B.

Campaña: 2965 réplicas, 19 escenarios. Código del cálculo original: `fd6475cdf4982b4f2ff9c7dd03dccd8a848f52cb`.

Verificador SHA-256: `f3a2914cd5cc733a0e8adccc37022cccc56bd4d4c38698938db66d048695bfd8`. Python 3.12.14.

## Comprobaciones

- Esquema, semillas y precisión: 2965 réplicas, 19 escenarios.
- Recuentos, rangos, unidades, conservación terminal y reloj: correctos.
- Reparto: 11860 filas; colectivos comparables P4: 361 réplicas.
- Resúmenes, 15 contrastes emparejados y precisión recalculados desde las réplicas.
- Números comunes: entrada invariante en X4/X5/X7/velocidad; mismos I1 en X5.

La conservación de las 2.965 réplicas se comprueba con los recuentos agregados y la auditoría realizada durante T5.3. Los CSV no contienen las trayectorias individuales de toda la campaña; no permiten volver a demostrar cada transición por sí solos.

## Reproducción desde las configs y semillas originales

Código de `src/` coincidente por SHA-256 con T5.3, normalizando CRLF a LF para permitir la conversión de finales de línea de Git en Windows. Una réplica por escenario, comprobada individualmente: IDs 0..N−1 sin duplicados, terminación mediante `audit_replica`, orden de entrada/asiento, todos los KPIs y metadatos de auditoría coincidentes. Tolerancia numérica: rtol=1e-9, atol=1e-8 en unidades de cada indicador; tiempos ordenados con tolerancia 1e-9 min.

| Escenario | Semilla | Espectadores |
|---|---:|---:|
| S1_N_-10 | 20261105 | 43898 |
| S1_N_+10 | 20261105 | 53653 |
| S1_vel_-15 | 20261105 | 48775 |
| S1_vel_+15 | 20261105 | 48775 |
| S1_serv_-25 | 20261105 | 48775 |
| S1_serv_+25 | 20261105 | 48775 |
| X0_base | 20261105 | 48775 |
| X1_2tornos | 20261105 | 48775 |
| X1_4tornos | 20261105 | 48775 |
| X2_anticipado | 20261105 | 48775 |
| X3_prioridad | 20261105 | 48775 |
| X4_escalonada | 20261105 | 48775 |
| X5_3acomodadores | 20261105 | 48775 |
| X5_6acomodadores | 20261105 | 48775 |
| X5_9acomodadores | 20261105 | 48775 |
| X6_con_redireccion | 20261105 | 48775 |
| X6_sin_redireccion | 20261105 | 48775 |
| X7_salida_bloqueada | 20261105 | 48775 |
| X7_todas_salidas | 20261105 | 48775 |

## Evidencia existente y límites

- Conservación en cada transición, salida ordinaria y truncamiento: `tests/test_conservacion.py`, `tests/test_orden_temporal.py`.
- Alarma, abandonos, no llegadas, conflictos interrumpidos y evacuación incompleta: `tests/test_emergency_integration.py`.
- KPIs con cálculos manuales, NaN, denominadores y unidades: `tests/test_metrics*.py`; IC y emparejamiento: `tests/test_analysis.py`.
- Capacidad y referencias analíticas ya documentadas por A/B: [VERIFICACION.md](VERIFICACION.md), `tests/test_capacity.py`, `tests/test_exit.py` y `tests/test_emergency.py`.

Esto aporta verificación interna y reproducibilidad. La validez externa sigue limitada por la falta de datos completos de colas y salidas (ESPECIFICACION §6). Se comparan escenarios; repetir la misma semilla no aporta una réplica estadística nueva.

## Pendiente de A y B para cerrar T6.2

- A: revisar la evidencia existente de carga con dos tornos (ρ>1), ritmo por torno frente a F2 y capacidad de entrada; confirmar su vigencia para la memoria.
- B: revisar capacidad de vomitorios/acomodadores/salidas y referencias de evacuación; confirmar supuestos y límites de sus módulos.
- Equipo: cerrar la validación conjunta. No hace falta repetir comprobaciones ya aportadas si sus responsables confirman que siguen vigentes.
- T6.3: redactar la memoria usando T6.1 y la revisión conjunta de T6.2.

## Reproducción

```bash
.venv/bin/python scripts/verify_results.py --replay
# Solo consistencia de las tablas (sin simular):
.venv/bin/python scripts/verify_results.py --output /tmp/verificacion_C.md
```

El comando no modifica `results/final`; escribe el informe solo si todas las comprobaciones pasan. La suite de tests se ejecuta aparte con `make check`.

## Huellas SHA-256 de las entradas

| Archivo | SHA-256 |
|---|---|
| kpis.csv | `ea39370dce4303835329a5f53a9e504fc8ef9d24ff24a4a5243e39d7ae3e59c2` |
| audit.csv | `faa15c259d237ec2c0efbfcd05fea7509fc6f7c4a813d350f65ff49fefbfd6ff` |
| zones.csv | `d07d1e5c603e2bf890e3491581e55395d5e973d43e602f988f624cd96e7036dc` |
| groups.csv | `ec893524fca306c45636a008a384ac1a04140788e193b21c86858c8270f47876` |
| summary.csv | `ac5c8af3123589cb7663fcf4928c1644ff53f4d2adba6ad700cb72f060e39072` |
| comparisons.csv | `f066743f55566fcfbe9cd8a990778722eaabda61c379e8bb271b9ba8319ad630` |
| precision.csv | `a93cba901abb28ae93df118afd9e8f9f27792e5be58e189f38f72280fc78eeb7` |
| manifest.json | `03ecf1cd00e115c47727147fe62f513eaf0906a011fc488af0b8658b27cc6322` |

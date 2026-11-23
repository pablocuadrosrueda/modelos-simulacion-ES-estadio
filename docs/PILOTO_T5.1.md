# Piloto T5.1 · X0–X7

> Histórico: este lote usó X6 en +20 y no incluía X5 con nueve. El piloto
> actualizado de T5.3 está en `results/final/pilot`; no mezclar ambos diseños.

**Estado:** piloto de diez réplicas por escenario; resultados provisionales, no la entrega definitiva.

12 escenarios, 120 réplicas de 48.775 espectadores; semillas comunes 20261105–20261114. No se han alterado parámetros del modelo ni hipótesis de X6/I3. Todas las réplicas terminan completas, con identidades únicas y exactamente un estado terminal por espectador.

## Reproducir y consultar

```bash
.venv/bin/python scripts/run_pilot.py --reps 10 --output results/pilot_repetido
```

El script evita sobrescribir resultados. Los CSV revisables están en [results/pilot](../results/pilot). `kpis.csv` mantiene el contrato original; `summary.csv` contiene media, semianchura y n válido. `comparisons.csv` usa diferencias emparejadas por semilla y las referencias indicadas abajo. `groups.csv` mide P4 con mayores/PMR y resto iguales en X0/X3, sin cambiar recorridos (D32). Los NaN se conservan para indicadores que no aplican. No se tratan espectadores como réplicas independientes.

## Procedencia y auditoría

- Código del lote: `fe9e64dee8517d94105449d63a20c726ce373e98`; análisis de cohortes: `54cbabd67a7fc106e55e01cdff16931b4f311e51`.
- Python 3.12.14; versiones, hashes de fuentes y configs resueltas en [manifest.json](../results/pilot/manifest.json).
- Para recuperar cohortes de P4 se repitieron X0 y X3 con las mismas diez semillas: 20 recálculos, cuyos KPIs originales se verificaron iguales con tolerancia 1e-12. No cuentan como réplicas nuevas.
- Cero espectadores pendientes en las 120 réplicas. Tiempo acumulado del lote y KPIs: 298.91 s (2.49 s/réplica; rango 1.95–3.85 s), sin incluir la recuperación posterior de P4.
- Reparto observado por zona entre 24.484 % y 25.406 % por réplica. La validación del ritmo por torno de A está en [VERIFICACION.md](VERIFICACION.md), T2.1 fusionada en PR #25.

## Acceso · medias entre réplicas

El IC del 95 % se expresa como media ± semianchura. P95 y porcentajes son medias de los KPIs de réplica.

| Escenario | Espera (min), IC 95 % | P95 (min) | Espera <10 min (%) | Entrada tardía (%) |
|---|---:|---:|---:|---:|
| X0_base | 0.186 ± 0.039 | 1.066 | 100.000 | 4.471 |
| X1_2tornos | 3.986 ± 0.121 | 11.636 | 89.180 | 20.225 |
| X1_4tornos | 0.015 ± 0.003 | 0.072 | 100.000 | 3.729 |
| X2_anticipado | 0.048 ± 0.007 | 0.181 | 100.000 | 2.594 |
| X3_prioridad | 0.186 ± 0.039 | 1.080 | 100.000 | 4.474 |
| X4_escalonada | 0.186 ± 0.039 | 1.066 | 100.000 | 4.471 |
| X5_3acomodadores | 0.186 ± 0.039 | 1.066 | 100.000 | 14.147 |
| X5_6acomodadores | 0.186 ± 0.039 | 1.066 | 100.000 | 7.250 |
| X6_con_redireccion | 0.186 ± 0.039 | 1.066 | 100.000 | 4.471 |
| X6_sin_redireccion | 0.189 ± 0.039 | 1.075 | 100.000 | 4.471 |
| X7_salida_bloqueada | 0.186 ± 0.039 | 1.066 | 100.000 | 4.471 |
| X7_todas_salidas | 0.186 ± 0.039 | 1.066 | 100.000 | 4.471 |

## Salida y evacuación

| Escenario | Salida (min), IC 95 % | Cola máxima salida (personas, media) | Evacuación (min), IC 95 % | Seguros a 8 min (%, media) |
|---|---:|---:|---:|---:|
| X0_base | 8.338 ± 0.023 | 1459.800 | — ± — | — |
| X1_2tornos | 8.338 ± 0.023 | 1459.800 | — ± — | — |
| X1_4tornos | 8.338 ± 0.023 | 1459.800 | — ± — | — |
| X2_anticipado | 8.338 ± 0.023 | 1459.800 | — ± — | — |
| X3_prioridad | 8.338 ± 0.023 | 1459.800 | — ± — | — |
| X4_escalonada | 9.284 ± 0.294 | 747.500 | — ± — | — |
| X5_3acomodadores | 32.656 ± 14.174 | 1457.200 | — ± — | — |
| X5_6acomodadores | 8.338 ± 0.023 | 1459.800 | — ± — | — |
| X6_con_redireccion | 8.338 ± 0.023 | 1459.800 | — ± — | — |
| X6_sin_redireccion | 8.338 ± 0.023 | 1459.800 | — ± — | — |
| X7_salida_bloqueada | — ± — | — | 8.445 ± 0.030 | 98.434 |
| X7_todas_salidas | — ± — | — | 7.393 ± 0.205 | 100.000 |

## Contrastes emparejados

Diferencia = alternativa − referencia. Una diferencia negativa reduce ese indicador. El control de X5 tiene la misma probabilidad de conflicto del 1 %, variando solo los acomodadores; X6 y X7 comparan sus propias variantes. P4 usa cohortes comunes de `groups.csv`.

| Alternativa | Referencia | Indicador | Diferencia, IC 95 % | Parejas |
|---|---|---|---:|---:|
| X1_2tornos | X0_base | wait_mean_min | 3.800 ± 0.089 | 10 |
| X1_4tornos | X0_base | wait_mean_min | -0.170 ± 0.038 | 10 |
| X2_anticipado | X0_base | wait_mean_min | -0.138 ± 0.039 | 10 |
| X3_prioridad | X0_base | wait_mean_priority_min | -0.174 ± 0.041 | 10 |
| X3_prioridad | X0_base | wait_mean_rest_min | 0.024 ± 0.006 | 10 |
| X4_escalonada | X0_base | exit_time_min | 0.945 ± 0.300 | 10 |
| X4_escalonada | X0_base | exit_queue_max | -712.300 ± 3.601 | 10 |
| X5_3acomodadores | X5_6acomodadores | conflict_delay_s | 254.067 ± 66.153 | 10 |
| X6_con_redireccion | X6_sin_redireccion | wait_mean_min | -0.003 ± 0.000 | 10 |
| X7_salida_bloqueada | X7_todas_salidas | evac_time_min | 1.052 ± 0.204 | 10 |
| X7_salida_bloqueada | X7_todas_salidas | evac_pct_ref | -1.566 ± 0.106 | 10 |

## Precisión y réplicas definitivas

Objetivo de la memoria: IC 95 % con semianchura ≤5 % de la espera media. Se estima n con la desviación y t del piloto; no es una garantía final. Al ampliar habrá que recalcular el IC. Una espera pequeña hace muy exigente la precisión relativa.

| Escenario | Réplicas piloto | Semianchura relativa (%) | n total estimado | Adicionales estimadas |
|---|---:|---:|---:|---:|
| X0_base | 10 | 21.172 | 180 | 170 |
| X1_2tornos | 10 | 3.026 | 10 | 0 |
| X1_4tornos | 10 | 18.313 | 135 | 125 |
| X2_anticipado | 10 | 14.107 | 80 | 70 |
| X3_prioridad | 10 | 21.242 | 181 | 171 |
| X4_escalonada | 10 | 21.172 | 180 | 170 |
| X5_3acomodadores | 10 | 21.172 | 180 | 170 |
| X5_6acomodadores | 10 | 21.172 | 180 | 170 |
| X6_con_redireccion | 10 | 21.172 | 180 | 170 |
| X6_sin_redireccion | 10 | 20.849 | 174 | 164 |
| X7_salida_bloqueada | 10 | 21.172 | 180 | 170 |
| X7_todas_salidas | 10 | 21.172 | 180 | 170 |

La estimación máxima es **181 réplicas totales**, frente a las ≈30 previstas inicialmente. Si se mantiene el mismo n en los 12 escenarios, serían 2052 ejecuciones adicionales, unos 85 min al ritmo observado en este Mac (sin S1). Las diez semillas del piloto se reutilizan; no se suman dos veces. Puede estimarse n por escenario conservando las semillas comunes en sus réplicas compartidas.

## Lectura provisional y cuestiones antes de cerrar resultados

- P2: dos tornos dan un 89,18 % de esperas inferiores a diez minutos; tres y cuatro dan 100 % en estas diez réplicas. La espera media base es de 0,186 min, unos 11,1 s.
- P4: la prioridad reduce la espera de mayores/PMR en unos 10,46 s frente a FIFO; el resto espera unos 1,46 s más. Son contrastes emparejados con los mismos colectivos.
- P5: escalonar reduce la cola máxima media por salida, pero añade unos 0,95 min al vaciado total. La tabla de contrastes conserva ambas medidas y sus IC.
- P6: el indicador de retraso de conflicto es unos 254 s mayor con tres acomodadores que con seis a probabilidad del 1 %. Este indicador compara tránsitos con/sin conflicto activo según D25, no una diferencia individual contrafactual.
- P7: la redirección reduce la espera global media unos 0,0031 min. El cierre sigue en +20 min (poca llegada), como en las configs; esto no demuestra el comportamiento de un cierre en hora punta. Confirmar con el grupo la intención antes de cambiar el instante.
- P8: con todas las salidas, vaciado completo ≤8 min en 9/10 réplicas; con una bloqueada, 0/10. La media de vaciado es 7,39 frente a 8,45 min; una media menor que ocho no implica cumplir en todos los partidos (máximo observado sin bloqueo: 8,208 min).
- El recuento I3 incluye averías posteriores a la entrada, según D25; no interpretar ese contador como número de averías que perjudicaron a espectadores.
- A ha completado T2.1 (PR #25, [verificación de capacidad](VERIFICACION.md)); A/B llevan T5.4. El piloto no modifica sus módulos.

## Qué sigue

T5.3: ampliar réplicas según la precisión requerida y ejecutar S1, conservando las semillas comunes. Después T6.1 genera las gráficas P1–P8; T6.2 verifica/valida con el equipo y T6.3 redacta la memoria de resultados. Las dudas de X6 e I3 deben quedar expresas en la interpretación.

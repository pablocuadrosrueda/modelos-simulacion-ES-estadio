# Resultados T5.3 · X0–X7 y sensibilidad S1

**Campaña completada:** 2,965 réplicas de 19 escenarios, conservando identidad y terminación completa de todos los espectadores.

Los IC del 95 % se expresan como media ± semianchura, usando una observación por réplica (t-Student). Las diferencias se emparejan por semilla. Los tamaños por escenario pueden diferir: se usan todas las parejas comunes disponibles.

## Diseño y procedencia

- X5: conflictos al 1 %, resolución Triangular(1,3,10) min, un conflicto por acomodador; comparación de 3, 6 y 9 por zona (D33). Se conserva la saturación.
- X6: puerta A-1 cerrada en t=−30 durante diez minutos, con/sin redirección (D31). El antiguo piloto en +20 es histórico y no se mezcla con este.
- S1: seis variantes de aforo, velocidad y servicio ya definidas en sus configs.
- Código de simulación/campaña: `fd6475cdf4982b4f2ff9c7dd03dccd8a848f52cb`. Python 3.12.14. Configs resueltas, versiones y hashes: [manifest.json](../results/final/manifest.json).
- [Datos finales](../results/final) y [piloto actualizado](../results/final/pilot). Las semillas son `base_seed + replica`; las del piloto no se cuentan dos veces.

## Precisión alcanzada

Mínimo de treinta réplicas por escenario en la campaña oficial. Se estimó n con el piloto de diez y se amplió hasta verificar que la semianchura del IC de la espera media no excede el 5 % de esa media (D34). Esto fija la precisión de la espera, no un objetivo independiente para cada uno de los demás indicadores.

| Escenario | n válido | Espera media (min) | Semianchura IC (min) | Semianchura relativa (%) |
|---|---|---|---|---|
| S1_N_+10 | 73 | 0.4865 | 0.0219 | 4.5030 |
| S1_N_-10 | 247 | 0.0899 | 0.0038 | 4.1906 |
| S1_serv_+25 | 30 | 1.4016 | 0.0499 | 3.5584 |
| S1_serv_-25 | 219 | 0.0311 | 0.0015 | 4.9865 |
| S1_vel_+15 | 180 | 0.1923 | 0.0084 | 4.3426 |
| S1_vel_-15 | 180 | 0.1923 | 0.0084 | 4.3426 |
| X0_base | 180 | 0.1923 | 0.0084 | 4.3426 |
| X1_2tornos | 30 | 4.0164 | 0.0776 | 1.9320 |
| X1_4tornos | 183 | 0.0159 | 0.0007 | 4.6893 |
| X2_anticipado | 138 | 0.0504 | 0.0025 | 4.9657 |
| X3_prioridad | 181 | 0.1924 | 0.0083 | 4.3205 |
| X4_escalonada | 180 | 0.1923 | 0.0084 | 4.3426 |
| X5_3acomodadores | 180 | 0.1923 | 0.0084 | 4.3426 |
| X5_6acomodadores | 180 | 0.1923 | 0.0084 | 4.3426 |
| X5_9acomodadores | 180 | 0.1923 | 0.0084 | 4.3426 |
| X6_con_redireccion | 199 | 0.2427 | 0.0090 | 3.7112 |
| X6_sin_redireccion | 45 | 0.4027 | 0.0176 | 4.3704 |
| X7_salida_bloqueada | 180 | 0.1923 | 0.0084 | 4.3426 |
| X7_todas_salidas | 180 | 0.1923 | 0.0084 | 4.3426 |

## Acceso · escenarios principales

| Escenario | n | Espera (min) | P95 (min) | Espera <10 min (%) | Entrada tardía (%) |
|---|---|---|---|---|---|
| X0_base | 180 | 0.1923 ± 0.0084 | 1.1497 ± 0.0685 | 100.0000 ± 0.0000 | 4.5778 ± 0.0516 |
| X1_2tornos | 30 | 4.0164 ± 0.0776 | 11.7639 ± 0.2661 | 88.9583 ± 0.7353 | 20.3032 ± 0.2029 |
| X1_4tornos | 183 | 0.0159 ± 0.0007 | 0.0757 ± 0.0017 | 100.0000 ± 0.0000 | 3.7538 ± 0.0158 |
| X2_anticipado | 138 | 0.0504 ± 0.0025 | 0.2085 ± 0.0118 | 100.0000 ± 0.0000 | 2.6045 ± 0.0145 |
| X3_prioridad | 181 | 0.1924 ± 0.0083 | 1.1605 ± 0.0725 | 100.0000 ± 0.0000 | 4.5805 ± 0.0515 |
| X4_escalonada | 180 | 0.1923 ± 0.0084 | 1.1497 ± 0.0685 | 100.0000 ± 0.0000 | 4.5778 ± 0.0516 |
| X5_3acomodadores | 180 | 0.1923 ± 0.0084 | 1.1497 ± 0.0685 | 100.0000 ± 0.0000 | 14.5493 ± 0.2813 |
| X5_6acomodadores | 180 | 0.1923 ± 0.0084 | 1.1497 ± 0.0685 | 100.0000 ± 0.0000 | 7.1947 ± 0.1389 |
| X5_9acomodadores | 180 | 0.1923 ± 0.0084 | 1.1497 ± 0.0685 | 100.0000 ± 0.0000 | 5.1316 ± 0.0687 |
| X6_con_redireccion | 199 | 0.2427 ± 0.0090 | 1.3601 ± 0.0585 | 100.0000 ± 0.0000 | 4.6445 ± 0.0517 |
| X6_sin_redireccion | 45 | 0.4027 ± 0.0176 | 1.7741 ± 0.1925 | 99.7170 ± 0.1428 | 5.2472 ± 0.1084 |
| X7_salida_bloqueada | 180 | 0.1923 ± 0.0084 | 1.1497 ± 0.0685 | 100.0000 ± 0.0000 | 4.5778 ± 0.0516 |
| X7_todas_salidas | 180 | 0.1923 ± 0.0084 | 1.1497 ± 0.0685 | 100.0000 ± 0.0000 | 4.5778 ± 0.0516 |

## Contrastes emparejados

Diferencia = alternativa − referencia; una cifra negativa reduce el indicador. X1–X4 y S1 usan X0; X5 usa seis acomodadores; X6 usa sin redirección y X7, todas las salidas. Para P4 se usan los mismos colectivos en X0/X3 (D32), sin alterar los KPIs originales de `kpis.csv`.

| Alternativa | Referencia | Indicador (unidad en su nombre) | Diferencia, IC 95 % | Parejas |
|---|---|---|---|---|
| X1_2tornos | X0_base | wait_mean_min | 3.8320 ± 0.0666 | 30 |
| X1_4tornos | X0_base | wait_mean_min | -0.1764 ± 0.0078 | 180 |
| X2_anticipado | X0_base | wait_mean_min | -0.1418 ± 0.0093 | 138 |
| X3_prioridad | X0_base | wait_mean_priority_min | -0.1814 ± 0.0083 | 180 |
| X3_prioridad | X0_base | wait_mean_rest_min | 0.0248 ± 0.0011 | 180 |
| X4_escalonada | X0_base | exit_time_min | 1.2239 ± 0.1050 | 180 |
| X4_escalonada | X0_base | exit_queue_max | -713.8778 ± 0.5731 | 180 |
| X5_3acomodadores | X5_6acomodadores | conflict_delay_s | 254.8879 ± 9.8997 | 180 |
| X5_9acomodadores | X5_6acomodadores | conflict_delay_s | -30.1717 ± 1.9347 | 180 |
| X6_con_redireccion | X6_sin_redireccion | wait_mean_min | -0.1596 ± 0.0072 | 45 |
| X7_salida_bloqueada | X7_todas_salidas | evac_time_min | 0.9505 ± 0.0460 | 180 |
| X7_salida_bloqueada | X7_todas_salidas | evac_pct_ref | -1.4391 ± 0.0284 | 180 |
| S1_N_+10 | X0_base | wait_mean_min | 0.2867 ± 0.0114 | 73 |
| S1_N_-10 | X0_base | wait_mean_min | -0.1036 ± 0.0050 | 180 |
| S1_serv_+25 | X0_base | wait_mean_min | 1.2172 ± 0.0341 | 30 |
| S1_serv_-25 | X0_base | wait_mean_min | -0.1613 ± 0.0069 | 180 |
| S1_vel_+15 | X0_base | wait_mean_min | 0.0000 ± 0.0000 | 180 |
| S1_vel_-15 | X0_base | wait_mean_min | 0.0000 ± 0.0000 | 180 |

## P6 · Acomodadores

La duración I1 medida incluye espera por acomodador y resolución. La resolución por sí sola tiene media teórica 4.667 min; su rango no limita la duración total cuando hay cola. Nueve puede reducir mucho la espera sin eliminarla. El indicador `conflict_delay_s` mide el contraste en otros espectadores de D25; no debe confundirse con la duración del conflicto de su causante.
Comprobación orientativa con las configs: unos 121.9 conflictos por macrozona requieren 569.0 minutos de trabajo de acomodador. Con pocos acomodadores esa carga se acumula, aunque cada resolución individual esté dentro del rango especificado.

| Escenario | n | Duración media I1 (min), IC 95 % | P95 I1 (min, media) | Mayor I1 observado (min) | Último asiento observado (t, min) |
|---|---|---|---|---|---|
| X5_3acomodadores | 180 | 44.6004 ± 0.4768 | 91.1064 | 116.2181 | 179.5733 |
| X5_6acomodadores | 180 | 13.7437 ± 0.2063 | 30.1717 | 47.3147 | 70.1294 |
| X5_9acomodadores | 180 | 6.6442 ± 0.0925 | 13.0399 | 24.8594 | 40.5353 |

## P7 · Cierre en hora punta

Colectivo afectado: asignados a A-1 que llegan durante [−30,−20). Su espera no es la media global de todo el estadio. No se cambia la hipótesis D23 sobre quienes ya estaban en cola al cerrarse la puerta.

| Escenario | n | Llegadas afectadas (media) | Redirigidos (media) | Espera de afectados (min), IC 95 % |
|---|---|---|---|---|
| X6_con_redireccion | 199 | 382.4573 | 382.4573 | 0.5433 ± 0.0260 |
| X6_sin_redireccion | 45 | 383.3111 | 0.0000 | 9.6259 ± 0.1204 |

## P8 · Evacuación

Una media de vaciado menor que ocho minutos no implica que todos los partidos cumplan. Se informa también cuántas réplicas vacían por completo antes de ocho minutos y el porcentaje de personas a salvo a ese instante.

| Escenario | n | Vaciado (min), IC 95 % | Seguros a 8 min (%), IC 95 % | Vaciado total ≤8 min | Máximo vaciado (min) |
|---|---|---|---|---|---|
| X7_salida_bloqueada | 180 | 8.4200 ± 0.0140 | 98.5607 ± 0.0284 | 0/180 | 9.3576 |
| X7_todas_salidas | 180 | 7.4694 ± 0.0516 | 99.9998 ± 0.0001 | 163/180 | 9.3576 |

## S1 · Sensibilidad

Cada variante cambia un parámetro respecto a X0. S1 hereda salida ordinaria sin alarma: estos resultados no constituyen una sensibilidad de evacuación.

| Escenario | n | Espera (min) | Acceso (min) | Tardíos (%) | Salida (min) |
|---|---|---|---|---|---|
| S1_N_+10 | 73 | 0.4865 ± 0.0219 | 2.2722 ± 0.0214 | 6.2844 ± 0.1154 | 9.1130 ± 0.0111 |
| S1_N_-10 | 247 | 0.0899 ± 0.0038 | 1.8652 ± 0.0038 | 4.0289 ± 0.0252 | 7.6822 ± 0.0389 |
| S1_serv_+25 | 30 | 1.4016 ± 0.0499 | 3.1930 ± 0.0497 | 11.1983 ± 0.1772 | 8.3360 ± 0.0132 |
| S1_serv_-25 | 219 | 0.0311 ± 0.0015 | 1.7952 ± 0.0018 | 3.7751 ± 0.0174 | 8.3677 ± 0.0167 |
| S1_vel_+15 | 180 | 0.1923 ± 0.0084 | 1.7741 ± 0.0084 | 4.1731 ± 0.0520 | 8.2807 ± 0.0051 |
| S1_vel_-15 | 180 | 0.1923 ± 0.0084 | 2.2472 ± 0.0084 | 5.1396 ± 0.0517 | 8.7326 ± 0.0572 |

## Alcance y siguiente paso

Los resultados comparan escenarios del modelo de la Parte 1, ampliado según D31/D33. I3 cuenta todas las averías registradas, incluso después de la entrada (D25); no equivale al número de averías que afectaron a personas. La capacidad analítica y el rendimiento están en [VERIFICACION.md](VERIFICACION.md).

Sigue T6.1 (gráficas P1–P8), T6.2 (verificación/validación conjunta) y T6.3 (memoria de resultados, justificando X6 en −30 y la variante de nueve en X5).

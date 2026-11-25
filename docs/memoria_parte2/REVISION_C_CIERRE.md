# Cierre de la aportación C · revisión del 25 de noviembre de 2026

Revisión sobre `main` en `eeea932` (integración inicial de A, PR #40).
Solo se corrigen fuentes y PDF de C y se actualiza el contexto. No se modifican
el LaTeX de A, los textos de B, el modelo, las configuraciones o los resultados.

## Correcciones de C

- C2: la diferencia de vaciado con velocidad +15 % es exactamente
  -0,0861497117744193 min. A cuatro decimales: **-0,0861 ± 0,0182 min**,
  con 180 parejas. Corregidos Markdown y PDF; buscada la cifra en C1–C3.
  Las menciones anteriores en el informe de coherencia son el registro histórico
  del error, no resultados vigentes.
- C3, P7: añadidos IC del 95 % y tamaños del colectivo afectado. Sin redirección:
  **9,6259 ± 0,1204 min, n = 45**. Con redirección:
  **0,5433 ± 0,0260 min, n = 199**. Fuente: auditoría definitiva por réplica.
- PDF C reexportado, 11 páginas; comprobados los cambios en el texto extraído,
  los hashes de las tres fuentes y la maquetación renderizada.
- T6.1: confirmado que figura **hecha** en ESTADO/TAREAS y que PR #30 está
  fusionado; no queda ese cambio pendiente del rol C.

## Revisión de la memoria única de A

Se ha compilado el LaTeX sin modificarlo, con XeLaTeX/TeX Live 2025, generando un
PDF de 26 páginas en un directorio temporal. Se ha leído el contenido de C y
revisado su maquetación. Los números de página siguientes son físicos del PDF,
incluida la portada; la numeración impresa es una unidad menor.

| Elemento revisado | Comprobación | Resultado |
|---|---|---|
| Tabla 4, campaña (p. 11) | Los 19 tamaños y semianchuras relativas frente a precisión definitiva | Coinciden; total 2.965, máximo 4,9865 % |
| Método y denominadores (pp. 10–12) | IC t-Student, diferencias antes del IC, n de parejas, colectivos de P4, afectados de P7 y evacuables de P8 | Conserva las definiciones de C |
| P5/P6/P7/P8 (pp. 20–23) | Medias e IC, unidades y tamaños frente a resumen, contrastes y auditoría | Sin discrepancias numéricas en lo revisado |
| P7 frente a X0 (p. 22) | Contraste con semillas comunes | +0,04989 ± 0,00346 min, 180 parejas; el redondeo de A es correcto |
| Tabla 19, S1 (p. 24) | Seis variantes: 18 medias y sus semianchuras, más los tamaños de parejas | Todas coinciden al redondeo declarado, incluido -0,0861 |
| P8 (p. 23) | Frecuencia de vaciado en plazo y porcentaje de personas | 163/180 y 0/180; no se confunde con una garantía por una media <8 |
| Sensibilidad y conclusiones (pp. 24–25) | Alcance de un factor, S1 sin alarma, límites y generalización | Mantiene las limitaciones de C |

No hace falta corregir cifras de C en el LaTeX de A. Como mejora de legibilidad,
la figura compuesta S1 queda pequeña a ancho de página; A puede separar sus
paneles o ampliarla en la maquetación final. La tabla 19 permite leer las cifras.

## Reproducción posterior a la integración

Se ha ejecutado `scripts/verify_results.py --replay` con el código de `main`
`eeea932`, sin cambios de scripts o módulos en esta rama. Las 19 réplicas (una
por escenario, semilla 20261105) reproducen los 21 KPIs y las auditorías.
Se actualiza `docs/VERIFICACION_C_T6.2.md`. Estas reproducciones no amplían la
muestra de T5.3 ni modifican los CSV originales.

## Pendientes fuera del cierre de C

- B: reproducir o retirar el contraste sin conflictos y completar las cifras
  señaladas en sus instrucciones de cierre.
- Grupo: confirmar la hipótesis de la cola ya formada al cerrar una puerta y
  la fecha que se pondrá en portada. No se toma esa decisión por el grupo.
- F2: sigue sin contraste directo; mantener la limitación si no se aporta la fuente.
- A: aplicar lo resuelto en el LaTeX, retirar las marcas pendientes que procedan
  y recompilar la memoria conjunta. T6.3 global no se declara terminada.

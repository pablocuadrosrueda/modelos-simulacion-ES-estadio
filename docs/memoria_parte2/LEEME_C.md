# T6.3 · Aportación del rol C

Chema pide preparar **solo su parte C**, para revisión e integración con A y B.

| Archivo | Uso |
|---|---|
| [C1_metodo_estadistico_y_campana.md](C1_metodo_estadistico_y_campana.md) | Runner, indicadores, denominadores, IC, emparejamiento, precisión y campaña |
| [C2_sensibilidad.md](C2_sensibilidad.md) | S1 y sus límites; figura y tabla de diferencias emparejadas |
| [C3_conclusiones_y_limites.md](C3_conclusiones_y_limites.md) | Síntesis de P1–P8, cambios de diseño, límites y conclusión conjunta propuesta |
| [Memoria_Parte2_C.pdf](Memoria_Parte2_C.pdf) | Versión de lectura de 11 páginas; no es la memoria conjunta definitiva |

Los Markdown son las fuentes editables. El PDF incluye sus hashes SHA-256, tablas
y tres paneles de sensibilidad separados para facilitar la lectura. Se ha
maquetado con ReportLab y revisado página por página; las figuras del PDF usan
los mismos contrastes de `results/final/comparisons.csv` que la figura S1.
Tras editar las fuentes, la versión PDF debe reexportarse y revisarse de nuevo.

## Correcciones de cierre

Aplicadas las instrucciones de ESTADO: redondeo S1 a −0,0861, IC/n de X6 en
C3 y revisión de la memoria integrada de A. PDF actualizado. Evidencia y
pendientes externos en [REVISION_C_CIERRE.md](REVISION_C_CIERRE.md).

## Integración con el equipo

- A tiene su borrador de entrada y P1–P4/P7 en el [PR #34](https://github.com/pablocuadrosrueda/modelos-simulacion-ES-estadio/pull/34).
  C1 resuelve los cruces sobre método y colectivos; C3 confirma el contraste
  adicional de X6 con X0. No se han copiado ni modificado los capítulos de A.
- B conserva la explicación de ubicación, salida, evacuación e I1/I4 y las
  respuestas detalladas P5/P6/P8. C3 recoge su diagnóstico documentado de las
  superaciones de ocho minutos en X7 (`docs/VALIDACION_T6.2.md`).
- La integración final debe conservar una sola explicación de métodos, las
  referencias a figuras/tablas y la distinción entre resultado del modelo y
  validación externa. T6.3 sigue en curso hasta revisar la memoria conjunta.
- Las etiquetas P3/P6 de las figuras se han corregido: la entrada tardía incluye
  el recorrido; no se ha cambiado el indicador ni ninguna cifra de T5.3.

El guion exige explicitar diferencias respecto a Parte 1. C3 recoge X6 en -30,
X5 con nueve, tamaños por precisión y la corrección de carga anticipada. El guion
no fija un formato específico para esta aportación: se conserva el borrador por
secciones del equipo. La Parte 1 PDF no se modifica.

## Contraste adicional pedido por A: X6 con redirección frente a X0

No está en `comparisons.csv`, porque la referencia oficial de X6 es **sin**
redirección. Sin modificar esa tabla se obtiene, con 180 parejas comunes,
**+0,04989093 ± 0,00346223 min**. No se restan las medias de muestras de 199 y 180.

Desde la raíz del clon:

```bash
.venv/bin/python - <<'PY'
import pandas as pd
from sanmames.analysis import confidence_interval
k = pd.read_csv('results/final/kpis.csv')
p = k.pivot(index='seed', columns='scenario', values='wait_mean_min')
p = p[['X6_con_redireccion', 'X0_base']].dropna()
d = p.X6_con_redireccion - p.X0_base
print('Parejas:', len(d), 'Media y semianchura (min):', confidence_interval(d))
PY
```

Para revisar el PDF en macOS:

```bash
open docs/memoria_parte2/Memoria_Parte2_C.pdf
```

Verificación de tablas sin simular ni sobrescribir la evidencia histórica:

```bash
.venv/bin/python scripts/verify_results.py --output /tmp/verificacion_C.md
make check
```

Fuentes utilizadas: datos finales y manifiesto de T5.3, figuras T6.1, informes de
verificación T6.2 y guion de prácticas aportado por Chema. La explicación se
limita a simulación terminante, réplicas, t-Student y sensibilidad de un factor;
no se añaden técnicas estadísticas o funcionalidades al modelo.

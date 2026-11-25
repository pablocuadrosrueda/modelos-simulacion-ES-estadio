# Entrega de la Parte 2

Qué se entrega, dónde está y cómo reproducirlo. Entrega de la memoria: 12 de
diciembre de 2026; defensa: 14 o 17 de diciembre.

## Qué se entrega

| Elemento | Dónde | Notas |
|---|---|---|
| Memoria de la Parte 2 (PDF) | `docs/memoria_parte2/Memoria_Parte2.pdf` | 26 páginas. Compilada desde la fuente LaTeX |
| Fuente de la memoria | `docs/memoria_parte2/latex/` | `main.tex` y un `.tex` por sección. Las figuras se leen de `results/figures` |
| Memoria de la Parte 1 | `docs/Memoria_San_Mames-2.pdf` | Sin cambios; las correcciones están en la sección 3 de la Parte 2 |
| Código del modelo | `src/sanmames/`, `configs/`, `scripts/` | Python 3 + SimPy. Instrucciones en `README.md` |
| Tests | `tests/` | `make check` (lint + pytest) |
| Datos definitivos | `results/final/` | 2.965 réplicas de 19 escenarios: tablas agregadas y `manifest.json` con commit, configs, versiones y semillas |
| Figuras | `results/figures/` | P1–P8 y S1, PNG (300 ppp) y SVG, con `statistics.csv` y hashes |
| Verificación y validación | `docs/VERIFICACION.md`, `docs/VALIDACION_T6.2.md`, `docs/VERIFICACION_C_T6.2.md` | Partes de A, B y C |
| Informe de la campaña | `docs/RESULTADOS_T5.3.md` | Tablas con IC y n |
| Borradores por rol | `docs/memoria_parte2/A*.md`, `B*.md`, `C*.md` | Fuente de las cifras de la memoria; coherencia en `INFORME_COHERENCIA.md` |

## Cómo compilar la memoria

Requiere TeX Live con XeLaTeX y la fuente Inter (incluida en TeX Live 2026).

```bash
cd docs/memoria_parte2/latex
latexmk -xelatex -outdir=build main.tex     # genera build/main.pdf
cp build/main.pdf ../Memoria_Parte2.pdf     # actualizar el PDF que se entrega
```

Comprobado el 2026-11-25 con TeX Live 2026: sin errores, sin cajas desbordadas
y sin referencias rotas.

## Cómo reproducir los datos

```bash
make install                                   # entorno e instalación editable
make check                                     # lint + tests
.venv/bin/python scripts/run_campaign.py --output results/campana_nueva --workers 4
.venv/bin/python scripts/report_campaign.py    # informe de results/final
.venv/bin/python scripts/plot_results.py       # figuras desde results/final
.venv/bin/python scripts/verify_results.py --replay   # repite una réplica por escenario
```

* La campaña original tardó unos 50 minutos de reloj (3.031 s según
  `results/final/manifest.json`); el tiempo depende del número de procesos
  (`--workers`). Usar una carpeta nueva para no sobrescribir `results/final`.
  Las semillas son `20261105 + r`.
* `verify_results.py --replay` comprueba, sin escribir en `results/final`, que
  el código actual reproduce una réplica de cada escenario con sus 21 KPIs.
* Si la ruta del repositorio contiene `:`, el entorno está en
  `~/.venvs/modelos-simulacion-ES-estadio` (`make venv-path`).

## Pendientes manuales antes de entregar

1. **Revisar el PDF** antes de entregarlo. La fecha de la portada ya está
   puesta (12 de diciembre de 2026, `\fechaentrega` en `main.tex`) y no queda
   ningún texto en rojo.
2. **Corregir la Parte 1** según la sección 3 de la memoria (ρ de X2 = 0,81 y
   cierre en t = −30 min), si el guion lo pide; el PDF de la Parte 1 no se ha
   modificado.
3. **Fuente F2.** La memoria contrasta el ritmo por torno con la cifra que la
   Parte 1 atribuye a F2 (15 pers/min) y lo declara como limitación: no se ha
   comprobado en el artículo original. Si alguien tiene el artículo, se puede
   confirmar y retirar la limitación.

## Ficheros que no deben entregarse

Ninguno está versionado (los ignora `.gitignore`), pero conviene no incluirlos si
se entrega una copia de la carpeta en lugar del repositorio:

* `.venv/` o el entorno de `~/.venvs/`, `src/sanmames.egg-info/`.
* Cachés: `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.DS_Store`.
* Compilación de la memoria: `docs/memoria_parte2/latex/build/` y `build.log`.
* Salidas de pruebas locales en `results/`: `X6_con_redireccion_kpis.csv`,
  `X6_sin_redireccion_kpis.csv`, `estudio_x6.csv` y los checkpoints de campaña.

`results/pilot/` (piloto de T5.1, con X6 en +20) está versionado pero es
histórico; se conserva por trazabilidad y la memoria no lo usa.

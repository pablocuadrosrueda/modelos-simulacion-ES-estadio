# `python -m venv` rechaza rutas con ':' (p. ej. ".../26:27/..."). En ese caso el
# entorno se crea fuera del repo. Se puede forzar con `make install VENV=/ruta`.
ifneq (,$(findstring :,$(CURDIR)))
VENV ?= $(HOME)/.venvs/modelos-simulacion-ES-estadio
else
VENV ?= .venv
endif
PY     := $(VENV)/bin/python
PYTHON ?= python3
EXP    ?= X0
REPS   ?= 1

.PHONY: install test lint format run run-base venv-path
install:
	$(PYTHON) -m venv "$(VENV)"
	"$(PY)" -m pip install -q -U pip
	"$(PY)" -m pip install -q -e ".[dev]"
test:
	"$(PY)" -m pytest -q
lint:
	"$(PY)" -m ruff check src tests scripts
	"$(PY)" -m ruff format --check src tests scripts
format:
	"$(PY)" -m ruff check --fix src tests scripts
	"$(PY)" -m ruff format src tests scripts
run:
	"$(PY)" scripts/run_experiment.py $(EXP) --reps $(REPS)
run-base:
	"$(PY)" scripts/run_experiment.py X0 --reps 1
venv-path:
	@echo "$(VENV)"

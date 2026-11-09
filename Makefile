PY := nepse-msc/bin/python
VENV := nepse-msc

.PHONY: help bootstrap install lock test test-fast nb nb00 freeze smoke status

help:
	@echo "bootstrap  create venv (uv, python 3.11)"
	@echo "install    install deps into venv (uv - fast)"
	@echo "lock       freeze requirements-lock.txt"
	@echo "test       full pytest suite (incl. nbmake smoke notebook)"
	@echo "test-fast  pytest without notebooks"
	@echo "nb00       regenerate + execute notebooks/00_smoke_test.ipynb"
	@echo "smoke      extract NABIL 2024-12 sample from local archive + DuckDB init"

bootstrap:
	uv venv $(VENV) --python 3.11

install:
	uv pip install --python $(PY) -r requirements.txt
	uv pip install --python $(PY) -e . --no-deps

lock:
	uv pip freeze --python $(PY) > requirements-lock.txt

test: test-fast
	-$(PY) -m pytest tests/smoke_nb --nbmake -x || true

test-fast:
	$(PY) -m pytest -m "not network" -m "not slow"

nb00:
	$(PY) scripts/make_nb00.py
	$(PY) -m jupyter nbconvert --to notebook --execute --inplace notebooks/00_smoke_test.ipynb

smoke:
	$(PY) scripts/extract_sample_month.py
	$(PY) scripts/init_duckdb_load_sample.py

freeze:
	$(PY) scripts/write_sample_hhi_table.py

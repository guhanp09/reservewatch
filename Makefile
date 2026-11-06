PYTHON ?= python3

.PHONY: run app test lint verify
run:
	reservewatch run
app:
	streamlit run app.py --server.port 8514
test:
	$(PYTHON) -m pytest -q
lint:
	$(PYTHON) -m ruff check src tests
verify: test lint
	$(PYTHON) scripts/verify_artifacts.py

SHELL := /bin/bash
ROOT  := $(HOME)/storesignal-ai
PY    := $(ROOT)/.venv/bin/python

.PHONY: help pipeline mock ingest normalize classify policy radar route fuse \
        alerts briefs evaluate graph forecast status serve ui test coverage \
        entities lint clean

help:
	@echo "StoreSignal AI — make targets"
	@echo "  pipeline   full end-to-end rebuild"
	@echo "  test       pytest"
	@echo "  lint       ruff"
	@echo "  serve      FastAPI on :8000"
	@echo "  ui         Streamlit on :8501"

pipeline:  ; $(PY) -m storesignal.pipeline
mock:      ; $(PY) -m storesignal.generate_mock_data
ingest:    ; $(PY) -m storesignal.ingestion
normalize: ; $(PY) -m storesignal.normalization
classify:  ; $(PY) -m storesignal.classification
policy:    ; $(PY) -m storesignal.risk_policy
radar:     ; $(PY) -m storesignal.detection
route:     ; $(PY) -m storesignal.routing
fuse:      ; $(PY) -m storesignal.fusion
alerts:    ; $(PY) -m storesignal.alerts
briefs:    ; $(PY) -m storesignal.briefs
evaluate:  ; $(PY) -m storesignal.evaluate
graph:     ; $(PY) -m storesignal.relationship_graph
forecast:  ; $(PY) -m storesignal.forecasting
status:    ; $(PY) -m storesignal.cli status
entities:  ; $(PY) -m storesignal.data_models

serve:     ; $(ROOT)/.venv/bin/uvicorn storesignal.api:app --reload --port 8000
ui:        ; $(ROOT)/.venv/bin/streamlit run src/storesignal/ui.py --server.port 8501

test:      ; cd $(ROOT) && $(PY) -m pytest -q tests
coverage:  ; cd $(ROOT) && $(PY) -m pytest --cov=src --cov-report=term-missing --cov-report=html:data/evaluation/coverage tests
lint:      ; cd $(ROOT) && $(PY) -m ruff check src tests

clean:
	@rm -f data/processed/*.parquet data/processed/*.json data/processed/*.graphml data/processed/audit.log data/processed/idempotency.jsonl 2>/dev/null || true
	@rm -rf data/processed/briefs 2>/dev/null || true
	@echo "cleaned generated artifacts"

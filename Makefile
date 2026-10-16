PY  := $(HOME)/storesignal-ai/.venv/bin/python
SRC := $(HOME)/storesignal-ai/src
PROC := $(HOME)/storesignal-ai/data/processed

.PHONY: help pipeline mock ingest normalize classify policy radar route fuse alerts briefs evaluate graph forecast status serve ui test lint clean

help:
	@echo "Targets: pipeline serve ui test lint clean"
	@echo "         plus per-stage targets (mock, ingest, normalize, classify,"
	@echo "         policy, radar, route, fuse, alerts, briefs, evaluate,"
	@echo "         graph, forecast, status)"

pipeline:   ; $(PY) $(SRC)/run_pipeline.py
mock:       ; $(PY) $(SRC)/generate_mock_data.py
ingest:     ; $(PY) $(SRC)/ingestion.py
normalize:  ; $(PY) $(SRC)/normalization.py
classify:   ; $(PY) $(SRC)/classification.py
policy:     ; $(PY) $(SRC)/risk_policy.py
radar:      ; $(PY) $(SRC)/detection.py
route:      ; $(PY) $(SRC)/routing.py
fuse:       ; $(PY) $(SRC)/fusion.py
alerts:     ; $(PY) $(SRC)/alerts.py
briefs:     ; $(PY) $(SRC)/briefs.py
evaluate:   ; $(PY) $(SRC)/evaluate.py
graph:      ; $(PY) $(SRC)/relationship_graph.py
forecast:   ; $(PY) $(SRC)/forecasting.py
status:     ; $(PY) $(SRC)/cli.py status
serve:      ; $(HOME)/storesignal-ai/.venv/bin/uvicorn api:app --reload --app-dir $(SRC) --port 8000
ui:         ; $(HOME)/storesignal-ai/.venv/bin/streamlit run $(SRC)/ui.py --server.port 8501
test:       ; cd $(HOME)/storesignal-ai && $(PY) -m pytest -q tests
coverage:   ; cd $(HOME)/storesignal-ai && $(PY) -m pytest --cov=src --cov-report=term-missing --cov-report=html:data/evaluation/coverage tests
entities:   ; $(PY) $(SRC)/data_models.py
lint:       ; cd $(HOME)/storesignal-ai && $(PY) -m ruff check src tests
clean:
	rm -rf $(PROC)/*.parquet $(PROC)/*.json $(PROC)/*.jsonl $(PROC)/*.log $(PROC)/briefs $(HOME)/storesignal-ai/models/*.joblib
	@echo "Cleaned generated artifacts."

> **Deployment:** see [DEPLOYMENT.md](DEPLOYMENT.md). **Handoff context:** see [HANDOFF.md](HANDOFF.md).

# StoreSignal AI — Voice-of-Store Engine

**Repo:** https://github.com/lalith2k5/AP-HACKTHON  
**Hackathon:** Talent AP Mega Hackathon — Track R5

Retail operations intelligence layer. Early-warning and incident-resolution
for multilingual store feedback.

## Quick start

    set +H
    cd "$HOME/storesignal-ai"

    # Full pipeline (~30s, deterministic)
    "$HOME/storesignal-ai/.venv/bin/python" -m storesignal.pipeline

    # Tests + lint
    "$HOME/storesignal-ai/.venv/bin/python" -m pytest -q tests
    "$HOME/storesignal-ai/.venv/bin/python" -m ruff check src tests

    # UI (blocks terminal, open http://localhost:8501)
    "$HOME/storesignal-ai/.venv/bin/streamlit" run src/storesignal/ui.py --server.port 8501

    # API (blocks terminal, docs at http://localhost:8000/docs)
    "$HOME/storesignal-ai/.venv/bin/uvicorn" storesignal.api:app --reload --port 8000

## Package layout

- `src/storesignal/` — 30 python modules
- `config/` — 6 YAML files (taxonomy, routing, risk_policy, thresholds, demo, config)
- `data/raw/` — 4 channel JSONL + hidden labels + seeded incidents
- `data/processed/` — pipeline outputs (parquet, json, briefs)
- `data/evaluation/reports/` — evaluation_report.{json,md}

## Environment variables

All 12 `STORESIGNAL_*` variables from spec 5.1 are honored. See
`src/storesignal/settings.py`. Override example:

    STORESIGNAL_DATA_DIR=/tmp/altdata "$HOME/storesignal-ai/.venv/bin/python" -m storesignal.pipeline

## Verified metrics

- Records: 40,053
- Macro-F1 (hidden): 0.9167
- Accuracy (hidden): 0.8910
- Escalation precision: 0.9432
- Seeded incidents: 3 / 3
- Mean lead days: 3.67
- Policy compliance: 100%
- Tests: 18 / 18
- Ruff: clean

## Honest limitations

See HANDOFF.md section 11 for the honest list of what's stubbed vs built.

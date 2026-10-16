# StoreSignal AI — Deployment Guide

**Scope:** local-first MVP deployment. Per spec section 20.5, multi-user
production deployment requires additional work (TLS, SSO, RBAC with real
identity, transactional storage) that is out of scope for this build.

## Architecture (as deployed)

    Browser (localhost:3300)
        |
        v
    Next.js 16 frontend (web/, Node)
        |
        v  x-api-key header
    FastAPI backend (src/storesignal/api.py, :8790)
        |
        +--> data/processed/*.parquet  (pipeline artifacts)
        +--> data/processed/*.jsonl    (overrides, notes, audit)
        +--> models/baseline_model.joblib

    Streamlit UI (src/storesignal/ui.py, :8501) — legacy, parallel, read-only.

## Prerequisites

- macOS 14+, Apple Silicon
- Python 3.11.17 with .venv at $HOME/storesignal-ai/.venv
- Node 20+ / npm 10+ (verified on Node 26.10.0 / npm 11.19.1)
- 97 GB free disk (recommended)

## First-time setup

    set +H
    cd "$HOME/storesignal-ai"

    # Python side
    "$HOME/storesignal-ai/.venv/bin/python" -m pip install -r requirements.txt

    # Run pipeline once to generate artifacts (~30s)
    "$HOME/storesignal-ai/.venv/bin/python" -m storesignal.pipeline

    # Node side
    cd web
    npm install

    # Verify
    "$HOME/storesignal-ai/.venv/bin/python" -m pytest -q tests
    "$HOME/storesignal-ai/.venv/bin/python" -m ruff check src tests
    cd web && npm run build

## Running (3 terminals)

Terminal A — FastAPI on 8790:

    set +H
    cd "$HOME/storesignal-ai"
    "$HOME/storesignal-ai/.venv/bin/uvicorn" storesignal.api:app --port 8790

Terminal B — Next.js on 3300:

    set +H
    cd "$HOME/storesignal-ai/web"
    npm run dev -- --port 3300
    # open http://localhost:3300

Terminal C — Streamlit on 8501 (optional, legacy comparison):

    set +H
    cd "$HOME/storesignal-ai"
    "$HOME/storesignal-ai/.venv/bin/streamlit" run src/storesignal/ui.py --server.port 8501

## Configuration

Backend: `.env` at project root (loaded by settings.py). All 12
STORESIGNAL_* variables documented in `.env.example`.

Key defaults:
    STORESIGNAL_API_KEY=demo-key-storesignal
    STORESIGNAL_DEMO_MODE=true
    STORESIGNAL_ENV=development

Frontend: `web/.env.local` (gitignored).

    NEXT_PUBLIC_API_URL=http://localhost:8790
    NEXT_PUBLIC_STORESIGNAL_API_KEY=demo-key-storesignal

## Demo reset (deterministic clean slate)

    set +H
    curl -X POST http://127.0.0.1:8790/api/v1/demo/reset \
      -H "x-api-key: demo-key-storesignal"

Clears user overrides + notes JSONL, reruns full pipeline (~27s).
Useful before judges walk up.

## Smoke checks

    set +H
    curl -s http://127.0.0.1:8790/health
    curl -s -X PATCH "http://127.0.0.1:8790/api/v1/incidents/INC-..." \
      -H "Content-Type: application/json" \
      -H "x-api-key: demo-key-storesignal" \
      -d '{"actor":"smoke","status":"triaged"}'

## Ports used by this project

    8790  FastAPI
    3300  Next.js dev
    8501  Streamlit (optional)

Ports 3000, 8000 are NOT used to avoid collision with user's other project.

## What is NOT covered here

- TLS, HTTPS termination
- SSO / OIDC authentication
- Multi-user RBAC with real identity
- Transactional database
- Cloud LLM or external APIs (no external dependency)
- Production monitoring/alerting
- Legal/compliance review for real customer data

See PRODUCTION_READINESS.md (spec 20.5) for the full multi-user checklist.

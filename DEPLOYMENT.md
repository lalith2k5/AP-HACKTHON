# StoreSignal AI — Deployment Guide

Local-first, end-to-end deployable. Two auth modes. SQLite transactional
state. Optional TLS via Caddy.

## Ports
    8790  FastAPI (backend)
    3300  Next.js (frontend)
    8180  Keycloak (only when OIDC mode is enabled)
    8443  Caddy TLS (optional, via scripts/serve-tls.sh)
    8501  retired (Streamlit removed)

## Startup (Mode A — static key, default)
    # Terminal 1
    set +H
    cd "$HOME/storesignal-ai"
    ./scripts/run-api.sh

    # Terminal 2
    set +H
    cd "$HOME/storesignal-ai/web"
    npm run dev -- --port 3300

    # Open http://localhost:3300

## Startup (Mode B — OIDC via local Keycloak)
    # Terminal 1 — Keycloak
    set +H
    cd "$HOME/storesignal-ai/deploy/keycloak"
    docker compose up -d

    # Terminal 2 — API (with .env OIDC vars set)
    set +H
    cd "$HOME/storesignal-ai"
    ./scripts/run-api.sh

    # Terminal 3 — Web (with web/.env.local OIDC vars set)
    set +H
    cd "$HOME/storesignal-ai/web"
    npm run dev -- --port 3300

    # Enable OIDC marker
    touch web/.oidc-enabled
    # Restart both servers.

## Enabling / disabling OIDC
    Enable:   touch web/.oidc-enabled
              Add STORESIGNAL_OIDC_ENABLED=true to .env
              Restart both servers.
    Disable:  rm web/.oidc-enabled
              Remove STORESIGNAL_OIDC_ENABLED from .env
              Restart both servers.

## Critical gotcha
    uvicorn does NOT read .env automatically.
    ALWAYS start the backend via ./scripts/run-api.sh, not bare uvicorn.
    Bare `uvicorn storesignal.api:app` silently runs with OIDC disabled.

## Test suites
    # Python (31 tests)
    set +H
    cd "$HOME/storesignal-ai"
    .venv/bin/python -m pytest -q tests

    # Lint
    .venv/bin/python -m ruff check src tests

    # Frontend E2E
    set +H
    cd "$HOME/storesignal-ai/web"
    npx playwright test

## Docker
    set +H
    cd "$HOME/storesignal-ai"
    docker compose build
    docker compose up

    Note: Docker daemon must be running. If `docker info` fails, start
    Docker Desktop. First build downloads ~200MB of base images.

## State persistence
    data/processed/storesignal.db         SQLite (WAL) — overrides, notes, audit
    data/processed/*.parquet              Derived pipeline artifacts
    Re-running the pipeline does NOT erase overrides/notes (separate store).
    Hard reset: POST /api/v1/demo/reset, or delete the SQLite DB manually.

## Full API surface (37 paths)
    /health
    /api/v1/overview
    /api/v1/incidents  +  /{id}  +  /{id}/notes  +  /{id}/timeline
    /api/v1/alerts     +  /{id}/acknowledge|resolve|override|review|assign
    /api/v1/briefs/weekly  +  /weekly/generate  +  /{region_id}
    /api/v1/stores     +  /{store_id}
    /api/v1/trends
    /api/v1/audit
    /api/v1/metrics
    /api/v1/forecasts
    /api/v1/replay     (POST)  +  /replay/{incident_id}  (GET)
    /api/v1/pipeline/run       +  /pipeline/{run_id}
    /api/v1/ingest             +  /ingest/{job_id}
    /api/v1/evaluation/run     +  /evaluation/{run_id}
    /api/v1/jobs/{job_id}
    /api/v1/feedback/batch     +  /feedback/{record_id}
    /api/v1/classify
    /api/v1/tracking/summary
    /api/v1/actions
    /api/v1/demo/reset
    /api/v1/me

## Frontend routes (17 pages)
    /                     Welcome / Sign-in
    /login                SSO sign-in
    /overview             KPIs + urgent queue
    /incidents            List
    /incidents/[id]       Detail (Overview / Evidence / Timeline / Actions)
    /alerts               Alert queue
    /trends               Baseline vs current + anomalies
    /stores               Ranked store list
    /stores/[id]          Store detail
    /actions              Action queue
    /reports              Weekly brief
    /import               Import wizard
    /data-health          Pipeline controls + metrics
    /settings             Health + session + config
    /audit                Audit event log

## Known limitations (documented, not hidden)
    - Single-worker uvicorn only (job registry is in-process).
    - No optimistic UI; mutations block until server responds (~200ms local).
    - Config editing via UI is intentionally disabled; edit YAML on disk.
    - TLS via self-signed cert for LAN; swap Caddyfile site line for real domain.
    - Legal/compliance review, pen testing, real-corp IdP swap are outside scope
      (spec §20.5, §24).

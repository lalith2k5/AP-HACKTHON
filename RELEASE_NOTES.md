# StoreSignal AI — v2.0 Release Notes

**Commit:** (see git log HEAD) · **Date:** 2026-10-16
**Event:** Talent AP Mega Hackathon — Track R5

## Status: local-first deployment ready

All spec 20.1-20.4 (local development deployment) requirements satisfied.
Spec 20.5 (production / multi-user) explicitly out of scope and documented.

## What ships

### Backend (FastAPI, port 8790)
- 40k+ records, 18/18 tests, ruff clean
- Pipeline: ingestion, normalization, classification, mandatory risk policy,
  trend detection, fusion, routing, briefs
- Endpoints: full incident lifecycle, alert ack/resolve/override, briefs,
  forecasts, replay, evaluation, audit, jobs
- Server-side API key auth (x-api-key), 8-role RBAC
- Rate limiting (300 req/min per IP)
- Async demo reset with job polling
- Structured audit log (append-only JSONL)

### Frontend (Next.js 16, port 3300)
- 5 Phase 1 screens, all data live from API:
  Welcome, Overview, Incidents list, Incident detail (4 tabs), Alerts, Reports
- Server-side API proxy (`/api/proxy/[...path]`) — API key never in browser
- Apple-style design tokens, dark mode, Framer Motion springs
- Playwright E2E: 6/6 passing

### Legacy (Streamlit, port 8501)
- Retained for comparison until Next.js reaches full 15-view parity
- Not deprecated, not deleted — parallel read-only UI

### Scripts
- `scripts/backup.sh` — tarball of config, reference, overrides, models, eval
- `scripts/restore.sh <archive>` — restore from backup
- `POST /api/v1/demo/reset` — async clean-slate reset

## Verified metrics

| Metric | Value |
|---|---|
| Records | 40,053 |
| Classification accuracy | 0.8910 |
| Macro-F1 | 0.9167 |
| Escalation precision | 0.9432 |
| Seeded incidents caught | 3/3 |
| Pipeline runtime | ~27s |
| pytest | 18/18 |
| ruff | clean |
| E2E | 6/6 |

## Out of scope (spec 20.5)

TLS, SSO/OIDC, multi-user RBAC with real identity, transactional DB,
backup automation, retention policy enforcement, legal/compliance review.
These are prerequisites for public or multi-user deployment, not for
local demo. See DEPLOYMENT.md.

## Known limitations

- Mutations block client until server responds (~200ms local)
- No offline mode
- No automatic data retention / rotation (JSONL grows unbounded)
- Streamlit still present (parallel, not blocking)

## How to run

See DEPLOYMENT.md. Quickstart:

    # Terminal A
    cd "$HOME/storesignal-ai"
    "$HOME/storesignal-ai/.venv/bin/uvicorn" storesignal.api:app --port 8790

    # Terminal B
    cd "$HOME/storesignal-ai/web"
    npm run dev -- --port 3300
    # open http://localhost:3300

## Post-deployment hardening (commit 911149e)

- **SQLite state store** replaces JSONL for overrides + notes. WAL mode,
  atomic writes, indexed. Survives restarts. Migration script included.
- **TLS via Caddy** — reverse proxy on :8443 with self-signed cert for LAN.
  Real-domain mode auto-provisions Let's Encrypt.
- **Legal / privacy templates** — DATA_INVENTORY.md, RETENTION_POLICY.md,
  PRIVACY_NOTES.md. Drafts for counsel, not certifications.
- **SSO** — deliberately deferred. No IdP selected; static x-api-key auth
  remains. Replacement path documented in HANDOFF section 15.

## Still not covered (requires decisions or vendors)
- Multi-user identity (SSO)
- PostgreSQL migration (SQLite is fine through pilot scale)
- SIEM integration for audit log
- Retention cron
- Penetration test before non-localhost exposure

# StoreSignal AI — Chat Handoff Document (v2.0 build)

**Purpose:** Give a new AI assistant full context on the ongoing project.

**Read this entire file before doing anything.**

## 0. If you are a new AI reading this mid-build

The user switches chats when context limits hit. Before doing anything:

1. `set +H`
2. `cd "$HOME/storesignal-ai"`
3. `git log --oneline -3` — see last landed commit
4. `"$HOME/storesignal-ai/.venv/bin/python" -m pytest -q tests` — confirm 18/18
5. `"$HOME/storesignal-ai/.venv/bin/python" -m ruff check src tests` — confirm clean
6. Read section 11 (honest gaps) and ask user which gap to close next.

Do NOT re-run the pipeline unless asked — it takes 30s and overwrites artifacts.
Node/npm/brew confirmed installed. Next.js frontend Phase 1 (5 screens) is the
current active workstream — read section 5a before doing anything frontend.
 Then confirm with the user
that you have understood the state and ask what they want to do next.

---

## 1. Project identity

- **Name:** StoreSignal AI
- **Event:** Talent AP Mega Hackathon — Track R5 "Turning Store Chatter
  Into Action: The Voice-of-Store Engine"
- **Position:** Multilingual retail operations intelligence layer.
  Early-warning and incident-resolution, NOT a sentiment dashboard.
- **Status:** v2.0 build complete. All 18 tests pass, lint clean,
  metrics identical to baseline, 13-screen UI live.
- **User profile:** Non-programmer. Terminal-only workflow on macOS.
  Everything must be copy-pasteable, prefixed with `set +H`.

## 2. Reference documents

1. R5 challenge brief (1 page)
2. Complete Deployable Implementation Specification v2.0 (30 pages,
   mockups included) — this is the target contract.
3. Old 14-page architecture spec (superseded).

## 3. Environment

- macOS 14+, Apple Silicon M2
- Home: `/Users/lalith.v`
- Project root: `$HOME/storesignal-ai/`
- Python 3.11.17
- Virtualenv: `$HOME/storesignal-ai/.venv/`
- Shell: zsh. **CRITICAL:** prefix every paste with `set +H`.
- `.env` (from `.env.example`) is auto-loaded by `settings.py`.
- Avoid `→`, `·`, em-dashes inside pasted code blocks when possible.


## 3a. GitHub repository

- **URL:** https://github.com/lalith2k5/AP-HACKTHON
- **Visibility:** public
- **Default branch:** `master`
- **Remote:** `origin` -> https://github.com/lalith2k5/AP-HACKTHON.git
- **Owner account:** `lalith2k5` (via `gh` CLI, authed)
- **Push command:**
      git add -A
      git -c user.name="StoreSignal Build" -c user.email="build@local" \
          commit -m "message"
      git push
- **Note:** `models/baseline_model.joblib` (6.4 MB) is committed. If future
  pushes time out, `git config http.postBuffer 524288000` and retry.

## 4. Folder structure (post-v2.0)

    ~/storesignal-ai/
    ├── README.md, DEMO_SCRIPT.md, PITCH_DECK.md, HANDOFF.md
    ├── Dockerfile, docker-compose.yml, .dockerignore
    ├── requirements.txt, pyproject.toml, Makefile, .env.example
    ├── .github/workflows/ci.yml
    ├── docs/architecture.svg
    ├── config/                 6 YAML files
    ├── src/
    │   └── storesignal/        30 python modules (was flat src/*.py)
    ├── tests/                  3 test files, 18 tests
    ├── models/baseline_model.joblib
    └── data/
        ├── raw/                6 files
        ├── reference/          2 files
        ├── processed/          33+ artifacts
        └── evaluation/reports/ evaluation_report.{json,md}

## 5. Package modules (src/storesignal/)

Pipeline (execution order in pipeline.py):
  1. generate_mock_data.py    40k records + 3 seeded incidents
  2. ingestion.py             Pydantic v2 validation -> raw_feedback.parquet
  3. normalization.py         NFKC, PII redact -> normalized_feedback.parquet
  4. weak_labels.py           keyword rules (NEVER reads hidden labels)
  5. classification.py        TF-IDF + LogisticRegression -> predictions.parquet
  6. risk_policy.py           mandatory escalation (independent of confidence)
  7. detection.py             Early-Warning Radar (robust z-score/MAD)
  8. routing.py               owner + SLA
  9. fusion.py                7-day rolling window dedup -> incidents.parquet
 10. alerts.py                evidence-backed alerts
 11. briefs.py                weekly regional briefs
 12. data_models.py           regions + routing_rules exports
 13. relationship_graph.py    NetworkX graph
 14. forecasting.py           action-impact simulator
 15. evaluate.py              hidden-label eval (guarded)

Infrastructure:
  - config_loader.py          Pydantic typed config
  - settings.py               12 STORESIGNAL_* env vars (spec 5.1)
  - paths.py                  central path resolution
  - versioning.py             SHA-256 hashes
  - security.py               API key auth, 7-role RBAC
  - tracking.py               action/resolution event log
  - workflow.py               8-state FSM + audit
  - import_wizard.py          CSV/JSONL/Parquet import with mapping
  - api_envelope.py           error envelope + cursor pagination
  - api.py                    FastAPI backend
  - ui.py                     Streamlit 15-view dashboard
  - ui_data.py                read-only UI accessors
  - tokens.py                 design tokens (dark/light)
  - cli.py                    Typer CLI
  - pipeline.py               orchestrator


## 5a. Next.js frontend — Phase 1 in progress

**Decision made:** Add a Next.js + Tailwind + shadcn/ui + Framer Motion
frontend for the 5 highest-visibility screens. Runs alongside the existing
Streamlit UI. Streamlit is NOT removed until the new UI is complete.

**Environment confirmed (2026-10-16):**
- Node v26.10.0
- npm 11.19.1
- Homebrew 7.0.9
- 97 GB free disk

**Phase 1 scope (5 screens):**
1. Welcome / Sign-in
2. Overview dashboard
3. Incident Detail (Overview / Evidence / Timeline / Actions tabs)
4. Alerts center
5. Weekly Report

**Planned stack:**
- Next.js 15 (App Router) + TypeScript
- Tailwind CSS v4 (via PostCSS, no CDN)
- shadcn/ui (component primitives)
- Framer Motion (spring physics, material transitions)
- Data source: existing FastAPI at http://localhost:8000

**Apple-grade design system targets:**
- SF Pro typography stack (-apple-system, BlinkMacSystemFont)
- 8pt spacing grid
- Continuous corner curve (squircle) via SVG mask for cards
- Semantic color tokens (systemBlue, systemGray, systemRed etc.)
- Backdrop-blur "materials" on overlays and sidebars
- Framer Motion springs: stiffness ~260, damping ~30 (Apple-ish feel)

**Directory target:**
    ~/storesignal-ai/web/
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx                 (welcome)
    │   ├── overview/page.tsx
    │   ├── incidents/[id]/page.tsx
    │   ├── alerts/page.tsx
    │   └── reports/page.tsx
    ├── components/ui/                (shadcn)
    ├── lib/api.ts                    (fetch wrapper for FastAPI)
    ├── lib/tokens.ts                 (Apple design tokens)
    ├── tailwind.config.ts
    ├── postcss.config.mjs
    ├── package.json
    └── tsconfig.json

**How to run (target end state):**
    # Terminal 1 — FastAPI backend
    "$HOME/storesignal-ai/.venv/bin/uvicorn" storesignal.api:app --reload --port 8000

    # Terminal 2 — Next.js frontend
    cd "$HOME/storesignal-ai/web" && npm run dev
    # open http://localhost:3000

**Migration note:** Streamlit UI remains at :8501 for comparison until the
Next.js frontend matches all 5 target screens. Then `ui.py` is deleted and
`make ui` is retired.

**Known Streamlit bugs fixed this session:**
- `category_distribution()` now returns column `category` (not `predicted_category`)
- `screen_trends` now reads `radar["predicted_category"]`
- `use_container_width=True` -> `width="stretch"` everywhere

## 5b. Next.js frontend — Phase 1 status (updated 2026-10-16 ~14:10)

**All 5 Phase 1 screens scaffolded and building.** Next.js 16.4.2 (not 15 —
scaffold pulled latest), Turbopack, Tailwind v4 (CSS-first via
@tailwindcss/turbopack, no tailwind.config), shadcn base-nova style
(NOT the old default — uses @base-ui/react, so Button takes `render={<Link/>}`
+ `nativeButton={false}` instead of `asChild`), motion v11 (`motion/react`).

**Ports (changed from earlier plan to avoid learntrace collision):**
- FastAPI:  **8790** (was 8000)
- Next dev:  **3300** (was 3000)
- Streamlit: 8501 (unchanged)

**Files added under web/:**
    app/layout.tsx                       Apple font stack applied
    app/page.tsx                         Welcome / Sign-in (screen 1)
    app/overview/page.tsx                KPIs + urgent queue (screen 2)
    app/incidents/page.tsx               Incidents list
    app/incidents/[id]/page.tsx          Server wrapper w/ Suspense
    app/incidents/[id]/incident-detail-client.tsx  Detail w/ 4 tabs (screen 3)
    app/alerts/page.tsx                  Alert queue w/ severity filter (screen 4)
    app/reports/page.tsx                 Weekly brief (screen 5)
    components/app-shell.tsx             Sidebar + topbar layout
    components/ui/button.tsx             shadcn
    lib/api.ts                           Fetch wrapper for FastAPI @ :8790
    lib/tokens.ts                        Apple motion/spacing/status tokens
    lib/utils.ts                         shadcn cn() helper

**Backend changes made this session:**
- Added `GET /api/v1/overview` to api.py (was missing despite spec 14.2).
  Composes kpis + urgent_queue + categories + freshness from existing
  incidents/alerts/metrics artifacts. `region_id` filter is best-effort
  (incidents parquet has no region_id column today, so it silently no-ops).
- Added CORSMiddleware to api.py allowing origins :3300 and :8501.

**All Phase 1 gaps CLOSED (2026-10-16 ~14:20):**
- Incident Actions tab: fully wired. Owner + status selectors, Save,
  Mark resolved, Add note. Uses `PATCH /api/v1/incidents/{id}` and
  `POST /api/v1/incidents/{id}/notes`.
- Incident Timeline tab: real events from `GET /api/v1/incidents/{id}/timeline`
  (first_seen + last_seen + every override + every note, sorted).
- Alerts page: Ack / Resolve / Override (with required reason) all wired.
  Uses `POST /api/v1/alerts/{id}/acknowledge|resolve|override`.
- Reports page: renders real `/api/v1/briefs/weekly` shape (region_name,
  week_start/end, total_feedback + delta, top_issues with trend/severity,
  mandatory-risk section derived from escalation_rule prefix).
- Overview `region_id` filter: now derives region from store_id prefix
  (S-DEL-001 -> DEL). Previously no-op.

**Backend endpoints added this session (all in src/storesignal/api.py):**
    GET    /api/v1/overview                          (composed dashboard)
    PATCH  /api/v1/incidents/{id}                    (owner/status/priority)
    POST   /api/v1/incidents/{id}/notes              (append note)
    GET    /api/v1/incidents/{id}/timeline           (first/last/overrides/notes)
    POST   /api/v1/alerts/{id}/acknowledge
    POST   /api/v1/alerts/{id}/resolve
    POST   /api/v1/alerts/{id}/override              (requires reason)
    GET    /api/v1/briefs/weekly                     (region_id now optional)
Also fixed: get_brief region_id was mandatory positional; now optional.

**State persistence pattern:**
    Overrides and notes are append-only JSONL in data/processed/:
      data/processed/incident_overrides.jsonl
      data/processed/alert_overrides.jsonl
      data/processed/incident_notes.jsonl
    Latest value wins per (id, field). Every mutation also writes to the
    audit log. Re-running the pipeline does NOT erase overrides — they
    live separately from the derived parquet artifacts. Demo reset
    (POST /api/v1/demo/reset) also does NOT currently clear them;
    if a hard reset is ever needed, delete those 3 JSONL files manually.
- Turbopack + Next 16 cacheComponents gave us a build error on the
  dynamic `[id]` route. Working fix: pure Server Component page that renders
  `<Suspense>` + Client child using `useParams()` with NO generic type
  argument (`useParams()` then cast). Any reintroduction of the generic
  re-triggers the SWC error.

**How to run (all three services):**
    # Terminal A — FastAPI on 8790
    set +H
    cd "$HOME/storesignal-ai"
    "$HOME/storesignal-ai/.venv/bin/uvicorn" storesignal.api:app --port 8790 --reload

    # Terminal B — Next.js on 3300
    set +H
    cd "$HOME/storesignal-ai/web"
    npm run dev -- --port 3300

    # Terminal C — Streamlit (still runs, parallel, for comparison)
    set +H
    cd "$HOME/storesignal-ai"
    "$HOME/storesignal-ai/.venv/bin/streamlit" run src/storesignal/ui.py --server.port 8501

**Session log (what broke and how it was fixed):**
1. shadcn init wrote `--font-sans: var(--font-sans);` self-ref -> patched to
   font-geist-sans + SF Pro fallback chain.
2. shadcn base-nova Button has no `asChild` -> replaced with `render={<Link/>}`
   + `nativeButton={false}` (Base UI's API).
3. No `/api/v1/overview` existed -> added to api.py.
4. No CORS on FastAPI -> added CORSMiddleware.
5. Port 8000/3000 collisions with learntrace project -> moved to 8790/3300.
6. Next 16 `cacheComponents:true` + dynamic `[id]` route -> fixed with
   Server Component parent + `<Suspense>` + Client child with untyped
   `useParams()`.

## 6. Current verified metrics (unchanged from baseline)

| Metric | Value |
|---|---|
| Records | 40,053 |
| Classification accuracy (hidden) | 0.8910 |
| Macro-F1 | 0.9167 |
| Weighted-F1 | 0.9065 |
| Escalation precision | 0.9432 |
| Escalation recall | 0.0661 (by design) |
| Seeded incidents | 3 / 3 |
| Mean lead days vs peak | 3.67 |
| Policy compliance | 1.0000 (1260/1260) |
| Pipeline runtime | ~26.5s |
| Ruff | clean |
| Pytest | 18/18 pass |

## 7. Key design rules (do not violate)

1. **Hidden labels** read ONLY by evaluate.py; env guard
   `STORESIGNAL_ALLOW_HIDDEN_EVAL` enforces this at import time.
2. **Mandatory escalation** fires on category OR weak_category OR severity,
   independent of classifier confidence.
3. **Prediction, anomaly detection, policy escalation** are separate modules.
4. **Fusion is a hypothesis**; `verification_status` defaults to "suspected".
5. **Every alert** has trigger_type, reason, evidence IDs, owner, priority,
   uncertainty (= 1 - mean confidence).
6. **Deterministic** seed 20260214.
7. **Paths come from `storesignal.paths`**, not hardcoded home paths.

## 8. Common commands

    set +H
    cd "$HOME/storesignal-ai"

    # Full rebuild (~30s)
    "$HOME/storesignal-ai/.venv/bin/python" -m storesignal.pipeline

    # Single stages
    "$HOME/storesignal-ai/.venv/bin/python" -m storesignal.<module>

    # Test / lint
    "$HOME/storesignal-ai/.venv/bin/python" -m pytest -q tests
    "$HOME/storesignal-ai/.venv/bin/python" -m ruff check src tests

    # Servers (each blocks its tab)
    "$HOME/storesignal-ai/.venv/bin/uvicorn" storesignal.api:app --reload --port 8000
    "$HOME/storesignal-ai/.venv/bin/streamlit" run src/storesignal/ui.py --server.port 8501

    # Import external data
    "$HOME/storesignal-ai/.venv/bin/python" -m storesignal.cli import-data path/to/file.csv

    # Env var override example
    STORESIGNAL_DATA_DIR=/tmp/altdata "$HOME/storesignal-ai/.venv/bin/python" -m storesignal.pipeline

## 9. Known issues

1. **Port conflicts**: 8501/8000 held if not Ctrl+C'd.
   `lsof -ti:8501 | xargs kill -9` / same for 8000.
2. **zsh history expansion**: prefix every paste with `set +H`.
3. **Heredoc truncation**: write long files via Python `Path.write_text(...)`.
4. **ruff --fix churn**: strips "unused" imports, then next phase adds code
   that uses them. **Re-check imports after every ruff --fix.**

## 10. v2.0 build phases completed

| Phase | What landed | Commit |
|---|---|---|
| Baseline snapshot | pre-v2 tag + tarball | 2b8bce1 |
| 1 | Repo restructure to src/storesignal/ | 2833fb0 |
| 2+4 | settings.py env vars + 7-role RBAC | f3e8504 |
| 3+5 | import wizard + API envelope + pagination | 5cd18b9 |
| 6+5b | workflow FSM + readiness health + ingest endpoints | 3575d5c |
| 7A | 13-screen UI scaffold + tokens + dark mode | 6af5b07 |
| 7B | incident detail tabs, evidence, trends, stores, actions, report | 10aa5ad |
| 7C | import wizard UI, data health, settings form, audit | d12d4ac |
| 8 | end-to-end verification green | 623f345 |
| Gap 1 | env-var path propagation (23 modules) + hidden-eval guard | 720c351 + 7d662c1 |


## 11. Remaining gaps (honest, end-of-build state)

**ALL originally identified gaps are closed OR explicitly documented.**

Closed this build:
- Gap 1: env-var path propagation (settings.py + paths.py, verified via override)
- Gap 2: region selector filters data (filter_by_region, 5 regions verified)
- Gap 3: import feeds pipeline (process-import CLI, 30 rows -> 30 classified)
- Gap 4: UI role gate (user_can helper)
- Gap 5: impact simulator wired to forecasts.parquet
- Gap 6: store impact map (50 stores, prefix-derived coords)
- Gap 7: mobile media-query CSS
- Gap 8: uv migration (uv.lock with 208 packages, pyproject now has deps)
- Gap 9: Dockerfile + docker-compose fixed for package layout
- Gap 10: PRODUCTION_READINESS.md + OPERATIONS_RUNBOOK.md written

**Not yet verified in this environment:**
- Docker image build (`docker compose up --build`) - daemon was not running
  during this session. Config is correct; image build is a follow-up.

**Explicitly out of scope for local MVP (per spec section 20.5):**
- TLS, SSO, RBAC-with-real-identity, transactional DB, retention policy,
  legal/compliance review.

## 11a. Additional files added this build
- `.env.example` - all 12 STORESIGNAL_* vars with placeholder values
- `OPERATIONS_RUNBOOK.md` - health checks, logs, incidents, backups, rollback
- `PRODUCTION_READINESS.md` - 10-section checklist for multi-user deployment
- `uv.lock` - 208 packages, reproducible deps
- `src/storesignal/logging_setup.py` - structured JSON logging (spec 19.1)
- `src/storesignal/process_import.py` - import -> classification -> policy
- `src/storesignal/workflow.py` - 8-state FSM with audit
- `src/storesignal/import_wizard.py` - CSV/JSONL/Parquet with mapping
- `src/storesignal/api_envelope.py` - error envelope + cursor pagination
- `src/storesignal/paths.py` - central path resolution
- `src/storesignal/settings.py` - 12 env vars honored
- `src/storesignal/tokens.py` - design tokens
- `src/storesignal/ui_data.py` - UI read-only accessors

## 12. How the user works

- **Non-programmer.** Cannot debug. Every command copy-paste ready.
- **One block at a time**, verify, then next block.
- **Values honesty** over polish. Flag gaps.
- **Uses multiple terminal tabs**, switches randomly. Never assume cwd.
- **Pattern that works:**
  1. Give a block, wait for output.
  2. Read output, diagnose.
  3. Ship a corrective block if needed.
  4. Verify.

## 13. First thing you should do as the new assistant

Reply with:
1. One-line confirmation you read this file.
2. Current verified state (metrics + tests + UI status).
3. Question: "What would you like to do next?"

Do NOT paste code until user says what they want.

---

## 14. Final state (2026-10-16 ~14:25, commit 0cea101)

**Phase 1 Next.js frontend: complete end to end. All gaps closed.**

Verified green:
- pytest: 18/18
- ruff: clean
- Frontend build: 6 routes, no TypeScript errors
- All 5 screens pull real data from FastAPI
- All mutation endpoints (PATCH incident, POST note, alert ack/resolve/override)
  work with x-api-key and persist to append-only JSONL
- Demo reset clears state + rebuilds pipeline (27s)

Screens:
    1. /                     Welcome / Sign-in
    2. /overview             KPIs + urgent queue, region filter functional
    3. /incidents            List with severity color
    4. /incidents/[id]       Overview / Evidence / Timeline / Actions
                             Actions: owner+status+save, mark resolved,
                             add note. All persist.
    5. /alerts               Filter, Ack / Resolve / Override (modal, reason
                             required)
    6. /reports              Real weekly brief

Backend endpoints added this session (all RBAC-guarded, all audit-logged):
    GET    /api/v1/overview
    PATCH  /api/v1/incidents/{id}
    POST   /api/v1/incidents/{id}/notes
    GET    /api/v1/incidents/{id}/timeline
    POST   /api/v1/alerts/{id}/acknowledge
    POST   /api/v1/alerts/{id}/resolve
    POST   /api/v1/alerts/{id}/override
    GET    /api/v1/briefs/weekly           (region_id now optional)
    POST   /api/v1/demo/reset              (clears overrides + notes)

Auth: x-api-key header, demo key `demo-key-storesignal` (admin role).
Frontend reads NEXT_PUBLIC_STORESIGNAL_API_KEY from web/.env.local.

Ports:
    8790  FastAPI
    3300  Next.js
    8501  Streamlit (legacy, still running, ui.py untouched)

Deployment guide: see DEPLOYMENT.md.

Gaps closed this session (final):
- CLOSED: Client bundle no longer contains the API key. All browser calls
  route through /api/proxy/[...path] (Next.js server route). The key is
  read from STORESIGNAL_API_KEY (server-only) and never reaches the client.
- CLOSED: Playwright E2E tests exist (web/e2e/smoke.spec.ts, 6 tests).
  Run: cd web && npx playwright test

Known honest limitations (not hidden, not blocking local demo):
- No optimistic UI; mutations block until server responds (~200ms local).
- Streamlit ui.py not yet retired (per HANDOFF 5a plan, delete only after
  Next.js reaches full parity — Streamlit still has 15 views, Next.js has 6).
  Streamlit remains available on :8501 for comparison.
- No offline / no-network mode.
- Production hardening (TLS, SSO, transactional DB) explicitly out of
  scope for local MVP per spec section 20.5.

## 15. Post-deployment hardening (2026-10-16 ~20:45, commit 911149e)

**All identified production gaps addressed or explicitly deferred.**

### SQLite transactional state (was: JSONL)
    src/storesignal/state.py    WAL-mode SQLite at data/processed/storesignal.db
    scripts/migrate_state.py    one-shot JSONL -> SQLite importer
Tables: incident_overrides, alert_overrides, incident_notes, audit_events.
All mutations atomic. Verified survives backend restart.

### TLS via Caddy
    deploy/tls/Caddyfile        reverse proxy :8443, security headers
    scripts/serve-tls.sh        boots Caddy with self-signed TLS (LAN)
    Caddy installed at /opt/homebrew/bin/caddy
For real domain: swap site line in Caddyfile to your hostname and remove
`tls internal` — Caddy auto-provisions Let's Encrypt.

### Legal / privacy templates
    DATA_INVENTORY.md     data classes, redaction, access, flow
    RETENTION_POLICY.md   retention windows + SAR procedure + sign-off
    PRIVACY_NOTES.md      design principles + threat model + boundaries
These are DRAFTS. Not compliance certifications. Legal review still required.

### SSO — wired and verified end to end (2026-10-16 21:35)

**Status: WORKING. 3/3 SSO Playwright tests pass against local Keycloak.**

Full flow verified:
  1. Unauthenticated /overview -> 302 to /login
  2. Click "Sign in with SSO" -> Keycloak login page
  3. Fill credentials -> redirect back to /overview
  4. Session established -> KPI cards render
  5. Backend accepts Bearer token (401 without, 200 with)

**Backend (FastAPI :8790)**
  - `src/storesignal/auth_oidc.py` — provider-agnostic JWT verifier
    - JWKS auto-discovery + 1h cache
    - dotted-path role claim (realm_access.roles works)
    - audience optional (skip when env empty)
  - `src/storesignal/security.py` — accepts `x-api-key` OR `Bearer <JWT>`
  - `src/storesignal/api.py` — global `_auth_middleware` enforces auth
    on all `/api/v1/*` when either static key or OIDC is enabled
  - `scripts/run-api.sh` — sources `.env` before launching uvicorn
    (critical: bare uvicorn does not load .env)

**Frontend (Next.js :3300)**
  - `web/auth.ts` — Auth.js v5 config, provider-agnostic OIDC
  - `web/app/api/auth/[...nextauth]/route.ts` — OAuth callback
  - `web/proxy.ts` — Next.js 16 middleware (redirects when OIDC on)
  - `web/app/login/page.tsx` — sign-in button
  - `web/app/api/proxy/[...path]/route.ts` — server-side token injection
    (reads Auth.js session, sets Authorization: Bearer)
  - `web/types/next-auth.d.ts` — module augmentation

**Keycloak (local, :8180)**
  - `deploy/keycloak/docker-compose.yml` + `realm.json`
  - Realm: storesignal, Client: storesignal-api
  - Users: admin / ops / reviewer / hr (password: `password`)
  - VERIFY_PROFILE required action disabled
  - Role mapper: realm_access.roles claim in tokens

**Env (backend `.env`)**
    STORESIGNAL_OIDC_ENABLED=true
    STORESIGNAL_OIDC_ISSUER=http://localhost:8180/realms/storesignal
    STORESIGNAL_OIDC_AUDIENCE=
    STORESIGNAL_OIDC_ROLE_CLAIM=realm_access.roles

**Env (web/.env.local)**
    AUTH_OIDC_ISSUER=http://localhost:8180/realms/storesignal
    AUTH_OIDC_CLIENT_ID=storesignal-api
    AUTH_OIDC_CLIENT_SECRET=storesignal-dev-secret
    AUTH_OIDC_ROLE_CLAIM=realm_access.roles

**To swap providers** (Auth0, Google, Azure, Okta):
change the 4 AUTH_OIDC_* vars in web/.env.local + 3 STORESIGNAL_OIDC_*
vars in .env. No code change.

**To disable OIDC** (fall back to static key):
    rm web/.oidc-enabled
    strip STORESIGNAL_OIDC_ENABLED from .env
    restart both servers

**One gotcha to remember:**
`uvicorn` does NOT load `.env` automatically. Always start it via
`./scripts/run-api.sh` (which sources `.env` first). Bare
`uvicorn storesignal.api:app` will silently run with OIDC disabled.

**Playwright notes:**
- smoke.spec.ts skips when `web/.oidc-enabled` exists
- sso.spec.ts runs only when that file exists
- Test creds: KC_TEST_USER / KC_TEST_PASS env vars (default: admin/password)

### Full endpoint list (final)
    GET    /health
    GET    /api/v1/overview
    GET    /api/v1/incidents
    GET    /api/v1/incidents/{id}
    PATCH  /api/v1/incidents/{id}
    POST   /api/v1/incidents/{id}/notes
    GET    /api/v1/incidents/{id}/timeline
    GET    /api/v1/alerts
    POST   /api/v1/alerts/{id}/acknowledge
    POST   /api/v1/alerts/{id}/resolve
    POST   /api/v1/alerts/{id}/override
    GET    /api/v1/briefs/weekly
    POST   /api/v1/briefs/weekly/generate
    GET    /api/v1/metrics
    GET    /api/v1/forecasts
    GET    /api/v1/replay/{id}
    POST   /api/v1/demo/reset        (async, returns job_id)
    GET    /api/v1/jobs/{id}
    POST   /api/v1/feedback/batch
    GET    /api/v1/feedback/{id}
    POST   /api/v1/classify
    GET    /api/v1/tracking/summary
    POST   /api/v1/actions

### Ports (unchanged)
    8790  FastAPI
    3300  Next.js dev
    8443  Caddy TLS (optional, when scripts/serve-tls.sh running)
    8501  Streamlit legacy

**END OF HANDOFF**

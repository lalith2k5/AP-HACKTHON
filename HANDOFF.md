# StoreSignal AI — Chat Handoff (v3.0)

**Read this file in full before doing anything.**

A new AI reading this mid-build: run the state check below, then read
section 11 (honest gaps) and ask the user which to close next. Do NOT
re-run the pipeline unless asked (it takes ~27s and overwrites artifacts).

---

## 0. State check (run first)

    set +H
    cd "$HOME/storesignal-ai"
    git log --oneline -3
    git status --short
    .venv/bin/python -m pytest -q tests 2>&1 | tail -3
    .venv/bin/python -m ruff check src tests
    curl -s http://localhost:8790/health

Expected: pytest 31/31, ruff clean, health {"status":"ok"}.

Start/stop the stack with the shell shortcuts (installed in ~/.zshrc):

    ss-start    # boot backend + frontend, opens browser
    ss-stop
    ss-status
    ss-logs

---

## 1. Project

- **StoreSignal AI** — Talent AP Mega Hackathon Track R5
- Voice-of-Store Engine: multilingual retail ops intelligence
- Early-warning + incident-resolution, NOT a sentiment dashboard
- **User**: non-programmer, macOS, terminal-only. Every paste prefixed `set +H`.
- **Repo**: https://github.com/lalith2k5/AP-HACKTHON (public, master)
- **Root**: `$HOME/storesignal-ai`
- **Python**: 3.11.17 in `.venv/`
- **Node**: v26.10.0, npm 11.19.1

## 2. Ports

    8790  FastAPI
    3300  Next.js
    8180  Keycloak (only if OIDC enabled)
    8443  Caddy TLS (optional)
    retired: 8501 Streamlit -> legacy/ui.py.retired

## 3. Critical gotcha

`uvicorn` does NOT read `.env`. Always start the backend via
`./scripts/run-api.sh`, not bare `uvicorn`. `ss-start` does this correctly.

## 4. Folder layout

    ~/storesignal-ai/
    ├── README.md, DEMO_SCRIPT.md, DEMO_RECORDING_GUIDE.md, HANDOFF.md
    ├── DEPLOYMENT.md, OPERATIONS_RUNBOOK.md, PRODUCTION_READINESS.md
    ├── DATA_INVENTORY.md, RETENTION_POLICY.md, PRIVACY_NOTES.md
    ├── Dockerfile, docker-compose.yml, Makefile, pyproject.toml
    ├── compliance/        (8 docs + 4 emails + 3 meeting agendas)
    ├── config/            6 YAML files
    ├── data/processed/    parquet + storesignal.db (SQLite WAL)
    ├── models/baseline_model.joblib
    ├── scripts/           run-api.sh, backup.sh, restore.sh, serve-tls.sh
    ├── src/storesignal/   30+ python modules
    ├── tests/             4 test files, 31 tests
    └── web/               Next.js 16 + Tailwind v4 + shadcn base-nova

## 5. Backend — 51 API endpoints

Core:
    GET    /health
    GET    /api/v1/overview
    GET    /api/v1/incidents          +  /{id}
    PATCH  /api/v1/incidents/{id}
    POST   /api/v1/incidents/{id}/notes
    GET    /api/v1/incidents/{id}/timeline
    GET    /api/v1/alerts
    POST   /api/v1/alerts/{id}/acknowledge|resolve|override|review|assign
    GET    /api/v1/briefs/weekly
    POST   /api/v1/briefs/weekly/generate
    GET    /api/v1/briefs/{region_id}
    POST   /api/v1/demo/reset

Spec-completeness (added in v3):
    GET    /api/v1/stores             +  /{store_id}
    GET    /api/v1/trends
    GET    /api/v1/audit
    POST   /api/v1/pipeline/run       +  GET /api/v1/pipeline/{run_id}
    POST   /api/v1/ingest             +  GET /api/v1/ingest/{job_id}
    POST   /api/v1/evaluation/run     +  GET /api/v1/evaluation/{run_id}
    GET    /api/v1/jobs/{job_id}

Feature endpoints (v3):
    POST   /api/v1/import/upload                     multipart file upload
    GET    /api/v1/import/upload/{id}/preview        columns + issues
    POST   /api/v1/import/validate                   mapping + row issues
    POST   /api/v1/import/commit                     returns batch_id
    GET    /api/v1/import/batches
    POST   /api/v1/incidents/merge
    POST   /api/v1/incidents/{id}/split
    GET    /api/v1/incidents/{id}/lineage
    POST   /api/v1/feedback/{id}/flag                reviewer label correction
    GET    /api/v1/feedback/{id}/flags
    GET    /api/v1/map/stores                        coords + incident counts
    GET    /api/v1/export/incidents.csv
    GET    /api/v1/export/audit.csv
    GET    /api/v1/export/brief/{region_id}.pdf      requires reportlab

## 6. Frontend — 18 pages

    /                      Welcome / landing
    /login                 SSO sign-in
    /overview              KPIs + urgent queue
    /incidents             list
    /incidents/[id]        Overview / Evidence / Timeline / Actions tabs
                           + MergeSplitDialog in Actions
    /alerts                queue with Ack/Resolve/Override
    /trends                baseline vs current + anomalies
    /stores                list  (tab: List)
    /stores/map            interactive Leaflet map (tab: Map)
    /stores/[id]           store detail
    /actions               action queue
    /reports               weekly brief + export buttons
    /import                upload -> map -> validate -> commit wizard
    /data-health           pipeline controls + metrics
    /settings              health + session + config list
    /audit                 event log + CSV export

## 7. Design system

- `web/app/globals.css` is the source of truth. Semantic class names
  (.card, .btn-primary, .pill, .table, .nav-link.is-active).
- Legacy shadcn tokens are aliased to Apple palette so all 18 pages
  render without per-page edits.
- Sidebar uses Lucide SVG icons (not unicode glyphs).
- Apple materials: backdrop-blur, translucent surfaces, .nav-link pills.
- Glass sidebar (blur 60px), 5 tier fonts, 6 spacing steps.
- 8pt grid, tracking-tight headings, cubic-bezier(0.22,0.61,0.36,1).

## 8. Import robustness (v3)

`import_wizard._read_csv_robust()` handles:
- BOM (utf-8-sig + belt-and-braces lstrip)
- Delimiter detection (picks the delimiter with the most occurrences in
  the header, from , ; \t |)
- Encoding fallback (utf-8-sig -> utf-8 -> latin-1)
- Non-ISO timestamp detection (warns with samples)
- Duplicate record_id detection (blocks commit, spec 7.2)
- Empty text_raw / empty store_id warnings

`detect_row_issues()` returns the warning/error list; preview, validate,
and commit all surface it.

## 9. Auth

Mode A (default, currently active): static x-api-key
    header: x-api-key: demo-key-storesignal
Mode B: OIDC via Keycloak. Enables by `touch web/.oidc-enabled` +
setting 3 STORESIGNAL_OIDC_* + 4 AUTH_OIDC_* env vars. Provider-agnostic
(Auth0/Google/Azure/Okta — see compliance/04_idp_swap_guide.md).

## 10. Verified metrics (unchanged from baseline)

    40,053 records
    Classification accuracy 0.8910
    Macro-F1 0.9167
    Escalation precision 0.9432
    Policy compliance 1.0000 (1260/1260)
    Seeded incidents 3/3, 3.67 mean lead days
    32 taxonomy categories
    5 languages (en, hi, mr, ta, mixed)
    4 channels

## 11. R5 brief compliance — 16/16

All verified. Every requirement from the original hackathon brief
(40k records, 4 channels, multilingual, ~30 categories, hidden labels,
normalization, mandatory policy, weekly brief with trend arrow,
routing with escalation rule stated, emerging detection, evaluate.py,
precision statement, de-dup) is delivered and verifiable.

## 12. Spec §2.2 workflow — 14/14

Import wizard, validation report, merge/split, flag-wrong-label,
store map, export buttons, and all 8 previously-missing spec endpoints
are now live. Only item intentionally deferred: browser file upload
is capped at 100MB.

## 13. Honest gaps (human-only)

Five items cannot be closed by code. Drafts in `compliance/`:

1. **Legal review** — 2 docs + email draft. Needs counsel signature.
2. **Pen test** — SOW + email. Needs vendor engagement.
3. **Real IdP swap** — env-var guide + email. Needs IT registration.
4. **Data owner sign-off** — form + email + meeting agenda. Needs signature.
5. **Stakeholder acceptance** — 10-gate form + worksheet + agenda. Needs sign-offs.

To send: open `compliance/outbound/READY_TO_SEND/*.eml` in a text editor,
fill [bracketed] placeholders, attach the referenced doc, double-click to
open in Mail.app.

To hold: open `compliance/meetings/*.md` — minute-by-minute agendas with
"what to bring" and "do NOT" sections.

## 14. Commit history (recent, on origin/master)

    52ec256  Apple-Maps aesthetic — Voyager -> ESRI tiles
    f68e9d4  import robust reader
    18b8422  import BOM + delimiter + dup + date
    ef3e73f  canonical-first mapping UI
    bb8ed1a  map invalidateSize fix
    f469445  ESRI tiles (no API key)
    7ec9a6a  consolidate Stores+Map nav
    f217b3a  consolidate Stores+Map
    e8b52ad  India outline SVG
    a36fe9e  store map coords fix
    ca72f6c  close 8 spec gaps
    6ec93ea  /import duplicate heading
    bb0c285  a11y: one h1 per page

## 15. Known issues

1. **zsh history expansion**: prefix every paste with `set +H`.
2. **Heredoc truncation**: write long files via `Path.write_text()`, not heredocs.
3. **ruff --fix strips "unused" imports**: always re-check after.
4. **Port conflicts**: `lsof -ti:8790 | xargs kill -9` etc.
5. **Playwright strict mode**: getByRole('heading', {name}) fails if two
   headings have the same name. /import had topbar h1 + page h2 both
   saying "Import data" — resolved by removing the page-level h2.
6. **Text collision**: getByText is case-insensitive. Avoid duplicate
   phrases like "SIMULATED DATA" / "simulated data" on one page.
7. **CSS @utility doesn't always emit**: use plain CSS classes with
   semantic names, not Tailwind @utility, for critical layout.

## 16. How the user works

- Non-programmer. Cannot debug.
- Wants one block at a time, verify, then next.
- Values honesty over polish. Flag gaps.
- Uses multiple terminal tabs, switches randomly.
- Pattern: block -> wait for output -> diagnose -> fix -> verify.

## 17. First thing to do as the new AI

Reply with:
1. One-line confirmation you read this file.
2. Current verified state (pytest, ruff, health, git log).
3. Question: "What would you like to do next?"

Do NOT paste code until the user says what they want.

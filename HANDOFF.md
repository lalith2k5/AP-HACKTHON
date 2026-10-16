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

**END OF HANDOFF**

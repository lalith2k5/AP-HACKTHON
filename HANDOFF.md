# StoreSignal AI — Chat Handoff Document (v2.0 build)

**Purpose:** Give a new AI assistant full context on the ongoing project.

**Read this entire file before doing anything.** Then confirm with the user
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
- Avoid `→`, `·`, em-dashes inside pasted code blocks when possible.

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

## 11. Remaining gaps (not built — honest list)

1. **Region selector is UI-only** — doesn't filter data by region.
2. **UI role selector is UI-only** — no client-side permission gating.
   Server-side API roles ARE enforced.
3. **Import doesn't feed the main pipeline** — imported batches land in
   `data/processed/imports/BATCH/` but classification/escalation don't
   run on them.
4. **Weekly Report reads existing briefs** — no regenerate button wired
   to `briefs.build()`.
5. **Impact Simulator button is decorative** — doesn't call `forecasting.build()`.
6. **Store Impact is a bar chart, no map** — store_master.csv has no lat/lon.
7. **Mobile responsiveness is Streamlit default** — no custom CSS.
8. **uv migration skipped** — still pip + .venv. Spec preferred uv+uv.lock.
9. **Docker not re-tested after restructure.**
10. **Production concerns** (TLS, SSO, RBAC-with-real-identity, DB,
    retention policy) — explicitly out of scope per spec section 20.5.

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

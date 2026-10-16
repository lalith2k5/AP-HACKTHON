# StoreSignal AI — Chat Handoff Document

**Purpose:** Give a new AI assistant full context on an ongoing project so
it can continue seamlessly.

**Read this entire file before doing anything.** Then confirm with the user
that you have understood the state and ask what they want to do next.

---

## 1. Project identity

- **Name:** StoreSignal AI
- **Event:** Talent AP Mega Hackathon — Track R5 "Turning Store Chatter Into Action: The Voice-of-Store Engine"
- **Position:** Multilingual retail operations intelligence layer. Early-warning
  and incident-resolution, NOT a sentiment dashboard.
- **Status:** Complete and verified end-to-end. Ready for submission.
- **User profile:** Non-programmer. Terminal-only workflow on macOS.
  Cannot debug code themselves. Everything must be copy-pasteable.

---

## 2. Reference documents

The user has shared two documents in previous chats (they can re-upload if needed):

1. **R5 challenge brief** — 1-page description of the problem, inputs,
   desired outputs, and stretch goal.
2. **Architecture specification** — 14-page detailed spec covering
   tech stack, data flow, schema, API contracts, security, evaluation.

All work has been checked against both. Latest audit result:
**199 PASS · 2 WARN (production-only) · 0 FAIL** against the arch spec.
**5/5 desired outputs + stretch satisfied** against the R5 brief.

---

## 3. Environment

- **OS:** macOS 14+, Apple Silicon M2
- **Home:** `/Users/lalith.v` (referred to as `$HOME`)
- **Project root:** `$HOME/storesignal-ai/`
- **Python:** 3.11.17
- **Virtualenv:** `$HOME/storesignal-ai/.venv/` — always use
  `$HOME/storesignal-ai/.venv/bin/python` explicitly, never bare `python`
- **Shell:** zsh. CRITICAL: user must prefix every paste with `set +H` to
  disable history expansion (otherwise `!` breaks). Also avoid `→`, `·`,
  em-dashes inside pasted blocks when possible.

---

## 4. Project folder structure

    ~/storesignal-ai/
    ├── README.md, DEMO_SCRIPT.md, PITCH_DECK.md
    ├── Dockerfile, docker-compose.yml, .dockerignore
    ├── requirements.txt, pyproject.toml, Makefile
    ├── .github/workflows/ci.yml
    ├── docs/architecture.svg
    ├── config/                   6 YAML files (split + merged loader)
    │   ├── config.yaml
    │   ├── demo.yaml
    │   ├── thresholds.yaml
    │   ├── risk_policy.yaml
    │   ├── routing.yaml
    │   └── taxonomy.yaml
    ├── src/                      24 Python modules
    ├── tests/                    3 test files, 18 tests
    ├── models/baseline_model.joblib
    └── data/
        ├── raw/                  6 files (4 channels + labels + seeds)
        ├── reference/            2 files (store_master.csv, taxonomy.csv)
        ├── processed/            32 artifacts (parquet + json + briefs)
        └── evaluation/reports/   evaluation_report.{json,md}

---

## 5. The 24 src/ modules

Pipeline (in execution order — see `src/run_pipeline.py`):

1. `generate_mock_data.py` — creates 40,053 mock records + 3 seeded incidents
2. `ingestion.py` — validates schemas with Pydantic v2, writes raw_feedback.parquet
3. `normalization.py` — NFKC, zero-width removal, PII redaction, writes normalized_feedback.parquet
4. `weak_labels.py` — keyword rules that generate training labels (NEVER reads hidden_labels.jsonl)
5. `classification.py` — TF-IDF (word+char n-grams) + LogisticRegression
6. `risk_policy.py` — mandatory escalation, independent of confidence
7. `detection.py` — Early-Warning Radar (robust z-score, MAD)
8. `routing.py` — owner assignment + SLA + escalation_rule
9. `fusion.py` — deduplication with 7-day rolling window per (store, category)
10. `alerts.py` — evidence-backed alerts with uncertainty column
11. `briefs.py` — weekly regional briefs (markdown + JSON)
12. `data_models.py` — exports regions.parquet, routing_rules.parquet
13. `relationship_graph.py` — NetworkX graph (37k nodes, 74k edges)
14. `forecasting.py` — action-impact simulator
15. `evaluate.py` — hidden-label F1, escalation precision, seeded lead time
16. `run_pipeline.py` — orchestrates all of the above

Infrastructure:
17. `config_loader.py` — Pydantic v2 typed config
18. `versioning.py` — SHA-256 hashes of config/data/model
19. `security.py` — API key auth, 4 roles, rate limiting, correlation IDs, idempotency
20. `tracking.py` — action/resolution event log
21. `api.py` — FastAPI backend, 16+ endpoints
22. `ui.py` — Streamlit 5-view dashboard
23. `cli.py` — Typer CLI with subcommands
24. `run_pipeline.py` (listed above)

---

## 6. Current verified metrics

| Metric | Value |
|---|---|
| Total records | 40,053 |
| Classification accuracy (hidden) | 0.8910 |
| Classification macro-F1 (hidden) | 0.9167 |
| Weighted-F1 (hidden) | 0.9065 |
| Escalation precision | 0.9432 |
| Escalation recall | 0.0661 (by design — conservative policy) |
| Seeded incidents detected | 3 / 3 |
| Mean lead time vs peak | 3.67 days |
| Policy compliance | 100% (1260/1260) |
| Pipeline runtime | ~27-34 seconds |
| Ruff | clean |
| Pytest | 18/18 pass |

---

## 7. Key design rules (do not violate)

1. **Hidden labels** (`data/raw/hidden_labels.jsonl`) are ONLY read by
   `evaluate.py`. Never used for training, tuning, or seeded detection.
2. **Mandatory escalation** (`risk_policy.py`) fires on category OR
   weak_category OR severity, independent of classifier confidence.
3. **Prediction, anomaly detection, and policy escalation are separate
   modules.** Do not merge them.
4. **Fusion is a hypothesis.** Incidents carry `verification_status` field
   (defaults to "suspected"). External verifications merged from
   `data/evaluation/incident_verifications.jsonl`.
5. **Every alert has**: trigger_type, reason, evidence record IDs,
   owner_function, priority, uncertainty (= 1 - mean confidence).
6. **Deterministic**: fixed seed 20260214 in `generate_mock_data.py`.

---

## 8. Common commands

All commands are run from `$HOME/storesignal-ai/` unless noted.

    # Full rebuild from seed (~30s, deterministic)
    make pipeline

    # Individual stages
    make mock        # regenerate raw data
    make ingest      # run ingestion.py
    make normalize
    make classify
    make policy
    make radar
    make route
    make fuse
    make alerts
    make briefs
    make evaluate

    # Entity exports
    make entities    # runs data_models.py

    # Test / lint / coverage
    make test
    make lint
    make coverage

    # Servers (each blocks its terminal — run in separate tabs)
    make ui          # Streamlit → http://localhost:8501
    make serve       # FastAPI → http://localhost:8000/docs

    # CLI alternative
    "$HOME/storesignal-ai/.venv/bin/python" src/cli.py status
    "$HOME/storesignal-ai/.venv/bin/python" src/cli.py pipeline

    # Clean generated artifacts
    make clean

---

## 9. Known issues / gotchas

1. **Port conflicts**: Streamlit (8501) and uvicorn (8000) hold ports if
   not stopped with Ctrl+C. Fix:
       lsof -ti:8501 | xargs kill -9
       lsof -ti:8000 | xargs kill -9

2. **zsh history expansion**: any block containing `!` breaks unless
   prefixed with `set +H`.

3. **Heredoc truncation**: pasting very long `cat << 'EOF' > file` blocks
   sometimes truncates mid-paste. Mitigation: write long files via a
   Python script using `Path.write_text(...)`, or via base64.

4. **sklearn FutureWarning**: `n_jobs=-1` in LogisticRegression is a no-op
   in sklearn 1.8+. Already removed in classification.py.

5. **Streamlit deprecation**: `use_container_width` replaced with
   `width="stretch"` in ui.py. No warnings expected.

---

## 10. What has been tried and reverted

- **Kaggle Multilingual Retail Query Dataset (India)** was integrated on
  2026-10-16 as a test of real-data handling. The integration worked
  functionally (400 records flowed through the pipeline) but was
  **reverted** at the user's request because:
  - The weak labeler's fallback category (`store_cleanliness`) mislabeled
    most navigation-style queries.
  - Integration required adding a `merge_real_data.py` step, which
    modified `run_pipeline.py`.
  - User preferred to keep the project at the verified mock-only state.
- All Kaggle-related files removed; run_pipeline.py reverted; kaggle
  Python packages uninstalled. Current state is clean.

---

## 11. What's left to do

**Nothing required.** The project passes both spec audits fully.

Optional future work if user asks:
- Re-integrate a real dataset with proper intent mapping (not fallback).
- Add navigation-query keyword rules to `weak_labels.py`.
- Containerize and test with `docker compose up --build`.
- Render the pitch deck to PDF (`npx @marp-team/marp-cli`).
- Enforce 100% test coverage (`make coverage`).

---

## 12. How the user works

- **Non-programmer.** They cannot debug. Every terminal command must be
  copy-paste ready, absolute paths preferred, `set +H` at the top.
- **Prefers one block per step**, verified before moving on.
- **Values honesty** over polish. They've explicitly asked me to flag
  gaps and partial items, not paper over them.
- **Uses multiple terminal tabs** and switches randomly. Never assume
  a working directory.
- **Pattern that works well**:
    1. Give a block, wait for output.
    2. Read output, diagnose.
    3. Ship a corrective block if needed.
    4. Verify.

---

## 13. First thing you should do as the new assistant

Reply with:
1. A one-line confirmation you've read and understood this file.
2. A short summary of the current verified state (metrics + tests).
3. A question: "What would you like to do next?"

Do NOT paste any code until the user tells you what they want.

If the user asks you to change code, follow the working pattern in §12.

---

**END OF HANDOFF**

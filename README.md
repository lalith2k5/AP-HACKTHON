# StoreSignal AI — Voice-of-Store Engine

A multilingual retail operations intelligence system that turns scattered
customer and employee feedback into prioritized, evidence-backed actions.

**Built for:** Talent AP Mega Hackathon — R5 *Turning Store Chatter Into Action*
**Environment:** macOS 14+, Apple Silicon M2, Python 3.11

---

## What it does

1. **Ingests** ~40,000 feedback records from 4 channels (online reviews,
   in-app comments, staff shift notes, call-centre transcripts).
2. **Normalizes** noisy, code-mixed English / Hinglish / Tamil / Marathi
   text — typos, emojis, truncation, PII redaction.
3. **Classifies** into ~30 operational categories using TF-IDF
   (word + char n-grams) + Logistic Regression.
4. **Escalates by policy** — allergen, safety, hygiene, and staff-misconduct
   reports are escalated regardless of volume or classifier confidence.
5. **Detects weak signals early** — per-store, per-category robust z-score
   anomaly detection with MAD baselines.
6. **Deduplicates** near-identical reports across channels.
7. **Routes** each issue to its owning function (Store Ops, Supply Chain,
   Merchandising, Digital, HR) with next-action and SLA.
8. **Generates weekly regional briefs** with top-5 issues, evidence quotes,
   affected stores, and trend arrows.

---

## Quick start

    # 1. Setup (one time)
    cd "$HOME/storesignal-ai"
    uv venv --python 3.11 "$HOME/storesignal-ai/.venv"
    uv pip install --python "$HOME/storesignal-ai/.venv/bin/python" \
      pandas pyarrow numpy scipy scikit-learn rapidfuzz \
      "pydantic>=2" fastapi "uvicorn[standard]" streamlit \
      typer rich pytest pytest-cov joblib pyyaml ruff

    # 2. Full pipeline
    make pipeline

    # 3. Dashboard (http://localhost:8501)
    make ui

    # 4. API (http://localhost:8000/docs)
    make serve

---

## Results (measured, not fabricated)

| Metric | Value |
|---|---|
| Classification accuracy (hidden) | 0.8910 |
| Classification macro-F1 (hidden) | 0.9167 |
| Classification weighted-F1 | 0.9065 |
| Escalation precision | 0.9432 |
| Seeded incidents detected | 3/3 |
| Mean lead time vs peak | 3.67 days |

---

## Design principles

- Feedback is unverified evidence, not automatic proof of a systemic issue.
- Mandatory escalation is independent of volume and of classifier confidence.
- Hidden evaluation labels are only consumed inside `evaluate.py` — never
  for training, tuning, or seeded-incident identification.
- Every displayed claim traces back to source records.

---

## Layout

    config/config.yaml        Central configuration
    data/raw/                 4 channel JSONL + hidden labels + seeds
    data/reference/           store_master.csv + taxonomy.csv
    data/processed/           Parquet artifacts per stage
    data/processed/briefs/    Regional weekly briefs (.json + .md)
    data/evaluation/reports/  evaluation_report.{json,md}
    models/                   baseline_model.joblib
    src/                      Pipeline modules (15 files)
    tests/                    Smoke + policy invariant tests
    Makefile                  Reproducible targets
    pyproject.toml            Ruff + pytest config

---

## Make targets

- `make pipeline` — run every stage end to end
- `make serve`    — FastAPI on :8000
- `make ui`       — Streamlit on :8501
- `make test`     — pytest
- `make lint`     — ruff
- `make clean`    — remove generated artifacts

---

## Limitations & future work

- File-based storage (Parquet/CSV/YAML). Transactional DB is a future extension.
- Not evaluated: multilingual embeddings, transformer NLP, relationship graph,
  action-impact simulator.
- No live retailer integration; no audio transcription.
- Human review required for safety, compliance, and staff-related decisions.

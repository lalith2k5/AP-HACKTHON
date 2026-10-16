# Operations Runbook — StoreSignal AI

Local-first MVP. For production deployment see PRODUCTION_READINESS.md.

## Health checks

    curl -s http://localhost:8000/health | jq

Response:
    {
      "status": "ok" | "degraded",
      "version": "0.2.0",
      "readiness": {
        "config": true, "model": true, "data_dir": true,
        "imports_dir": true, "errors": []
      },
      "demo_mode": true, "env": "development"
    }

Status is `degraded` when config or model is missing. Investigate readiness.errors.

## Logs

Structured JSON to stderr, one object per line. Fields:
timestamp, level, component, event, request_id, run_id, stage,
duration_ms, records_in, records_out, error_code.

Tail logs:

    "$HOME/storesignal-ai/.venv/bin/python" -m storesignal.pipeline 2> logs/pipeline.jsonl

## Common incidents

### Pipeline fails on stage N
1. Read stderr — the failing stage is named in `[pipeline] FAILED`.
2. Confirm config loads: `python -m storesignal.config_loader`.
3. Confirm model artifact: `ls models/baseline_model.joblib`.
4. Retry: `python -m storesignal.pipeline`. Stages are idempotent.

### Port conflict (8000 or 8501)

    lsof -ti:8501 | xargs kill -9
    lsof -ti:8000 | xargs kill -9

### Hidden-eval guard blocks evaluate

    STORESIGNAL_ALLOW_HIDDEN_EVAL=true "$HOME/storesignal-ai/.venv/bin/python" -m storesignal.evaluate

Only in a controlled environment. See spec 17.2.

### Reset demo artifacts

    git clean -fd data/processed
    "$HOME/storesignal-ai/.venv/bin/python" -m storesignal.pipeline

## Backups

Critical assets to back up before any schema or code change:
- `config/*.yaml`
- `data/reference/store_master.csv`, `taxonomy.csv`
- `models/baseline_model.joblib`
- `data/processed/audit.log`
- `data/evaluation/reports/*`
- `data/processed/briefs/*`

    tar czf "backup-$(date +%Y%m%d).tgz" \
      config data/reference models data/evaluation data/processed/briefs

## Rollback

Git-tagged history. To roll back to the last verified commit:

    git reset --hard HEAD~1 && git clean -fd

Baseline tag: `pre-v2-build` (pre-restructure state).

## Restart procedure

    cd "$HOME/storesignal-ai"
    git pull
    "$HOME/storesignal-ai/.venv/bin/python" -m pip install -e . --quiet
    "$HOME/storesignal-ai/.venv/bin/python" -m storesignal.pipeline
    "$HOME/storesignal-ai/.venv/bin/python" -m pytest -q tests

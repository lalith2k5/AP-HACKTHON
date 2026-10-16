"""
StoreSignal AI - spec 14.2 job endpoints
==========================================
Long-running operations: ingest, pipeline run, evaluation run.
Each returns a job/run ID; clients poll the status endpoint.

Job registry is in-process. Single-worker uvicorn only. For
multi-worker, replace _JOBS with a shared store (Redis/SQLite).
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query

from storesignal.paths import PROCESSED_DIR
from storesignal.security import (
    audit,
    check_idempotency,
    require_permission,
    store_idempotency,
)

router = APIRouter(prefix="/api/v1", tags=["jobs"])

_perm_read = require_permission("read_overview")
_perm_run = require_permission("read_overview")

_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def _new_job(kind: str, meta: dict | None = None) -> dict[str, Any]:
    jid = f"{kind}-{uuid.uuid4().hex[:12]}"
    job = {
        "job_id": jid,
        "kind": kind,
        "status": "queued",
        "stage": "queued",
        "created_at": time.time(),
        "updated_at": time.time(),
        "meta": meta or {},
        "counts": {},
        "warnings": [],
        "error": None,
    }
    with _LOCK:
        _JOBS[jid] = job
    return job


def _update(jid: str, **kw) -> None:
    with _LOCK:
        if jid in _JOBS:
            _JOBS[jid].update(kw)
            _JOBS[jid]["updated_at"] = time.time()


def _run_pipeline_job(jid: str) -> None:
    _update(jid, status="running", stage="generate_mock_data")
    try:
        from storesignal import pipeline as _pipeline
        stages = getattr(_pipeline, "STAGES", None) or getattr(_pipeline, "STAGE_ORDER", None)
        _update(jid, counts={"stages_total": len(stages) if stages else 0})
        if hasattr(_pipeline, "main"):
            _pipeline.main()
        elif hasattr(_pipeline, "run"):
            _pipeline.run()
        else:
            raise RuntimeError("pipeline module exposes neither main() nor run()")
        _update(jid, status="succeeded", stage="done")
        audit("pipeline_run_completed", "system", f"job={jid}")
    except Exception as e:
        _update(jid, status="failed", stage="error", error=str(e))
        audit("pipeline_run_failed", "system", f"job={jid} err={e}")


def _run_eval_job(jid: str) -> None:
    _update(jid, status="running", stage="evaluate")
    try:
        from storesignal import evaluate as _eval
        if hasattr(_eval, "main"):
            _eval.main()
        elif hasattr(_eval, "run"):
            _eval.run()
        else:
            raise RuntimeError("evaluate module exposes neither main() nor run()")
        _update(jid, status="succeeded", stage="done")
        audit("evaluation_run_completed", "system", f"job={jid}")
    except Exception as e:
        _update(jid, status="failed", stage="error", error=str(e))
        audit("evaluation_run_failed", "system", f"job={jid} err={e}")


@router.get("/jobs/{job_id}")
def job_status(job_id: str, _p=Depends(_perm_read)):  # noqa: B008
    with _LOCK:
        job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"unknown job: {job_id}")
    return job


class PipelineRunIn(dict):
    pass


@router.post("/pipeline/run")
def pipeline_run(
    bg: BackgroundTasks,
    payload: dict = Body(default={}),  # noqa: B008
    idempotency_key: str | None = Query(default=None),
    _p=Depends(_perm_run),  # noqa: B008
):
    if idempotency_key:
        cached = check_idempotency(idempotency_key)
        if cached:
            return cached
    job = _new_job("pipeline", {"filters": payload})
    bg.add_task(_run_pipeline_job, job["job_id"])
    resp = {"run_id": job["job_id"], "status": "accepted",
            "poll": f"/api/v1/pipeline/{job['job_id']}"}
    if idempotency_key:
        store_idempotency(idempotency_key, "/api/v1/pipeline/run", resp)
    return resp


@router.get("/pipeline/{run_id}")
def pipeline_status(run_id: str, _p=Depends(_perm_read)):  # noqa: B008
    with _LOCK:
        job = _JOBS.get(run_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"unknown run: {run_id}")
    return job


class IngestIn(dict):
    pass


@router.post("/ingest")
def ingest(
    bg: BackgroundTasks,
    payload: dict = Body(default={}),  # noqa: B008
    idempotency_key: str | None = Query(default=None),
    _p=Depends(_perm_run),  # noqa: B008
):
    """
    Spec 14.2: multipart file + column mapping in production.
    Local MVP accepts JSON body:
      { "path": "data/raw/x.csv", "mapping": {...}, "format": "csv" }
    or inline rows:
      { "rows": [ {...}, ... ], "mapping": {...} }
    """
    if idempotency_key:
        cached = check_idempotency(idempotency_key)
        if cached:
            return cached

    path = payload.get("path")
    rows = payload.get("rows")
    mapping = payload.get("mapping") or {}
    fmt = payload.get("format") or ("csv" if path else "inline")

    if not path and not rows:
        raise HTTPException(status_code=422,
                            detail="ingest requires either 'path' or 'rows'")

    job = _new_job("ingest", {"path": path, "format": fmt,
                              "mapping_keys": list(mapping.keys())})

    def _do(jid: str):
        _update(jid, status="running", stage="validate")
        try:
            from storesignal import process_import as _pi
            if path:
                p = Path(path)
                if not p.is_absolute():
                    from storesignal.paths import CODE_ROOT
                    p = CODE_ROOT / path
                if not p.exists():
                    raise FileNotFoundError(f"file not found: {p}")
                if hasattr(_pi, "process_file"):
                    result = _pi.process_file(p, mapping=mapping)
                else:
                    raise RuntimeError("process_import.process_file not available")
            else:
                if hasattr(_pi, "process_rows"):
                    result = _pi.process_rows(rows, mapping=mapping)
                else:
                    raise RuntimeError("process_import.process_rows not available")
            _update(jid, status="succeeded", stage="done",
                    counts=result if isinstance(result, dict) else {"result": str(result)})
            audit("ingest_completed", "system", f"job={jid} path={path}")
        except Exception as e:
            _update(jid, status="failed", stage="error", error=str(e))
            audit("ingest_failed", "system", f"job={jid} err={e}")

    bg.add_task(_do, job["job_id"])
    resp = {"import_id": job["job_id"], "status": "accepted",
            "poll": f"/api/v1/ingest/{job['job_id']}"}
    if idempotency_key:
        store_idempotency(idempotency_key, "/api/v1/ingest", resp)
    return resp


@router.get("/ingest/{job_id}")
def ingest_status(job_id: str, _p=Depends(_perm_read)):  # noqa: B008
    with _LOCK:
        job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"unknown ingest: {job_id}")
    return job


@router.post("/evaluation/run")
def evaluation_run(
    bg: BackgroundTasks,
    payload: dict = Body(default={}),  # noqa: B008
    idempotency_key: str | None = Query(default=None),
    _p=Depends(_perm_run),  # noqa: B008
):
    if idempotency_key:
        cached = check_idempotency(idempotency_key)
        if cached:
            return cached
    job = _new_job("evaluation", {"payload": payload})
    bg.add_task(_run_eval_job, job["job_id"])
    resp = {"evaluation_run_id": job["job_id"], "status": "accepted",
            "poll": f"/api/v1/evaluation/{job['job_id']}"}
    if idempotency_key:
        store_idempotency(idempotency_key, "/api/v1/evaluation/run", resp)
    return resp


@router.get("/evaluation/{run_id}")
def evaluation_status(run_id: str, _p=Depends(_perm_read)):  # noqa: B008
    report_path = PROCESSED_DIR.parent / "evaluation" / "reports" / "evaluation_report.json"
    with _LOCK:
        job = _JOBS.get(run_id)
    if job:
        if job["status"] == "succeeded" and report_path.exists():
            try:
                job = dict(job)
                job["report"] = json.loads(report_path.read_text())
            except Exception:
                pass
        return job
    if report_path.exists():
        return {"evaluation_run_id": "latest", "status": "succeeded",
                "report": json.loads(report_path.read_text())}
    raise HTTPException(status_code=404, detail=f"unknown evaluation: {run_id}")


class ReplayIn(dict):
    pass


@router.post("/replay")
def replay_post(payload: dict = Body(default={}),  # noqa: B008
                _p=Depends(_perm_read)):  # noqa: B008
    incident_id = payload.get("incident_id")
    if not incident_id:
        raise HTTPException(status_code=422, detail="incident_id required")
    return _replay_impl(incident_id)


@router.get("/replay/{incident_id}")
def replay_get(incident_id: str, _p=Depends(_perm_read)):  # noqa: B008
    return _replay_impl(incident_id)


def _replay_impl(incident_id: str) -> dict:
    inc_path = PROCESSED_DIR / "incidents.parquet"
    if not inc_path.exists():
        raise HTTPException(status_code=503, detail="incidents.parquet not built")
    import pandas as pd
    df = pd.read_parquet(inc_path, engine="pyarrow")
    row = df[df["incident_id"] == incident_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"unknown incident: {incident_id}")
    r = row.iloc[0].to_dict()
    evidence_ids: list[str] = []
    raw = r.get("sample_text")
    if isinstance(raw, str) and raw.strip():
        evidence_ids = [raw[:120]]
    return {
        "incident_id": incident_id,
        "replayed": True,
        "store_id": r.get("store_id"),
        "category": r.get("predicted_category"),
        "severity": r.get("severity"),
        "first_seen": str(r.get("first_seen")),
        "last_seen": str(r.get("last_seen")),
        "record_count": r.get("record_count"),
        "evidence_snippets": evidence_ids,
        "note": "Local deterministic replay from frozen artifacts.",
    }


@router.get("/briefs/{region_id}")
def brief_for_region(
    region_id: str,
    from_ts: str | None = Query(default=None, alias="from"),
    to_ts: str | None = Query(default=None, alias="to"),
    format: str = Query(default="json"),
    _p=Depends(_perm_read),  # noqa: B008
):
    from fastapi.responses import PlainTextResponse

    from storesignal.briefs import generate_weekly_brief

    try:
        brief = generate_weekly_brief(region_id=region_id,
                                      from_ts=from_ts, to_ts=to_ts)
    except TypeError:
        brief = generate_weekly_brief(region_id)

    if format == "markdown" or format == "md":
        text = brief.get("markdown") if isinstance(brief, dict) else str(brief)
        return PlainTextResponse(text or "")
    return brief

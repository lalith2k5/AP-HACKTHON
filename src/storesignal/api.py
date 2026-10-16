"""
StoreSignal AI — FastAPI backend (full spec coverage)
=====================================================
API key auth with roles, rate limiting, audit logging, correlation IDs,
idempotency keys, spec-compliant classify response.
"""

import json
import time
import uuid
from collections import defaultdict as _defaultdict
from collections import deque as _deque

import pandas as pd
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from storesignal.api_envelope import install as install_envelope
from storesignal.config_loader import load_config
from storesignal.paths import (
    CODE_ROOT,
    PROCESSED_DIR,
    REFERENCE_DIR,
    REPORTS_DIR,
)
from storesignal.security import (
    audit,
    check_idempotency,
    install_security,
    require_permission,
    resolve_role,
    store_idempotency,
)
from storesignal.tracking import record_event
from storesignal.tracking import summarize as tracking_summary
from storesignal import state as _state

ROOT = CODE_ROOT
PROC = PROCESSED_DIR
TAXONOMY_CSV = REFERENCE_DIR / "taxonomy.csv"
_cfg = load_config()

MANDATORY = set(_cfg.risk_policy.mandatory_categories)
OWNER_MAP = {}
if TAXONOMY_CSV.exists():
    _tax = pd.read_csv(TAXONOMY_CSV, dtype=str)
    OWNER_MAP = dict(zip(_tax["category_id"], _tax["default_owner"]))
NEXT_ACTION = dict(_cfg.routing.next_action_by_owner)

app = FastAPI(
    title="StoreSignal AI API",
    version="0.3.0",
    description="Voice-of-Store Engine — early-warning and incident-resolution intelligence layer.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3300",
        "http://127.0.0.1:3300",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Rate limiting (spec 18) — in-memory, per-IP, 300 req/min.
# For multi-user production: replace with a shared store (Redis).
# ---------------------------------------------------------------------------
_RATE_BUCKETS: dict = _defaultdict(_deque)
_RATE_LIMIT = 300
_RATE_WINDOW = 60.0


@app.middleware("http")
async def _rate_limit_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    bucket = _RATE_BUCKETS[ip]
    while bucket and bucket[0] < now - _RATE_WINDOW:
        bucket.popleft()
    if len(bucket) >= _RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"error": {"code": "RATE_LIMITED",
                               "message": "too many requests"}},
        )
    bucket.append(now)
    return await call_next(request)

install_envelope(app)

install_security(app)

_CACHE = {}


def _load(name, path):
    if name not in _CACHE:
        if not path.exists():
            raise HTTPException(status_code=503, detail=f"artifact not built: {path.name}")
        _CACHE[name] = pd.read_parquet(path, engine="pyarrow")
    return _CACHE[name]


def preds():       return _load("preds",       PROC / "predictions.parquet")
def routing():     return _load("routing",     PROC / "routing.parquet")
def escalations(): return _load("escalations", PROC / "escalations.parquet")
def incidents():   return _load("incidents",   PROC / "incidents.parquet")
def links():       return _load("links",       PROC / "incident_links.parquet")
def alerts():      return _load("alerts",      PROC / "alerts.parquet")
def radar():       return _load("radar",       PROC / "radar_flags.parquet")
def forecasts():   return _load("forecasts",   PROC / "forecasts.parquet")


class FeedbackIn(BaseModel):
    record_id: str
    source_id: str
    channel: str
    store_id: str
    timestamp: str
    text_raw: str
    rating: int | None = None
    language_hint: str | None = None


class ClassifyIn(BaseModel):
    text: str = Field(min_length=1)


class AlertAction(BaseModel):
    actor: str
    note: str | None = None
    status: str | None = None


def _coerce(value):
    """Convert pandas/numpy scalars to JSON-friendly Python types."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return str(value)


@app.get("/health")
def health():
    """Liveness + readiness. Never exposes secrets."""
    from storesignal import settings as _s
    from storesignal.import_wizard import IMPORT_DIR
    errs = _s.validate_startup()
    model_ok = (_s.MODEL_DIR / "baseline_model.joblib").exists()
    demo = _s.DEMO_MODE
    return {
        "status": "ok" if not errs else "degraded",
        "version": "0.2.0",
        "readiness": {
            "config": not any("config" in e for e in errs),
            "model": model_ok,
            "data_dir": _s.DATA_DIR.exists(),
            "imports_dir": IMPORT_DIR.exists(),
            "errors": errs,
        },
        "demo_mode": demo,
        "env": _s.ENV,
    }


@app.post("/api/v1/feedback/batch",
          dependencies=[Depends(require_permission("ingest"))])
def ingest_batch(
    records: list[FeedbackIn],
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    cached = check_idempotency(idempotency_key)
    if cached:
        return {**cached["response"], "idempotent_replay": True}
    payload = {"status": "accepted", "count": len(records)}
    store_idempotency(idempotency_key, "POST /api/v1/feedback/batch", payload)
    audit("feedback_batch", "api", f"{len(records)} records")
    return payload


@app.get("/api/v1/feedback/{record_id}")
def get_feedback(record_id: str):
    df = preds()
    row = df[df["record_id"] == record_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="record not found")
    return {k: _coerce(v) for k, v in row.iloc[0].to_dict().items()}


# ---------------------------------------------------------------------------
# Classify — spec §6.2 compliant response
# ---------------------------------------------------------------------------
@app.post("/api/v1/classify",
          dependencies=[Depends(require_permission("ingest"))])
def classify(
    payload: ClassifyIn,
    x_request_id: str | None = Header(default=None),
):
    import joblib
    model_path = ROOT / "models" / "baseline_model.joblib"
    if not model_path.exists():
        raise HTTPException(status_code=503, detail="model not trained yet")
    bundle = joblib.load(model_path)
    vec = bundle["vectorizer"]
    clf = bundle["classifier"]
    X = vec.transform([payload.text])
    cat = clf.predict(X)[0]
    proba = float(clf.predict_proba(X).max())
    sev = bundle["severity_map"].get(cat, "medium")
    actionable = bundle["actionable_by_severity"].get(sev, False)
    policy_escalation = cat in MANDATORY
    suggested_owner = OWNER_MAP.get(cat, "Store Ops")
    live_id = f"LIVE-{uuid.uuid4().hex[:10].upper()}"
    audit("classify", "api", cat, request_id=x_request_id or "?")
    return {
        "record_id": live_id,
        "issue_category": cat,
        "severity": sev,
        "actionable": actionable,
        "confidence": round(proba, 4),
        "policy_escalation": policy_escalation,
        "suggested_owner": suggested_owner,
        "next_action": NEXT_ACTION.get(suggested_owner, ""),
        "evidence": [payload.text],
        "model_version": "baseline-v1",
        "status": "predicted",
    }


# ---------------------------------------------------------------------------
# State overrides (append-only JSONL; latest wins per (id, field))
# ---------------------------------------------------------------------------
def _apply_overrides(d, kind, id_field, id_value):
    """Apply latest overrides from SQLite state store."""
    if kind == "incident":
        ov = _state.latest_incident_overrides(id_value)
    elif kind == "alert":
        ov = _state.latest_alert_overrides(id_value)
    else:
        ov = {}
    for k, v in ov.items():
        d[k] = v
    d["_overridden_fields"] = sorted(ov.keys())
    return d


class IncidentPatch(BaseModel):
    actor: str = Field(default="demo-operator")
    owner_function: str | None = None
    owner_id: str | None = None
    status: str | None = None
    priority: str | None = None
    reason: str | None = None


class NoteBody(BaseModel):
    actor: str = Field(default="demo-operator")
    note: str


class AlertAck(BaseModel):
    actor: str = Field(default="demo-operator")
    note: str | None = None
    decision: str | None = None


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------
@app.get("/api/v1/incidents")
def list_incidents(
    store_id: str | None = None,
    category: str | None = None,
    severity: str | None = None,
    verification_status: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
):
    df = incidents().copy()
    if store_id: df = df[df["store_id"] == store_id]
    if category: df = df[df["predicted_category"] == category]
    if severity: df = df[df["severity"] == severity]
    if verification_status and "verification_status" in df.columns:
        df = df[df["verification_status"] == verification_status]
    df = df.sort_values("record_count", ascending=False).head(limit)
    return [{k: _coerce(v) for k, v in row.items()} for row in df.to_dict(orient="records")]


@app.get("/api/v1/incidents/{incident_id}")
def get_incident(incident_id: str):
    inc = incidents()
    row = inc[inc["incident_id"] == incident_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="incident not found")
    rec = {k: _coerce(v) for k, v in row.iloc[0].to_dict().items()}
    rec = _apply_overrides(rec, "incident", "incident_id", incident_id)
    rec["evidence"] = links()[links()["incident_id"] == incident_id]["record_id"].tolist()
    rec["notes"] = [n for n in _read_jsonl(_notes_path()) if n.get("incident_id") == incident_id]
    return rec


@app.patch("/api/v1/incidents/{incident_id}",
          dependencies=[Depends(require_permission("record_action"))])
def patch_incident(incident_id: str, body: IncidentPatch):
    """MVP demo: no auth dependency (matches read endpoints in demo mode)."""
    inc = incidents()
    row = inc[inc["incident_id"] == incident_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="incident not found")
    before = {k: _coerce(v) for k, v in row.iloc[0].to_dict().items()}
    before = _apply_overrides(before, "incident", "incident_id", incident_id)
    updates = body.model_dump(exclude_none=True, exclude={"actor", "reason"})
    if not updates:
        raise HTTPException(status_code=422, detail="no fields to update")
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for field, value in updates.items():
        _state.append_incident_override(
            incident_id, field, value, body.actor, body.reason,
        )
    audit("incident.status_changed", body.actor, incident_id,
          before={k: before.get(k) for k in updates},
          after=updates, reason=body.reason)
    after = _apply_overrides(before, "incident", "incident_id", incident_id)
    return {"incident_id": incident_id, "before": before, "after": after}


@app.post("/api/v1/incidents/{incident_id}/notes",
          dependencies=[Depends(require_permission("record_action"))])
def post_incident_note(incident_id: str, body: NoteBody):
    inc = incidents()
    if inc[inc["incident_id"] == incident_id].empty:
        raise HTTPException(status_code=404, detail="incident not found")
    if not body.note.strip():
        raise HTTPException(status_code=422, detail="note cannot be empty")
    rec = _state.add_note(incident_id, body.actor, body.note)
    audit("incident.note_added", body.actor, incident_id,
          note_preview=body.note[:120])
    return rec


@app.get("/api/v1/incidents/{incident_id}/timeline")
def incident_timeline(incident_id: str):
    inc = incidents()
    row = inc[inc["incident_id"] == incident_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="incident not found")
    r = row.iloc[0]
    events = []
    if _coerce(r.get("first_seen")):
        events.append({"ts": str(_coerce(r.get("first_seen"))), "kind": "first_seen",
                       "label": "Incident first observed"})
    if _coerce(r.get("last_seen")):
        events.append({"ts": str(_coerce(r.get("last_seen"))), "kind": "last_seen",
                       "label": "Most recent record in window"})
    for ov in _state.incident_override_history(incident_id):
        events.append(ov)
    for nt in _state.notes_for(incident_id):
        events.append({"ts": nt.get("ts"), "kind": "note",
                       "label": (nt.get("note") or "")[:200],
                       "actor": nt.get("actor")})
    events = [e for e in events if e.get("ts")]
    events.sort(key=lambda e: str(e["ts"]))
    return {"incident_id": incident_id, "events": events}


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------
@app.get("/api/v1/alerts")
def list_alerts(
    trigger_type: str | None = None,
    severity: str | None = None,
    owner: str | None = None,
    status: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
):
    df = alerts().copy()
    if trigger_type: df = df[df["trigger_type"] == trigger_type]
    if severity: df = df[df["severity"] == severity]
    if owner: df = df[df["owner_function"] == owner]
    df = df.sort_values("priority", ascending=False).head(limit)
    records = []
    for row in df.to_dict(orient="records"):
        rec = {k: _coerce(v) for k, v in row.items()}
        rec = _apply_overrides(rec, "alert", "alert_id", rec.get("alert_id", ""))
        rec.setdefault("status", "open")
        if status and rec.get("status") != status:
            continue
        records.append(rec)
    return records


@app.post("/api/v1/alerts/{alert_id}/acknowledge",
          dependencies=[Depends(require_permission("review_alert"))])
def ack_alert(alert_id: str, body: AlertAck):
    df = alerts()
    if df[df["alert_id"] == alert_id].empty:
        raise HTTPException(status_code=404, detail="alert not found")
    ts = _state.append_alert_override(
        alert_id, "status", "acknowledged", body.actor, body.note,
    )
    audit("alert.acknowledged", body.actor, alert_id)
    return {"alert_id": alert_id, "status": "acknowledged", "ts": ts}


@app.post("/api/v1/alerts/{alert_id}/resolve",
          dependencies=[Depends(require_permission("review_alert"))])
def resolve_alert(alert_id: str, body: AlertAck):
    df = alerts()
    if df[df["alert_id"] == alert_id].empty:
        raise HTTPException(status_code=404, detail="alert not found")
    ts = _state.append_alert_override(
        alert_id, "status", "resolved", body.actor, body.note,
    )
    audit("alert.resolved", body.actor, alert_id)
    return {"alert_id": alert_id, "status": "resolved", "ts": ts}


@app.post("/api/v1/alerts/{alert_id}/override",
          dependencies=[Depends(require_permission("review_alert"))])
def override_alert(alert_id: str, body: AlertAck):
    df = alerts()
    if df[df["alert_id"] == alert_id].empty:
        raise HTTPException(status_code=404, detail="alert not found")
    if not (body.note and body.note.strip()):
        raise HTTPException(status_code=422, detail="override requires a reason")
    ts = _state.append_alert_override(
        alert_id, "status", "suppressed_with_reason",
        body.actor, body.note, body.decision or "suppressed",
    )
    audit("alert.overridden", body.actor, alert_id,
          decision=body.decision, reason=body.note)
    return {"alert_id": alert_id, "status": "suppressed_with_reason", "ts": ts}


@app.post("/api/v1/alerts/{alert_id}/review",
          dependencies=[Depends(require_permission("review_alert"))])
def review_alert(
    alert_id: str,
    body: AlertAction,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    cached = check_idempotency(idempotency_key)
    if cached:
        return {**cached["response"], "idempotent_replay": True}
    rec = record_event("review", alert_id, body.actor, body.note or "",
                       body.status or "reviewed")
    audit("alert_review", body.actor, alert_id)
    payload = {"status": "reviewed", "event": rec}
    store_idempotency(idempotency_key, "POST /api/v1/alerts/{id}/review", payload)
    return payload


@app.post("/api/v1/alerts/{alert_id}/assign",
          dependencies=[Depends(require_permission("assign_alert"))])
def assign_alert(
    alert_id: str,
    body: AlertAction,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    cached = check_idempotency(idempotency_key)
    if cached:
        return {**cached["response"], "idempotent_replay": True}
    rec = record_event("assign", alert_id, body.actor, body.note or "",
                       body.status or "assigned")
    audit("alert_assign", body.actor, alert_id)
    payload = {"status": "assigned", "event": rec}
    store_idempotency(idempotency_key, "POST /api/v1/alerts/{id}/assign", payload)
    return payload


@app.post("/api/v1/actions",
          dependencies=[Depends(require_permission("record_action"))])
def record_action_endpoint(
    body: AlertAction,
    alert_id: str = Query(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    cached = check_idempotency(idempotency_key)
    if cached:
        return {**cached["response"], "idempotent_replay": True}
    rec = record_event("action", alert_id, body.actor, body.note or "",
                       body.status or "in_progress")
    audit("action_recorded", body.actor, alert_id)
    payload = {"status": "recorded", "event": rec}
    store_idempotency(idempotency_key, "POST /api/v1/actions", payload)
    return payload


@app.get("/api/v1/tracking/summary")
def tracking_summary_endpoint():
    return tracking_summary()


# ---------------------------------------------------------------------------
# Briefs
# ---------------------------------------------------------------------------
@app.get("/api/v1/briefs/weekly")
def get_brief(region_id: str | None = None):
    briefs_dir = PROC / "briefs"
    if region_id:
        files = sorted(briefs_dir.glob(f"brief_{region_id}_*.json"))
    else:
        files = sorted(briefs_dir.glob("brief_*.json"))
    if not files:
        raise HTTPException(
            status_code=404,
            detail="brief not found; run POST /api/v1/briefs/weekly/generate",
        )
    with open(files[-1], encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/v1/briefs/weekly/generate",
          dependencies=[Depends(require_permission("generate_brief"))])
def generate_brief(region_id: str = Query(...)):
    import subprocess
    PY = ROOT / ".venv" / "bin" / "python"
    SRC = ROOT / "src"
    res = subprocess.run([str(PY), "-m", "storesignal.briefs"],
                         check=False, cwd=str(SRC))
    if res.returncode != 0:
        raise HTTPException(status_code=500, detail="brief regeneration failed")
    audit("brief_generate", "api", region_id)
    return get_brief(region_id)


@app.get("/api/v1/replay/{incident_id}")
def replay(incident_id: str):
    return get_incident(incident_id)


@app.get("/api/v1/overview")
def overview(region_id: str | None = None):
    """Composed dashboard payload for the Next.js Overview screen (spec 14.2)."""
    import pandas as _pd

    inc = incidents().copy()
    alt = alerts().copy()
    # Region filter: derive from store_id prefix (S-DEL-001 -> DEL)
    if region_id:
        def _reg(df):
            if "region_id" in df.columns:
                return df[df["region_id"] == region_id]
            if "store_id" in df.columns:
                return df[df["store_id"].astype(str).str.split("-").str[1] == region_id]
            return df
        inc = _reg(inc)
        alt = _reg(alt)

    # KPIs
    kpis = []
    kpis.append({"label": "Open incidents", "value": int(len(inc))})
    kpis.append({"label": "Escalated alerts", "value": int(len(alt))})
    crit = int((alt["severity"] == "critical").sum()) if "severity" in alt.columns else 0
    kpis.append({"label": "Critical alerts", "value": crit})
    # Accuracy from metrics if the file exists
    try:
        m = metrics()
        acc = m.get("classification", {}).get("accuracy")
        if acc is not None:
            kpis.append({"label": "Model accuracy", "value": round(float(acc), 3)})
    except Exception:
        pass

    # Urgent queue: top alerts by priority, fallback to severity ordering
    if "priority" in alt.columns:
        urgent = alt.sort_values("priority", ascending=False).head(8)
    elif "severity" in alt.columns:
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        urgent = alt.assign(_o=alt["severity"].map(order).fillna(9)).sort_values("_o").head(8)
    else:
        urgent = alt.head(8)
    urgent_queue = [
        {
            "id": str(r.get("alert_id") or r.get("incident_id") or ""),
            "title": str(r.get("reason") or r.get("predicted_category") or "Alert"),
            "severity": str(r.get("severity") or "unknown"),
        }
        for _, r in urgent.iterrows()
    ]

    # Categories from incidents
    categories = []
    if "predicted_category" in inc.columns and len(inc):
        counts = inc["predicted_category"].value_counts().head(12)
        categories = [{"category": str(k), "count": int(v)} for k, v in counts.items()]

    # Freshness
    freshness = None
    if "last_seen" in inc.columns and len(inc):
        try:
            freshness = str(_pd.to_datetime(inc["last_seen"]).max())
        except Exception:
            freshness = str(inc["last_seen"].max())

    return {
        "kpis": kpis,
        "urgent_queue": urgent_queue,
        "categories": categories,
        "freshness": freshness,
    }


@app.get("/api/v1/metrics")
def metrics():
    for p in [REPORTS_DIR / "evaluation_report.json",
              PROC / "evaluation_report.json"]:
        if p.exists():
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    return {"status": "not_yet_evaluated"}


@app.get("/api/v1/forecasts")
def list_forecasts(store_id: str | None = None, limit: int = 50):
    df = forecasts().copy()
    if store_id:
        df = df[df["store_id"] == store_id]
    df = df.sort_values("act_now_advantage", ascending=False).head(limit)
    return [{k: _coerce(v) for k, v in row.items()} for row in df.to_dict(orient="records")]


_JOBS: dict = {}


def _run_reset_bg(job_id: str):
    import subprocess
    job = _JOBS[job_id]
    job["status"] = "running"
    try:
        result = _state.clear_all_state()
        job["cleared_state_files"] = result["cleared"]
        PY = ROOT / ".venv" / "bin" / "python"
        SRC = ROOT / "src"
        res = subprocess.run(
            [str(PY), "-m", "storesignal.pipeline"],
            check=False, cwd=str(SRC),
        )
        if res.returncode != 0:
            job["status"] = "failed"
            job["error"] = f"pipeline exited {res.returncode}"
        else:
            job["status"] = "succeeded"
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
    finally:
        job["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        audit("demo_reset", "api",
              f"job={job_id} status={job['status']}")


@app.post("/api/v1/demo/reset",
          dependencies=[Depends(require_permission("reset"))])
def reset(background_tasks: BackgroundTasks):
    """Async reset. Returns job_id immediately; poll /api/v1/jobs/{id}."""
    job_id = "JOB-" + uuid.uuid4().hex[:12]
    _JOBS[job_id] = {
        "job_id": job_id,
        "kind": "demo_reset",
        "status": "queued",
        "queued_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "started_at": None,
        "finished_at": None,
        "cleared_state_files": [],
        "error": None,
    }
    _JOBS[job_id]["started_at"] = _JOBS[job_id]["queued_at"]
    background_tasks.add_task(_run_reset_bg, job_id)
    return {"job_id": job_id, "status": "queued",
            "poll": f"/api/v1/jobs/{job_id}"}


@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/api/v1/me")
def whoami(x_api_key: str | None = Header(default=None)):
    role = resolve_role(x_api_key) or "anonymous"
    return {"role": role}

"""
StoreSignal AI — FastAPI backend (full spec coverage)
=====================================================
API key auth with roles, rate limiting, audit logging, correlation IDs,
idempotency keys, spec-compliant classify response.
"""

import json
import uuid
from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from storesignal.config_loader import load_config
from storesignal.api_envelope import install as install_envelope
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

ROOT = Path.home() / "storesignal-ai"
PROC = ROOT / "data" / "processed"
TAXONOMY_CSV = ROOT / "data" / "reference" / "taxonomy.csv"
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
    rec["evidence"] = links()[links()["incident_id"] == incident_id]["record_id"].tolist()
    return rec


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------
@app.get("/api/v1/alerts")
def list_alerts(
    trigger_type: str | None = None,
    severity: str | None = None,
    owner: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
):
    df = alerts().copy()
    if trigger_type: df = df[df["trigger_type"] == trigger_type]
    if severity: df = df[df["severity"] == severity]
    if owner: df = df[df["owner_function"] == owner]
    df = df.sort_values("priority", ascending=False).head(limit)
    return [{k: _coerce(v) for k, v in row.items()} for row in df.to_dict(orient="records")]


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
def get_brief(region_id: str):
    briefs_dir = PROC / "briefs"
    files = sorted(briefs_dir.glob(f"brief_{region_id}_*.json"))
    if not files:
        raise HTTPException(status_code=404, detail="brief not found")
    with open(files[-1], encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/v1/briefs/weekly/generate",
          dependencies=[Depends(require_permission("generate_brief"))])
def generate_brief(region_id: str = Query(...)):
    import subprocess
    PY = ROOT / ".venv" / "bin" / "python"
    SRC = ROOT / "src"
    res = subprocess.run([str(PY), str(SRC / "briefs.py")],
                         check=False, cwd=str(SRC))
    if res.returncode != 0:
        raise HTTPException(status_code=500, detail="brief regeneration failed")
    audit("brief_generate", "api", region_id)
    return get_brief(region_id)


@app.get("/api/v1/replay/{incident_id}")
def replay(incident_id: str):
    return get_incident(incident_id)


@app.get("/api/v1/metrics")
def metrics():
    for p in [ROOT / "data" / "evaluation" / "reports" / "evaluation_report.json",
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


@app.post("/api/v1/demo/reset",
          dependencies=[Depends(require_permission("reset"))])
def reset():
    import subprocess
    PY = ROOT / ".venv" / "bin" / "python"
    SRC = ROOT / "src"
    res = subprocess.run([str(PY), str(SRC / "run_pipeline.py")],
                         check=False, cwd=str(SRC))
    if res.returncode != 0:
        raise HTTPException(status_code=500, detail="pipeline reset failed")
    audit("demo_reset", "api", "pipeline rebuilt")
    return {"status": "reset_ok", "message": "pipeline rebuilt from seed"}


@app.get("/api/v1/me")
def whoami(x_api_key: str | None = Header(default=None)):
    role = resolve_role(x_api_key) or "anonymous"
    return {"role": role}

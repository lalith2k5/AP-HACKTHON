"""StoreSignal AI - read-only artifact accessors for the UI."""
from __future__ import annotations

import json

import pandas as pd

from storesignal import settings as S

PROC = S.DATA_DIR / "processed"
REF = S.DATA_DIR / "reference"
REPORTS = S.DATA_DIR / "evaluation" / "reports"


def _read_parquet(name: str) -> pd.DataFrame | None:
    p = PROC / name
    if not p.exists():
        return None
    try:
        return pd.read_parquet(p)
    except Exception:
        return None


def _read_json(name: str) -> dict | None:
    p = PROC / name
    if not p.exists():
        return None
    return json.loads(p.read_text())


def predictions() -> pd.DataFrame | None:
    return _read_parquet("predictions.parquet")


def incidents() -> pd.DataFrame | None:
    return _read_parquet("incidents.parquet")


def alerts() -> pd.DataFrame | None:
    return _read_parquet("alerts.parquet")


def escalations() -> pd.DataFrame | None:
    return _read_parquet("escalations.parquet")


def radar() -> pd.DataFrame | None:
    return _read_parquet("radar_flags.parquet")


def forecasts() -> pd.DataFrame | None:
    return _read_parquet("forecasts.parquet")


def routing() -> pd.DataFrame | None:
    return _read_parquet("routing.parquet")


def regions() -> list[str]:
    p = REF / "store_master.csv"
    if not p.exists():
        return ["HYD", "BLR", "MUM"]
    df = pd.read_csv(p)
    if "region_id" in df.columns:
        return sorted(df["region_id"].dropna().unique().tolist())
    return ["ALL"]


def evaluation_report() -> dict | None:
    p = REPORTS / "evaluation_report.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def audit_log() -> pd.DataFrame | None:
    p = PROC / "audit.log"
    if not p.exists():
        return None
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return pd.DataFrame(rows) if rows else None


def overview_metrics() -> dict:
    p = predictions()
    inc = incidents()
    alerts_df = alerts()
    esc = escalations()
    total = 0 if p is None else len(p)
    open_inc = 0 if inc is None else len(inc)
    mandatory_open = 0
    if alerts_df is not None and "trigger_type" in alerts_df.columns:
        mandatory_open = int((alerts_df["trigger_type"] == "mandatory_policy").sum())
    resolved_this_week = 0
    avg_resolution = "—"
    if esc is not None and "actionable" in esc.columns:
        resolved_this_week = int((esc["actionable"] == False).sum()) if False else 0
    return {
        "total": total,
        "open_incidents": open_inc,
        "mandatory_open": mandatory_open,
        "resolved_this_week": resolved_this_week,
        "avg_resolution": avg_resolution,
    }


def feedback_series() -> pd.DataFrame | None:
    p = predictions()
    if p is None or "timestamp" not in p.columns:
        return None
    df = p.copy()
    df["date"] = pd.to_datetime(df["timestamp"], errors="coerce").dt.date
    agg = df.groupby("date").size().reset_index(name="count")
    return agg.tail(60)


def category_distribution() -> pd.DataFrame | None:
    p = predictions()
    if p is None or "predicted_category" not in p.columns:
        return None
    agg = (p.groupby("predicted_category").size()
             .reset_index(name="count")
             .sort_values("count", ascending=False).head(12))
    return agg


def action_recommendations(incident_id: str) -> list[dict]:
    """Deterministic recommendation playbook keyed off the incident category."""
    inc = incidents()
    if inc is None or inc.empty or "incident_id" not in inc.columns:
        return []
    rows = inc[inc["incident_id"].astype(str) == incident_id]
    if rows.empty:
        return []
    row = rows.iloc[0]
    cat = str(row.get("category", row.get("predicted_category", "unknown")))
    sev = str(row.get("severity", "medium")).lower()
    urgency = {"critical": "critical", "high": "high",
               "medium": "medium", "low": "low"}.get(sev, "medium")
    playbook = {
        "refrigeration_equipment": [
            ("Inspect freezer immediately", "Store Ops", "2-4 hrs",
             "Prevent food-safety risk"),
            ("Escalate to maintenance team", "Maintenance", "4-8 hrs",
             "Restore cold chain"),
        ],
        "availability_stockout": [
            ("Trigger replenishment order", "Supply Chain", "1-2 hrs",
             "Recover lost sales"),
            ("Audit planogram compliance", "Merchandising", "2-3 hrs",
             "Prevent repeat"),
        ],
        "allergen_risk": [
            ("Verify allergen labeling on shelf", "Food Safety", "1 hr",
             "Prevent regulatory exposure"),
            ("Remove ambiguous product", "Store Ops", "30 min",
             "Immediate safety"),
        ],
        "staff_conduct_misconduct": [
            ("Log restricted case with HR", "HR", "1 hr",
             "Compliance"),
            ("Preserve evidence record", "HR", "30 min",
             "Due process"),
        ],
        "food_safety_or_hygiene": [
            ("Hygiene sweep and log", "Store Ops", "2-4 hrs",
             "Prevent safety incident"),
            ("Review CCTV segment", "Store Ops", "1 hr",
             "Confirm conditions"),
        ],
    }
    default = [
        ("Acknowledge and triage", "Store Ops", "1 hr", "Reduce MTTR"),
        ("Assign owner with SLA", "Store Ops", "30 min", "Accountability"),
    ]
    actions = playbook.get(cat, default)
    return [
        {"action": a, "owner": o, "effort": e, "benefit": b, "urgency": urgency}
        for a, o, e, b in actions
    ]

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


def overview_metrics(region: str = "ALL") -> dict:
    p = filter_by_region(predictions(), region)
    inc = filter_by_region(incidents(), region)
    alerts_df = filter_by_region(alerts(), region)
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
             .reset_index()
             .rename(columns={"predicted_category": "category"})
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
    cat = str(row.get("predicted_category", row.get("category", "unknown")))
    sev = str(row.get("severity", "medium")).lower()
    urgency = {"critical": "critical", "high": "high",
               "medium": "medium", "low": "low"}.get(sev, "medium")
    playbook = {
        "allergen_or_labeling": [
            ("Verify allergen labeling on shelf", "Food Safety", "1 hr",
             "Prevent regulatory exposure"),
            ("Pull ambiguous SKU from shelf", "Store Ops", "30 min",
             "Immediate safety"),
        ],
        "food_safety_or_hygiene": [
            ("Hygiene sweep and log", "Store Ops", "2-4 hrs",
             "Prevent safety incident"),
            ("Review CCTV segment", "Store Ops", "1 hr",
             "Confirm conditions"),
        ],
        "safety_hazard": [
            ("Close off hazard area", "Store Ops", "Immediate",
             "Prevent injury"),
            ("File safety incident report", "Store Ops", "1 hr",
             "Compliance"),
        ],
        "equipment_or_refrigeration": [
            ("Inspect freezer / fridge", "Maintenance", "2-4 hrs",
             "Protect cold chain"),
            ("Escalate to maintenance team", "Maintenance", "4-8 hrs",
             "Restore equipment"),
        ],
        "cold_chain_integrity": [
            ("Verify temperature log", "Store Ops", "1 hr",
             "Prevent spoilage"),
            ("Quarantine suspect stock", "Store Ops", "1 hr",
             "Safety"),
        ],
        "expired_or_near_expiry": [
            ("Sweep shelf for expired SKUs", "Store Ops", "2 hrs",
             "Prevent sale of expired stock"),
        ],
        "out_of_stock": [
            ("Trigger replenishment order", "Supply Chain", "1-2 hrs",
             "Recover lost sales"),
            ("Audit planogram compliance", "Merchandising", "2-3 hrs",
             "Prevent repeat"),
        ],
        "stock_shortage_or_allocation": [
            ("Reallocate stock from nearby store", "Supply Chain", "4 hrs",
             "Restore availability"),
        ],
        "pricing_or_price_tag_error": [
            ("Audit price tags vs POS", "Merchandising", "2 hrs",
             "Prevent billing disputes"),
            ("Correct shelf labeling", "Store Ops", "1 hr",
             "Customer trust"),
        ],
        "promotion_or_offer_issue": [
            ("Verify promo setup in POS", "Merchandising", "1 hr",
             "Honor advertised offer"),
        ],
        "queue_or_wait_time": [
            ("Open additional checkout lane", "Store Ops", "30 min",
             "Reduce wait time"),
            ("Review staffing roster", "Store Ops", "1 hr",
             "Recurring fix"),
        ],
        "checkout_experience": [
            ("Review POS performance logs", "Digital", "2 hrs",
             "Fix systemic issues"),
        ],
        "store_cleanliness": [
            ("Deep clean affected area", "Store Ops", "2 hrs",
             "Customer experience"),
        ],
        "restroom_condition": [
            ("Restroom inspection + cleaning", "Store Ops", "1 hr",
             "Hygiene"),
        ],
        "staff_misconduct": [
            ("Log restricted case with HR", "HR", "1 hr", "Compliance"),
            ("Preserve evidence record", "HR", "30 min", "Due process"),
        ],
        "staff_conduct": [
            ("Log case with HR", "HR", "1 hr", "Compliance"),
        ],
        "billing_staff_behaviour": [
            ("Review transaction + staff statement", "Store Ops", "2 hrs",
             "Resolve dispute"),
        ],
        "delivery_or_receiving": [
            ("Audit receiving log", "Supply Chain", "2 hrs",
             "Prevent recurrence"),
        ],
        "online_order_fulfillment": [
            ("Review picking workflow", "Digital", "2 hrs",
             "Reduce errors"),
        ],
        "app_crash_or_bug": [
            ("File bug ticket with app team", "Digital", "1 hr",
             "Ship fix"),
        ],
        "app_payment_issue": [
            ("Escalate payment gateway issue", "Digital", "2 hrs",
             "Restore revenue"),
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


CITY_PREFIX_COORDS = {
    "DEL": (28.6139, 77.2090),
    "BOM": (19.0760, 72.8777),
    "MUM": (19.0760, 72.8777),
    "HYD": (17.3850, 78.4867),
    "BLR": (12.9716, 77.5946),
    "MAA": (13.0827, 80.2707),
    "CHN": (13.0827, 80.2707),
    "CCU": (22.5726, 88.3639),
    "KOL": (22.5726, 88.3639),
    "PUN": (18.5204, 73.8567),
    "PNQ": (18.5204, 73.8567),
    "AMD": (23.0225, 72.5714),
    "JAI": (26.9124, 75.7873),
    "LKO": (26.8467, 80.9462),
    "KOC": (9.9312, 76.2673),
}


def store_coords() -> dict:
    """store_id -> (lat, lon), derived from the S-XXX-NNN prefix."""
    p = REF / "store_master.csv"
    if not p.exists():
        return {}
    df = pd.read_csv(p)
    out = {}
    for sid in df["store_id"].astype(str):
        parts = sid.split("-")
        if len(parts) >= 2 and parts[1] in CITY_PREFIX_COORDS:
            out[sid] = CITY_PREFIX_COORDS[parts[1]]
    return out



def _region_store_ids(region_id: str) -> set[str]:
    p = REF / "store_master.csv"
    if not p.exists():
        return set()
    df = pd.read_csv(p)
    if "region_id" not in df.columns or "store_id" not in df.columns:
        return set()
    return set(df[df["region_id"] == region_id]["store_id"].astype(str).tolist())


def filter_by_region(df, region_id: str):
    if df is None or region_id in (None, "ALL", ""):
        return df
    ids = _region_store_ids(region_id)
    if not ids or "store_id" not in df.columns:
        return df
    return df[df["store_id"].astype(str).isin(ids)]


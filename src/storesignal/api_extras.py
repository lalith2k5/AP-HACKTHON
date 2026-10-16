"""
StoreSignal AI - spec 14.2 extra read endpoints
================================================
APIRouter for /api/v1/stores, /api/v1/stores/{id}, /api/v1/trends,
/api/v1/audit. Mounted by api.py so the main module stays readable.

All routes inherit the global auth middleware. Per-route permission
checks use require_permission (security.py) via module-level singletons
to stay ruff B008-clean.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from storesignal.paths import PROCESSED_DIR, REFERENCE_DIR
from storesignal.security import require_permission

router = APIRouter(prefix="/api/v1", tags=["extras"])

_perm_read_overview = require_permission("read_overview")
_perm_read_trends = require_permission("read_trends")


def _read_parquet(name: str) -> pd.DataFrame:
    p = PROCESSED_DIR / name
    if not p.exists():
        raise HTTPException(status_code=503, detail=f"artifact not built: {name}")
    return pd.read_parquet(p, engine="pyarrow")


def _read_reference_csv(name: str) -> pd.DataFrame | None:
    p = REFERENCE_DIR / name
    if not p.exists():
        return None
    return pd.read_csv(p, dtype=str)


def _maybe_int(v: Any) -> int | None:
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        return int(float(v))
    except Exception:
        return None


def _region_of(store_id: str | None) -> str | None:
    if not isinstance(store_id, str):
        return None
    parts = store_id.split("-")
    return parts[1] if len(parts) >= 2 else None


@router.get("/stores")
def list_stores(_perm=Depends(_perm_read_overview)):  # noqa: B008
    """Ranked store list. Raw counts + denominator availability."""
    stores = _read_reference_csv("store_master.csv")
    if stores is None:
        raise HTTPException(status_code=503,
                            detail="store_master.csv missing in data/reference/")
    inc = _read_parquet("incidents.parquet")
    al = _read_parquet("alerts.parquet")

    inc_counts = inc.groupby("store_id").size().to_dict() if len(inc) else {}
    al_counts = al.groupby("store_id").size().to_dict() if len(al) else {}

    rows: list[dict] = []
    for _, s in stores.iterrows():
        sid = s.get("store_id")
        if not isinstance(sid, str):
            continue
        rows.append({
            "store_id": sid,
            "store_name": s.get("store_name"),
            "region_id": s.get("region_id") or _region_of(sid),
            "city": s.get("city"),
            "store_format": s.get("store_format"),
            "weekly_footfall": _maybe_int(s.get("weekly_footfall")),
            "has_denominator": s.get("weekly_footfall") is not None
                               and not pd.isna(s.get("weekly_footfall")),
            "incident_count": int(inc_counts.get(sid, 0)),
            "alert_count": int(al_counts.get(sid, 0)),
        })

    rows.sort(key=lambda r: (-r["incident_count"], r["store_id"]))
    return {"stores": rows, "count": len(rows)}


@router.get("/stores/{store_id}")
def store_detail(store_id: str, _perm=Depends(_perm_read_overview)):  # noqa: B008
    stores = _read_reference_csv("store_master.csv")
    if stores is None:
        raise HTTPException(status_code=503, detail="store_master.csv missing")
    row = stores[stores["store_id"] == store_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"unknown store: {store_id}")
    s = row.iloc[0].to_dict()

    inc = _read_parquet("incidents.parquet")
    my_inc = inc[inc["store_id"] == store_id] if len(inc) else inc
    cols = [c for c in [
        "incident_id", "predicted_category", "severity", "owner_function",
        "first_seen", "last_seen", "record_count", "verification_status",
    ] if c in my_inc.columns]

    return {
        "store": {
            "store_id": s.get("store_id"),
            "store_name": s.get("store_name"),
            "region_id": s.get("region_id") or _region_of(store_id),
            "city": s.get("city"),
            "store_format": s.get("store_format"),
            "weekly_footfall": _maybe_int(s.get("weekly_footfall")),
        },
        "incidents": my_inc[cols].head(50).to_dict(orient="records"),
        "incident_count": int(len(my_inc)),
    }


@router.get("/trends")
def trends(
    region_id: str | None = Query(default=None),
    category: str | None = Query(default=None),
    from_ts: str | None = Query(default=None, alias="from"),
    to_ts: str | None = Query(default=None, alias="to"),
    _perm=Depends(_perm_read_trends),  # noqa: B008
):
    """Baseline vs current trend series from predictions.parquet +
    flagged anomalies from radar_flags.parquet."""
    preds = _read_parquet("predictions.parquet")
    if "timestamp" in preds.columns:
        preds = preds.copy()
        preds["timestamp"] = pd.to_datetime(preds["timestamp"],
                                            errors="coerce", utc=True)

    if region_id:
        preds = preds[preds["store_id"].astype(str).str.contains(
            f"-{region_id}-", na=False, regex=False)]
    if category:
        preds = preds[preds["predicted_category"] == category]
    if from_ts:
        preds = preds[preds["timestamp"] >= pd.to_datetime(from_ts, utc=True)]
    if to_ts:
        preds = preds[preds["timestamp"] <= pd.to_datetime(to_ts, utc=True)]

    if len(preds):
        preds = preds.assign(day=preds["timestamp"].dt.date.astype(str))
        series = (
            preds.groupby(["day", "predicted_category"], dropna=False)
            .size().reset_index(name="count")
        )
    else:
        series = pd.DataFrame(columns=["day", "predicted_category", "count"])

    anomalies: list[dict] = []
    radar_path = PROCESSED_DIR / "radar_flags.parquet"
    if radar_path.exists():
        radar = pd.read_parquet(radar_path, engine="pyarrow")
        if region_id and "store_id" in radar.columns:
            radar = radar[radar["store_id"].astype(str).str.contains(
                f"-{region_id}-", na=False, regex=False)]
        if category and "predicted_category" in radar.columns:
            radar = radar[radar["predicted_category"] == category]
        anomalies = radar.head(200).to_dict(orient="records")

    return {
        "filters": {"region_id": region_id, "category": category,
                    "from": from_ts, "to": to_ts},
        "series": series.to_dict(orient="records"),
        "anomalies": anomalies,
        "count": len(series),
    }


@router.get("/audit")
def audit_events(
    object_id: str | None = Query(default=None),
    actor: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
    _perm=Depends(_perm_read_overview),  # noqa: B008
):
    """Append-only audit event list. Reads data/processed/audit.log (JSONL).
    Filters are best-effort; unknown keys on events are passed through."""
    log_path = PROCESSED_DIR / "audit.log"
    if not log_path.exists():
        return {"events": [], "count": 0, "note": "audit.log not present"}

    events: list[dict] = []
    with log_path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                e = json.loads(raw)
            except Exception:
                continue
            if object_id and e.get("object_id") != object_id:
                continue
            if event_type and e.get("event_type") != event_type:
                continue
            if actor:
                a = e.get("actor") or e.get("actor_id")
                if a != actor:
                    continue
            events.append(e)

    events = events[-limit:]
    events.reverse()
    return {"events": events, "count": len(events)}

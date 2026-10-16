"""
StoreSignal AI — Action & Resolution Tracking (P2 stretch)
==========================================================
Append-only JSONL log of every review/assign/action/resolve event.
Provides a queryable summary of alert lifecycle.
"""

import json
import time
import uuid
from pathlib import Path

ROOT = Path.home() / "storesignal-ai"
LOG = ROOT / "data" / "processed" / "actions.jsonl"
LOG.parent.mkdir(parents=True, exist_ok=True)
REPORT = ROOT / "data" / "processed" / "tracking_report.json"

VALID_EVENTS = {"review", "assign", "action", "resolve", "escalate"}


def _append(record: dict):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def record_event(event_type: str, alert_id: str, actor: str,
                 note: str = "", status: str = "") -> dict:
    if event_type not in VALID_EVENTS:
        raise ValueError(f"invalid event_type: {event_type}")
    rec = {
        "event_id": f"EV-{uuid.uuid4().hex[:10]}",
        "event_type": event_type,
        "alert_id": alert_id,
        "actor": actor,
        "note": note,
        "status": status or event_type,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _append(rec)
    return rec


def read_events() -> list:
    if not LOG.exists():
        return []
    out = []
    with open(LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def summarize() -> dict:
    events = read_events()
    by_type: dict[str, int] = {}
    by_alert: dict[str, int] = {}
    for e in events:
        by_type[e["event_type"]] = by_type.get(e["event_type"], 0) + 1
        by_alert[e["alert_id"]] = by_alert.get(e["alert_id"], 0) + 1
    return {
        "total_events": len(events),
        "by_type": by_type,
        "distinct_alerts": len(by_alert),
        "log_path": str(LOG),
    }


if __name__ == "__main__":
    # Write a demo lifecycle
    record_event("review", "AL-POL-demo0001", "reviewer@ops", "initial triage")
    record_event("assign", "AL-POL-demo0001", "manager@ops", "assigned to S-MUM-003")
    record_event("action", "AL-POL-demo0001", "store@ops", "freezer repair dispatched")
    record_event("resolve", "AL-POL-demo0001", "manager@ops", "confirmed fixed")
    summary = summarize()
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))

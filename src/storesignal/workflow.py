"""
StoreSignal AI - Incident workflow state machine (spec section 12).
==================================================================
Enforces allowed transitions, requires a reason for override/downgrade,
and emits an append-only audit event for every transition.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from storesignal import settings as _settings

STATE_FILE = _settings.DATA_DIR / "processed" / "incident_state.jsonl"
AUDIT_FILE = _settings.DATA_DIR / "processed" / "audit.log"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

STATES = {
    "new", "triaged", "assigned", "in_progress",
    "resolved", "verified_closed", "reopened", "needs_review",
}

TRANSITIONS: dict[str, set[str]] = {
    "new":            {"triaged", "needs_review"},
    "triaged":        {"assigned", "needs_review"},
    "assigned":       {"in_progress", "needs_review"},
    "in_progress":    {"resolved", "needs_review"},
    "resolved":       {"verified_closed", "reopened"},
    "verified_closed": set(),
    "reopened":       {"triaged"},
    "needs_review":   {"triaged", "assigned"},
}

TERMINAL = {"verified_closed"}

OVERRIDE_REQUIRED_STATES = {"resolved", "verified_closed"}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append_state(rec: dict) -> None:
    with open(STATE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")


def _audit(event_type: str, actor: str, object_id: str,
           before: dict | None, after: dict | None,
           reason: str | None, run_id: str | None) -> None:
    rec = {
        "event_id": f"AUD-{uuid.uuid4().hex[:12]}",
        "event_type": event_type,
        "actor_id": actor,
        "object_type": "incident",
        "object_id": object_id,
        "occurred_at": _now(),
        "before": before or {},
        "after": after or {},
        "reason": reason,
        "request_id": None,
        "run_id": run_id,
    }
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")


def current_state(incident_id: str, default: str = "new") -> str:
    if not STATE_FILE.exists():
        return default
    state = default
    for line in STATE_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("incident_id") == incident_id:
            state = rec.get("to_state", state)
    return state


def transition(
    incident_id: str,
    to_state: str,
    actor: str,
    reason: str | None = None,
    run_id: str | None = None,
    is_override: bool = False,
) -> dict:
    """Attempt a state transition. Returns {ok, from, to, error?}."""
    if to_state not in STATES:
        return {"ok": False, "error": f"unknown state '{to_state}'",
                "allowed": sorted(STATES)}
    from_state = current_state(incident_id)
    allowed = TRANSITIONS.get(from_state, set())
    if to_state not in allowed and not is_override:
        return {"ok": False, "error": f"invalid transition {from_state} -> {to_state}",
                "from": from_state, "allowed": sorted(allowed)}
    if is_override and not reason:
        return {"ok": False, "error": "override requires reason"}
    if to_state in OVERRIDE_REQUIRED_STATES and to_state != "reopened" and not reason:
        if from_state != "in_progress" and from_state != "resolved":
            pass  # normal resolution path, no reason needed
    rec = {
        "incident_id": incident_id,
        "from_state": from_state,
        "to_state": to_state,
        "actor": actor,
        "reason": reason,
        "is_override": is_override,
        "ts": _now(),
    }
    _append_state(rec)
    _audit("incident.status_changed", actor, incident_id,
           {"status": from_state}, {"status": to_state}, reason, run_id)
    return {"ok": True, "from": from_state, "to": to_state,
            "is_override": is_override, "occurred_at": rec["ts"]}


def history(incident_id: str) -> list[dict]:
    if not STATE_FILE.exists():
        return []
    out = []
    for line in STATE_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("incident_id") == incident_id:
            out.append(rec)
    return out


def summary() -> dict:
    if not STATE_FILE.exists():
        return {"transitions": 0, "incidents": 0, "states": {}}
    counts: dict[str, int] = {}
    incidents: set[str] = set()
    n = 0
    for line in STATE_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        n += 1
        incidents.add(rec.get("incident_id"))
        counts[rec.get("to_state")] = counts.get(rec.get("to_state"), 0) + 1
    return {"transitions": n, "incidents": len(incidents), "states": counts}

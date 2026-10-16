"""One-shot migration: JSONL -> SQLite.

Safe to re-run; skips rows already present (by ts+id+field).

Usage:
    .venv/bin/python scripts/migrate_state.py
"""
import json
from pathlib import Path

from storesignal.paths import PROCESSED_DIR
from storesignal import state


def _read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    out = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def migrate_incident_overrides():
    rows = _read_jsonl(PROCESSED_DIR / "incident_overrides.jsonl")
    n = 0
    for r in rows:
        state.append_incident_override(
            r.get("incident_id", ""),
            r.get("field", ""),
            r.get("value"),
            r.get("actor", "migrated"),
            r.get("reason"),
        )
        n += 1
    return n


def migrate_alert_overrides():
    rows = _read_jsonl(PROCESSED_DIR / "alert_overrides.jsonl")
    n = 0
    for r in rows:
        state.append_alert_override(
            r.get("alert_id", ""),
            r.get("field", ""),
            r.get("value"),
            r.get("actor", "migrated"),
            r.get("note"),
            r.get("decision"),
        )
        n += 1
    return n


def migrate_notes():
    rows = _read_jsonl(PROCESSED_DIR / "incident_notes.jsonl")
    n = 0
    for r in rows:
        state.add_note(r.get("incident_id", ""),
                       r.get("actor", "migrated"),
                       r.get("note", ""))
        n += 1
    return n


if __name__ == "__main__":
    state.init_db()
    print("incident overrides migrated:", migrate_incident_overrides())
    print("alert overrides migrated:   ", migrate_alert_overrides())
    print("notes migrated:             ", migrate_notes())
    print("db path:", state.DB_PATH)

"""SQLite-backed transactional state store.

Replaces append-only JSONL files for incident overrides, alert overrides,
and notes. Benefits:
  - Atomic writes (crash-safe)
  - Indexed lookups (no full-file scan)
  - Concurrent reads during writes (WAL mode)
  - Schema enforcement + UNIQUE constraints

Migration: scripts/migrate_state.py imports legacy JSONL on first run.
"""
from __future__ import annotations

import json
import sqlite3
import time
from typing import Any

from storesignal.paths import PROCESSED_DIR

DB_PATH = PROCESSED_DIR / "storesignal.db"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS incident_overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT NOT NULL,
    field TEXT NOT NULL,
    value TEXT NOT NULL,
    ts TEXT NOT NULL,
    actor TEXT NOT NULL,
    reason TEXT
);
CREATE INDEX IF NOT EXISTS idx_inc_ovr
    ON incident_overrides(incident_id, field, ts DESC);

CREATE TABLE IF NOT EXISTS alert_overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id TEXT NOT NULL,
    field TEXT NOT NULL,
    value TEXT NOT NULL,
    ts TEXT NOT NULL,
    actor TEXT NOT NULL,
    note TEXT,
    decision TEXT
);
CREATE INDEX IF NOT EXISTS idx_alert_ovr
    ON alert_overrides(alert_id, field, ts DESC);

CREATE TABLE IF NOT EXISTS incident_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    actor TEXT NOT NULL,
    note TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_inc_notes
    ON incident_notes(incident_id, ts);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    detail TEXT,
    extra TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_events(ts DESC);
"""


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _conn() -> sqlite3.Connection:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB_PATH), timeout=10.0)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init_db() -> None:
    with _conn() as c:
        c.executescript(SCHEMA)


def append_incident_override(
    incident_id: str, field: str, value: Any,
    actor: str, reason: str | None = None,
) -> str:
    ts = _now()
    with _conn() as c:
        c.execute(
            "INSERT INTO incident_overrides"
            " (incident_id, field, value, ts, actor, reason)"
            " VALUES (?,?,?,?,?,?)",
            (incident_id, field, json.dumps(value), ts, actor, reason),
        )
    return ts


def latest_incident_overrides(incident_id: str) -> dict:
    with _conn() as c:
        rows = c.execute(
            """SELECT field, value FROM incident_overrides o
               WHERE incident_id = ?
                 AND ts = (SELECT MAX(ts) FROM incident_overrides
                            WHERE incident_id = o.incident_id AND field = o.field)""",
            (incident_id,),
        ).fetchall()
    return {r["field"]: json.loads(r["value"]) for r in rows}


def incident_override_history(incident_id: str) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT ts, field, value, actor, reason FROM incident_overrides"
            " WHERE incident_id = ? ORDER BY ts",
            (incident_id,),
        ).fetchall()
    return [
        {"ts": r["ts"], "kind": "override",
         "label": f"{r['field']} -> {json.loads(r['value'])}",
         "actor": r["actor"], "reason": r["reason"]}
        for r in rows
    ]


def append_alert_override(
    alert_id: str, field: str, value: Any, actor: str,
    note: str | None = None, decision: str | None = None,
) -> str:
    ts = _now()
    with _conn() as c:
        c.execute(
            "INSERT INTO alert_overrides"
            " (alert_id, field, value, ts, actor, note, decision)"
            " VALUES (?,?,?,?,?,?,?)",
            (alert_id, field, json.dumps(value), ts, actor, note, decision),
        )
    return ts


def latest_alert_overrides(alert_id: str) -> dict:
    with _conn() as c:
        rows = c.execute(
            """SELECT field, value FROM alert_overrides o
               WHERE alert_id = ?
                 AND ts = (SELECT MAX(ts) FROM alert_overrides
                            WHERE alert_id = o.alert_id AND field = o.field)""",
            (alert_id,),
        ).fetchall()
    return {r["field"]: json.loads(r["value"]) for r in rows}


def add_note(incident_id: str, actor: str, note: str) -> dict:
    ts = _now()
    with _conn() as c:
        c.execute(
            "INSERT INTO incident_notes (incident_id, ts, actor, note)"
            " VALUES (?,?,?,?)",
            (incident_id, ts, actor, note),
        )
    return {"incident_id": incident_id, "ts": ts, "actor": actor, "note": note}


def notes_for(incident_id: str) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT ts, actor, note FROM incident_notes"
            " WHERE incident_id = ? ORDER BY ts",
            (incident_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def clear_all_state() -> dict:
    with _conn() as c:
        c.execute("DELETE FROM incident_overrides")
        c.execute("DELETE FROM alert_overrides")
        c.execute("DELETE FROM incident_notes")
    return {"cleared": ["incident_overrides", "alert_overrides", "incident_notes"]}


# Ensure schema on import.
init_db()


def record_audit(event_type: str, actor: str, detail: str = "", extra: dict | None = None) -> None:
    """Append an audit event to the SQLite audit_events table.
    This mirrors the JSONL audit log so both trails stay in sync."""
    import json as _json
    conn = _conn()
    conn.execute(
        """
        INSERT INTO audit_events (ts, event_type, actor, detail, extra_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            _now(),
            event_type,
            actor,
            detail,
            _json.dumps(extra or {}),
        ),
    )
    conn.commit()

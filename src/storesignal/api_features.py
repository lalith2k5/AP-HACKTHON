"""
StoreSignal AI - spec-completeness endpoints
=============================================
Covers the remaining spec surfaces:
- File upload + preview + validate + commit (spec 2.2, 7.x)
- Merge/split incidents (spec 11.3)
- Flag wrong label (spec 8.4)
- Exports: incidents CSV, audit CSV, brief PDF (spec 13.2, 14.2)
- Store impact map with coordinates (spec 3.2)

All routes inherit the global auth middleware. Mutations are audit-logged.
"""
from __future__ import annotations

import io
import json
import time
import uuid
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse, StreamingResponse

from storesignal.paths import PROCESSED_DIR, REFERENCE_DIR
from storesignal.security import audit, require_permission

router = APIRouter(prefix="/api/v1", tags=["features"])

_perm_read = require_permission("read_overview")
_perm_run = require_permission("read_overview")

UPLOAD_DIR = PROCESSED_DIR / "imports" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

_FLAG_LOG = PROCESSED_DIR / "label_flags.jsonl"
_MERGE_LOG = PROCESSED_DIR / "incident_merges.jsonl"


def _read_parquet(name: str) -> pd.DataFrame:
    p = PROCESSED_DIR / name
    if not p.exists():
        raise HTTPException(status_code=503, detail=f"artifact not built: {name}")
    return pd.read_parquet(p, engine="pyarrow")


# ---------------------------------------------------------------------------
# IMPORT - file upload + preview + validate + commit
# ---------------------------------------------------------------------------

@router.post("/import/upload")
async def import_upload(file: UploadFile = File(...), _p=Depends(_perm_run)):  # noqa: B008
    """Accept an uploaded file. Saves to a temp upload dir and returns an id."""
    if not file.filename:
        raise HTTPException(status_code=422, detail="filename required")
    ext = Path(file.filename).suffix.lower()
    if ext not in {".csv", ".jsonl", ".ndjson", ".parquet", ".pq"}:
        raise HTTPException(status_code=422,
                            detail=f"unsupported format: {ext}. Use CSV, JSONL, or Parquet.")

    upload_id = f"UP-{uuid.uuid4().hex[:10]}"
    dest = UPLOAD_DIR / f"{upload_id}{ext}"

    # Save with a hard size cap (spec 18: bounded uploads)
    MAX_BYTES = 100 * 1024 * 1024
    total = 0
    with dest.open("wb") as fh:
        while True:
            chunk = await file.read(1 << 20)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_BYTES:
                fh.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="upload too large (max 100MB)")
            fh.write(chunk)

    meta = {
        "upload_id": upload_id,
        "filename": file.filename,
        "size_bytes": total,
        "path": str(dest.relative_to(PROCESSED_DIR.parent.parent)) if False else str(dest),
    }
    (UPLOAD_DIR / f"{upload_id}.json").write_text(json.dumps(meta))
    audit("import_uploaded", "operator", f"upload_id={upload_id} bytes={total}")
    return meta


@router.get("/import/upload/{upload_id}/preview")
def import_preview(upload_id: str, n: int = Query(default=5, ge=1, le=20), _p=Depends(_perm_read)):  # noqa: B008
    """Return a safe preview of the uploaded file (first N rows + columns)."""
    from storesignal import import_wizard as iw
    meta_p = UPLOAD_DIR / f"{upload_id}.json"
    if not meta_p.exists():
        raise HTTPException(status_code=404, detail=f"unknown upload: {upload_id}")
    meta = json.loads(meta_p.read_text())
    src = Path(meta["path"])
    if not src.exists():
        raise HTTPException(status_code=410, detail="upload file gone")

    fmt = iw._detect_format(str(src))
    if fmt == "csv":
        df = pd.read_csv(src, dtype=str, keep_default_na=False, nrows=n)
        full_cols = list(pd.read_csv(src, dtype=str, keep_default_na=False, nrows=0).columns)
    elif fmt == "jsonl":
        rows = []
        with src.open() as fh:
            for i, line in enumerate(fh):
                if i >= n:
                    break
                rows.append(json.loads(line))
        df = pd.DataFrame(rows)
        full_cols = list(df.columns)
    elif fmt == "parquet":
        df = pd.read_parquet(src, engine="pyarrow")
        full_cols = list(df.columns)
        df = df.head(n)
    else:
        raise HTTPException(status_code=422, detail=f"unsupported format: {fmt}")

    return {
        "upload_id": upload_id,
        "filename": meta["filename"],
        "format": fmt,
        "columns": full_cols,
        "preview": df.astype(str).to_dict(orient="records"),
        "suggested_mapping": {c: c for c in full_cols if c in iw.CANONICAL_COLUMNS},
    }


@router.post("/import/validate")
def import_validate(payload: dict = Body(default={}), _p=Depends(_perm_run)):  # noqa: B008
    """Check that a mapping covers the required columns."""
    from storesignal import import_wizard as iw
    columns = payload.get("columns") or []
    mapping = payload.get("mapping") or {}
    errors = iw.validate_mapping(columns, mapping)
    missing_required = [c for c in iw.REQUIRED_COLUMNS
                        if c not in mapping.values()]
    return {
        "ok": len(errors) == 0 and len(missing_required) == 0,
        "errors": errors,
        "missing_required": missing_required,
        "required_columns": iw.REQUIRED_COLUMNS,
    }


@router.post("/import/commit")
def import_commit(payload: dict = Body(default={}), _p=Depends(_perm_run)):  # noqa: B008
    """Run the import with the given mapping. Returns a batch id."""
    from storesignal import import_wizard as iw
    upload_id = payload.get("upload_id")
    mapping = payload.get("mapping") or {}
    channel_override = payload.get("channel_override")
    if not upload_id:
        raise HTTPException(status_code=422, detail="upload_id required")

    meta_p = UPLOAD_DIR / f"{upload_id}.json"
    if not meta_p.exists():
        raise HTTPException(status_code=404, detail=f"unknown upload: {upload_id}")
    meta = json.loads(meta_p.read_text())
    src = Path(meta["path"])

    try:
        batch_id = iw.run_import(src, mapping, channel_override=channel_override)
    except Exception as e:
        audit("import_commit_failed", "operator", f"upload={upload_id} err={e}")
        raise HTTPException(status_code=422, detail=str(e)) from e

    audit("import_committed", "operator", f"batch={batch_id} upload={upload_id}")
    return {"batch_id": batch_id, "upload_id": upload_id,
            "process_url": "/api/v1/pipeline/run"}


@router.get("/import/batches")
def import_batches(_p=Depends(_perm_read)):  # noqa: B008
    from storesignal import import_wizard as iw
    return {"batches": iw.list_batches()}


# ---------------------------------------------------------------------------
# MERGE / SPLIT
# ---------------------------------------------------------------------------

@router.post("/incidents/merge")
def merge_incidents(payload: dict = Body(default={}), _p=Depends(_perm_run)):  # noqa: B008
    """Merge N source incidents into a target. Append-only; originals preserved."""
    target = payload.get("target_id")
    sources = payload.get("source_ids") or []
    reason = (payload.get("reason") or "").strip()
    actor = payload.get("actor") or "operator"
    if not target or not sources:
        raise HTTPException(status_code=422, detail="target_id and source_ids required")
    if len(reason) < 4:
        raise HTTPException(status_code=422, detail="reason is required (min 4 chars)")
    if target in sources:
        raise HTTPException(status_code=422, detail="target cannot be in source_ids")

    inc = _read_parquet("incidents.parquet")
    known = set(inc["incident_id"].astype(str).tolist())
    for i in [target, *sources]:
        if i not in known:
            raise HTTPException(status_code=404, detail=f"unknown incident: {i}")

    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": "merge",
        "target_id": target,
        "source_ids": sources,
        "actor": actor,
        "reason": reason,
        "merge_id": f"MG-{uuid.uuid4().hex[:10]}",
    }
    with _MERGE_LOG.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")
    audit("incident.merged", actor, f"target={target} sources={len(sources)}")
    return entry


@router.post("/incidents/{incident_id}/split")
def split_incident(incident_id: str, payload: dict = Body(default={}), _p=Depends(_perm_run)):  # noqa: B008
    """Split a subset of records out of an incident into a new incident."""
    record_ids = payload.get("record_ids") or []
    reason = (payload.get("reason") or "").strip()
    actor = payload.get("actor") or "operator"
    if not record_ids:
        raise HTTPException(status_code=422, detail="record_ids required")
    if len(reason) < 4:
        raise HTTPException(status_code=422, detail="reason is required (min 4 chars)")

    inc = _read_parquet("incidents.parquet")
    if incident_id not in set(inc["incident_id"].astype(str)):
        raise HTTPException(status_code=404, detail=f"unknown incident: {incident_id}")

    new_id = f"INC-SPLIT-{uuid.uuid4().hex[:8].upper()}"
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": "split",
        "source_incident_id": incident_id,
        "new_incident_id": new_id,
        "record_ids": record_ids,
        "actor": actor,
        "reason": reason,
        "split_id": f"SP-{uuid.uuid4().hex[:10]}",
    }
    with _MERGE_LOG.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")
    audit("incident.split", actor, f"source={incident_id} new={new_id} records={len(record_ids)}")
    return entry


@router.get("/incidents/{incident_id}/lineage")
def incident_lineage(incident_id: str, _p=Depends(_perm_read)):  # noqa: B008
    """Return any merge/split events touching this incident."""
    events: list[dict] = []
    if _MERGE_LOG.exists():
        for line in _MERGE_LOG.read_text().splitlines():
            try:
                e = json.loads(line)
            except Exception:
                continue
            if (e.get("target_id") == incident_id
                    or incident_id in (e.get("source_ids") or [])
                    or e.get("source_incident_id") == incident_id
                    or e.get("new_incident_id") == incident_id):
                events.append(e)
    return {"incident_id": incident_id, "events": events, "count": len(events)}


# ---------------------------------------------------------------------------
# FLAG WRONG LABEL (spec 8.4)
# ---------------------------------------------------------------------------

@router.post("/feedback/{record_id}/flag")
def flag_label(record_id: str, payload: dict = Body(default={}), _p=Depends(_perm_run)):  # noqa: B008
    """Reviewer flags a record's label as wrong. Stored separately from model output."""
    suggested = (payload.get("suggested_category") or "").strip()
    reason = (payload.get("reason") or "").strip()
    actor = payload.get("actor") or "reviewer"
    action = payload.get("action") or "flag"  # flag | accept | remove

    if action in ("flag", "accept") and not suggested:
        raise HTTPException(status_code=422, detail="suggested_category required")
    if action not in ("flag", "accept", "remove"):
        raise HTTPException(status_code=422, detail="invalid action")

    preds = _read_parquet("predictions.parquet")
    if record_id not in set(preds["record_id"].astype(str)):
        raise HTTPException(status_code=404, detail=f"unknown record: {record_id}")

    row = preds[preds["record_id"].astype(str) == record_id].iloc[0].to_dict()
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "record_id": record_id,
        "action": action,
        "original_category": str(row.get("predicted_category", "")),
        "original_confidence": float(row.get("confidence", 0.0)),
        "suggested_category": suggested,
        "reason": reason,
        "actor": actor,
        "flag_id": f"FL-{uuid.uuid4().hex[:10]}",
    }
    with _FLAG_LOG.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")
    audit("label.flagged", actor, f"record={record_id} action={action}")
    return entry


@router.get("/feedback/{record_id}/flags")
def label_flags_for_record(record_id: str, _p=Depends(_perm_read)):  # noqa: B008
    out = []
    if _FLAG_LOG.exists():
        for line in _FLAG_LOG.read_text().splitlines():
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("record_id") == record_id:
                out.append(e)
    return {"record_id": record_id, "flags": out, "count": len(out)}


# ---------------------------------------------------------------------------
# STORE MAP (spec 3.2 - store impact map)
# ---------------------------------------------------------------------------

@router.get("/map/stores")
def map_stores(_p=Depends(_perm_read)):  # noqa: B008
    """Store coordinates + incident counts, for the impact map."""
    ref = REFERENCE_DIR / "store_master.csv"
    if not ref.exists():
        return {"stores": [], "note": "store_master.csv missing"}
    df = pd.read_csv(ref, dtype=str)
    inc = _read_parquet("incidents.parquet")

    # Derive lat/lng from region prefix deterministically if not in the file
    REGION_COORDS = {
        "DEL": (28.6139, 77.2090),
        "MUM": (19.0760, 72.8777),
        "BLR": (12.9716, 77.5946),
        "HYD": (17.3850, 78.4867),
        "CHN": (13.0827, 80.2707),
    }

    counts = inc.groupby("store_id").size().to_dict() if len(inc) else {}
    sev_counts = (
        inc[inc["severity"].isin(["critical", "high"])].groupby("store_id").size().to_dict()
        if len(inc) else {}
    )

    import random
    out = []
    for _, s in df.iterrows():
        sid = s.get("store_id")
        if not isinstance(sid, str):
            continue
        # Derive region CODE from store_id prefix (S-DEL-001 -> DEL).
        # The store_master region_id column is "R-NORTH" style, which does
        # not map to coordinates.
        parts = sid.split("-")
        code = parts[1] if len(parts) >= 2 else None
        base = REGION_COORDS.get(code, (20.5937, 78.9629))  # fallback: India centroid
        rnd = random.Random(sid)
        lat = base[0] + rnd.uniform(-0.06, 0.06)
        lng = base[1] + rnd.uniform(-0.06, 0.06)
        out.append({
            "store_id": sid,
            "store_name": s.get("store_name"),
            "region_id": code,
            "city": s.get("city") or code,
            "lat": round(lat, 4),
            "lng": round(lng, 4),
            "incident_count": int(counts.get(sid, 0)),
            "high_severity_count": int(sev_counts.get(sid, 0)),
        })
    return {"stores": out, "count": len(out)}


# ---------------------------------------------------------------------------
# EXPORTS (spec 13.2, 14.2)
# ---------------------------------------------------------------------------

@router.get("/export/incidents.csv")
def export_incidents_csv(
    region_id: str | None = None,
    severity: str | None = None,
    _p=Depends(_perm_read),  # noqa: B008
):
    inc = _read_parquet("incidents.parquet")
    if region_id:
        inc = inc[inc["store_id"].astype(str).str.contains(f"-{region_id}-", na=False, regex=False)]
    if severity:
        inc = inc[inc["severity"] == severity]
    buf = io.StringIO()
    inc.to_csv(buf, index=False)
    return PlainTextResponse(
        buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="storesignal_incidents.csv"'},
    )


@router.get("/export/audit.csv")
def export_audit_csv(_p=Depends(_perm_read)):  # noqa: B008
    log = PROCESSED_DIR / "audit.log"
    rows = []
    if log.exists():
        for line in log.read_text().splitlines():
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["ts", "event_type", "actor", "detail"])
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return PlainTextResponse(
        buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="storesignal_audit.csv"'},
    )


@router.get("/export/brief/{region_id}.pdf")
def export_brief_pdf(region_id: str, _p=Depends(_perm_read)):  # noqa: B008
    """Generate a PDF of the weekly brief for a region (spec 13.2)."""
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError:
        raise HTTPException(status_code=503, detail="reportlab not installed") from None

    # Briefs are stored as JSON by storesignal.briefs. Find the file for
    # the region, else generate, else use any available brief.
    briefs_dir = PROCESSED_DIR / "briefs"

    def _find_brief_json(rid: str):
        if briefs_dir.exists():
            hits = sorted(briefs_dir.glob(f"brief_{rid}_*.json"))
            if hits:
                return hits[-1]
        return None

    candidates = [region_id, "R-NORTH", "R-WEST", "R-SOUTH", "R-EAST", "R-CENTRAL"]
    CODE_TO_ID = {"DEL": "R-NORTH", "MUM": "R-WEST", "BLR": "R-SOUTH",
                  "HYD": "R-SOUTH", "CHN": "R-SOUTH"}
    if region_id in CODE_TO_ID:
        candidates.insert(1, CODE_TO_ID[region_id])

    brief_path = None
    for rid in candidates:
        brief_path = _find_brief_json(rid)
        if brief_path:
            region_id = rid
            break

    if brief_path is None:
        # Generate via subprocess, then retry
        import subprocess

        from storesignal.paths import CODE_ROOT
        py = str(CODE_ROOT / ".venv" / "bin" / "python")
        try:
            subprocess.run(
                [py, "-m", "storesignal.briefs"],
                cwd=str(CODE_ROOT), check=True, timeout=60,
                capture_output=True,
            )
        except Exception as e:
            raise HTTPException(status_code=503,
                                detail=f"could not generate brief: {e}") from e
        for rid in candidates:
            brief_path = _find_brief_json(rid)
            if brief_path:
                region_id = rid
                break

    if brief_path is None:
        raise HTTPException(status_code=404, detail="no brief JSON available")

    brief = json.loads(brief_path.read_text())

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER,
                             leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                             topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    h1 = styles["Heading1"]
    h2 = styles["Heading2"]
    body = styles["BodyText"]

    story = []
    story.append(Paragraph(f"StoreSignal AI - Weekly Brief: {brief.get('region_name', region_id)}", h1))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Week: {brief.get('week_start')} to {brief.get('week_end')}", body))
    story.append(Paragraph(f"Total feedback: {brief.get('total_feedback')} (prev {brief.get('total_feedback_previous_week')})", body))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Top issues", h2))
    for t in brief.get("top_issues", [])[:5]:
        story.append(Paragraph(
            f"<b>{t.get('category','').replace('_', ' ')}</b> - "
            f"{t.get('severity','')} - trend {t.get('trend','')} - "
            f"count {t.get('current_count')} (prev {t.get('previous_count')})",
            body,
        ))
        story.append(Paragraph(f"Owner: {t.get('owner_function','')} - Rule: {t.get('escalation_rule','')}", body))
        story.append(Paragraph(f"Next: {t.get('next_action','')}", body))
        for q in (t.get("evidence_quotes") or [])[:2]:
            story.append(Paragraph(f"<i>\"{q}\"</i>", body))
        story.append(Spacer(1, 8))

    mandatory = [t for t in brief.get("top_issues", [])
                 if str(t.get("escalation_rule", "")).startswith("mandatory_policy")]
    if mandatory:
        story.append(Paragraph("Mandatory risk escalations", h2))
        for t in mandatory:
            story.append(Paragraph(
                f"{t.get('category','').replace('_',' ')} - {t.get('severity','')} - "
                f"{t.get('current_count')} signals", body))

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Unverified feedback. Not a determination of fact. "
        "See DEPLOYMENT.md for limitations.", body))

    doc.build(story)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="storesignal_brief_{region_id}.pdf"'},
    )

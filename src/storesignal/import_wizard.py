"""
StoreSignal AI - Import Wizard (spec section 7)
================================================
Accepts CSV / JSONL / Parquet, applies a user-supplied column mapping,
validates against the canonical feedback schema, emits a validation
report, writes an immutable raw artifact, and records an import batch.

Used by the CLI (`storesignal import`) and the API (`POST /api/v1/ingest`).
"""
import csv
import io
import json
import time
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from storesignal import settings as _settings

CANONICAL_COLUMNS = [
    "record_id", "source_id", "channel", "store_id", "timestamp",
    "text_raw", "language_hint", "rating",
]
REQUIRED_COLUMNS = ["record_id", "channel", "store_id", "timestamp", "text_raw"]
VALID_CHANNELS = {"online_review", "app_feedback", "staff_shift_note",
                  "call_transcript", "app_review", "call_centre", "other"}
MAX_LINE_BYTES = 256 * 1024

IMPORT_DIR = _settings.DATA_DIR / "processed" / "imports"
IMPORT_DIR.mkdir(parents=True, exist_ok=True)
BATCH_INDEX = IMPORT_DIR / "batches.jsonl"


def _new_batch_id() -> str:
    return f"IMP-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"


def _detect_format(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return {".csv": "csv", ".jsonl": "jsonl", ".ndjson": "jsonl",
            ".parquet": "parquet", ".pq": "parquet"}.get(ext, "unknown")


def preview(source: Path, n: int = 5) -> dict:
    """Return a safe preview without loading the whole file into memory."""
    fmt = _detect_format(str(source))
    if fmt == "csv":
        with open(source, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            rows = [next(reader, None) for _ in range(n)]
        rows = [r for r in rows if r is not None]
        cols = list(rows[0].keys()) if rows else []
    elif fmt == "jsonl":
        rows = []
        cols = []
        with open(source, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if len(line.encode("utf-8")) > MAX_LINE_BYTES:
                    continue
                rows.append(json.loads(line))
                if len(rows) >= n:
                    break
        if rows:
            cols = sorted({k for r in rows for k in r})
    elif fmt == "parquet":
        df = pd.read_parquet(source).head(n)
        rows = df.to_dict(orient="records")
        cols = list(df.columns)
    else:
        return {"format": fmt, "error": "unsupported file type"}
    return {"format": fmt, "columns": cols, "sample_rows": rows}


def validate_mapping(columns: list[str], mapping: dict[str, str]) -> list[str]:
    """Return list of error strings (empty = ok)."""
    errors = []
    for req in REQUIRED_COLUMNS:
        src = mapping.get(req)
        if not src:
            errors.append(f"required canonical field '{req}' has no source column")
        elif src not in columns:
            errors.append(f"mapped source column '{src}' not found in file")
    return errors


def _load_raw(source: Path, fmt: str) -> pd.DataFrame:
    if fmt == "csv":
        return pd.read_csv(source, dtype=str, keep_default_na=False)
    if fmt == "jsonl":
        return pd.read_json(source, lines=True, dtype=False)
    if fmt == "parquet":
        return pd.read_parquet(source)
    raise ValueError(f"unsupported format: {fmt}")


def run_import(
    source_path: Path,
    mapping: dict[str, str],
    channel_override: str | None = None,
) -> dict[str, Any]:
    """
    Execute an import. Returns:
      {batch_id, valid, rejected, warnings, sample_rejections,
       raw_artifact, mapping, channel_override, completed_at}
    """
    fmt = _detect_format(str(source_path))
    if fmt == "unknown":
        return {"error": "unsupported file type", "source": str(source_path)}

    df = _load_raw(source_path, fmt)
    if len(df) > _settings.MAX_ROWS:
        return {"error": f"row count {len(df)} exceeds STORESIGNAL_MAX_ROWS={_settings.MAX_ROWS}"}

    errors = validate_mapping(list(df.columns), mapping)
    if errors:
        return {"error": "mapping_invalid", "details": errors}

    renames = {src: canon for canon, src in mapping.items() if src in df.columns}
    df = df.rename(columns=renames)
    for col in CANONICAL_COLUMNS:
        if col not in df.columns:
            df[col] = None

    valid_rows = []
    rejected = []
    warnings = []
    for idx, row in df.iterrows():
        rec = {c: row.get(c) for c in CANONICAL_COLUMNS}
        rid = rec.get("record_id")
        if not rid:
            rejected.append({"row": int(idx), "reason": "missing record_id"})
            continue
        text = (rec.get("text_raw") or "").strip()
        if not text:
            rejected.append({"row": int(idx), "reason": "empty text", "record_id": rid})
            continue
        if channel_override:
            rec["channel"] = channel_override
        if rec.get("channel") not in VALID_CHANNELS:
            warnings.append({"row": int(idx), "issue": "unknown channel",
                             "value": rec.get("channel")})
            rec["channel"] = "other"
        ts = rec.get("timestamp")
        if not ts:
            rejected.append({"row": int(idx), "reason": "missing timestamp",
                             "record_id": rid})
            continue
        try:
            pd.to_datetime(ts)
        except Exception:
            rejected.append({"row": int(idx), "reason": "malformed timestamp",
                             "record_id": rid, "value": str(ts)})
            continue
        rec["record_id"] = str(rid)
        valid_rows.append(rec)

    batch_id = _new_batch_id()
    out_dir = IMPORT_DIR / batch_id
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_artifact = out_dir / "raw.parquet"
    pd.DataFrame(valid_rows).to_parquet(raw_artifact, index=False)
    (out_dir / "rejections.jsonl").write_text(
        "\n".join(json.dumps(r, default=str) for r in rejected), encoding="utf-8"
    )
    (out_dir / "warnings.jsonl").write_text(
        "\n".join(json.dumps(w, default=str) for w in warnings), encoding="utf-8"
    )
    manifest = {
        "batch_id": batch_id,
        "source_path": str(source_path),
        "source_format": fmt,
        "mapping": mapping,
        "channel_override": channel_override,
        "rows_in": int(len(df)),
        "rows_valid": len(valid_rows),
        "rows_rejected": len(rejected),
        "warnings": len(warnings),
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "raw_artifact": str(raw_artifact),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    with open(BATCH_INDEX, "a", encoding="utf-8") as f:
        f.write(json.dumps(manifest, default=str) + "\n")
    manifest["sample_rejections"] = rejected[:10]
    manifest["sample_warnings"] = warnings[:10]
    return manifest


def list_batches() -> list[dict]:
    if not BATCH_INDEX.exists():
        return []
    out = []
    for line in BATCH_INDEX.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def mapping_template() -> dict:
    """A reasonable default mapping for the mock dataset's JSONL shape."""
    return {c: c for c in CANONICAL_COLUMNS}

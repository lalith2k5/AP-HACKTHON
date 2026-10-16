"""
StoreSignal AI - Ingestion & Schema Validation
==============================================
Reads the 4 raw JSONL channel files, validates every record against a
Pydantic v2 schema, cross-checks store IDs, deduplicates on record_id,
applies PII redaction, and writes a single unified Parquet file.

Outputs:
  $HOME/storesignal-ai/data/processed/raw_feedback.parquet
  $HOME/storesignal-ai/data/processed/ingestion_report.json
"""

import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, Field, ValidationError, field_validator

from storesignal.paths import (
    CODE_ROOT,
    DATA_DIR,
    PROCESSED_DIR,
    RAW_DIR,
    REFERENCE_DIR,
    REPORTS_DIR,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HOME = Path.home()
ROOT = CODE_ROOT
DATA_RAW = RAW_DIR
DATA_REF = REFERENCE_DIR
DATA_PROCESSED = PROCESSED_DIR
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

CHANNEL_FILES = {
    "online_review":    DATA_RAW / "reviews.jsonl",
    "app_feedback":     DATA_RAW / "app_feedback.jsonl",
    "staff_shift_note": DATA_RAW / "staff_notes.jsonl",
    "call_transcript":  DATA_RAW / "call_transcripts.jsonl",
}

ALLOWED_CHANNELS = set(CHANNEL_FILES.keys())

# ---------------------------------------------------------------------------
# PII redaction
# ---------------------------------------------------------------------------
PHONE_RE = re.compile(r"(?:\+91[\s-]?)?\b[6-9]\d{9}\b")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
AADHAAR_RE = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")


def redact(text: str) -> str:
    if not text:
        return text
    text = PHONE_RE.sub("[PHONE]", text)
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = AADHAAR_RE.sub("[AADHAAR]", text)
    text = PAN_RE.sub("[PAN]", text)
    return text


# ---------------------------------------------------------------------------
# Pydantic v2 schema
# ---------------------------------------------------------------------------
class FeedbackRecord(BaseModel):
    record_id: str = Field(min_length=3)
    source_id: str = Field(min_length=1)
    channel: str
    store_id: str = Field(min_length=3)
    timestamp: datetime
    text_raw: str = Field(min_length=1)
    rating: int | None = None
    language_hint: str | None = None

    @field_validator("channel")
    @classmethod
    def _check_channel(cls, v: str) -> str:
        if v not in ALLOWED_CHANNELS:
            raise ValueError(f"channel '{v}' not allowed")
        return v

    @field_validator("rating")
    @classmethod
    def _check_rating(cls, v):
        if v is None:
            return v
        if not (1 <= v <= 5):
            raise ValueError("rating must be between 1 and 5")
        return v


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------
def load_store_master() -> pd.DataFrame:
    path = DATA_REF / "store_master.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing store master: {path}")
    df = pd.read_csv(path, dtype=str)
    required = {"store_id", "region_id", "region_name", "size_band", "weekly_footfall"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"store_master.csv missing columns: {missing}")
    return df


def load_taxonomy() -> pd.DataFrame:
    path = DATA_REF / "taxonomy.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing taxonomy: {path}")
    df = pd.read_csv(path, dtype=str)
    required = {"category_id", "category_name", "default_owner"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"taxonomy.csv missing columns: {missing}")
    return df


# ---------------------------------------------------------------------------
# JSONL reader
# ---------------------------------------------------------------------------
def read_jsonl(path: Path) -> list:
    records = []
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name} line {line_no}: {exc}") from exc
    return records


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def ingest():
    print("[ingestion] Loading reference data...")
    stores_df = load_store_master()
    taxonomy_df = load_taxonomy()
    valid_store_ids = set(stores_df["store_id"].astype(str))
    valid_categories = set(taxonomy_df["category_id"].astype(str))

    all_rows = []
    report = {
        "files": {},
        "total_files": len(CHANNEL_FILES),
        "total_records_read": 0,
        "total_records_valid": 0,
        "total_records_invalid": 0,
        "invalid_store_ids": 0,
        "duplicate_record_ids": 0,
        "schema_errors": [],
        "channel_counts": {},
        "valid_store_ids_count": len(valid_store_ids),
        "valid_categories_count": len(valid_categories),
        "timestamp_range": {"min": None, "max": None},
    }

    seen_ids = set()

    for channel, path in CHANNEL_FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing channel file: {path}")

        raw_records = read_jsonl(path)
        report["files"][channel] = {"path": str(path), "records": len(raw_records)}
        report["total_records_read"] += len(raw_records)

        valid_c = 0
        invalid_c = 0

        for idx, raw in enumerate(raw_records):
            try:
                rec = FeedbackRecord(**raw)
            except ValidationError as exc:
                invalid_c += 1
                msg = exc.errors()[0]["msg"] if exc.errors() else str(exc)
                report["schema_errors"].append(
                    {"channel": channel, "index": idx, "error": msg}
                )
                continue

            if rec.store_id not in valid_store_ids:
                invalid_c += 1
                report["invalid_store_ids"] += 1
                continue

            if rec.record_id in seen_ids:
                report["duplicate_record_ids"] += 1
                continue
            seen_ids.add(rec.record_id)

            all_rows.append({
                "record_id": rec.record_id,
                "source_id": rec.source_id,
                "channel": rec.channel,
                "store_id": rec.store_id,
                "timestamp": rec.timestamp,
                "text_raw": rec.text_raw,
                "text_redacted": redact(rec.text_raw),
                "rating": rec.rating if rec.rating is not None else -1,
                "language_hint": rec.language_hint or "unknown",
                "source_file": path.name,
            })
            valid_c += 1

        report["channel_counts"][channel] = {"valid": valid_c, "invalid": invalid_c}
        report["total_records_valid"] += valid_c
        report["total_records_invalid"] += invalid_c

    if not all_rows:
        raise RuntimeError("No valid records ingested. Aborting.")

    df = pd.DataFrame(all_rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, format="ISO8601")
    df = df.sort_values("timestamp").reset_index(drop=True)

    report["timestamp_range"]["min"] = df["timestamp"].min().isoformat()
    report["timestamp_range"]["max"] = df["timestamp"].max().isoformat()

    out_path = DATA_PROCESSED / "raw_feedback.parquet"
    df.to_parquet(out_path, engine="pyarrow", index=False)
    print(f"[ingestion] Wrote unified parquet -> {out_path} ({len(df)} rows)")

    report_path = DATA_PROCESSED / "ingestion_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"[ingestion] Wrote report         -> {report_path}")

    print("")
    print("[ingestion] SUMMARY")
    print(f"  Files read          : {report['total_files']}")
    print(f"  Records read        : {report['total_records_read']}")
    print(f"  Records valid       : {report['total_records_valid']}")
    print(f"  Records invalid     : {report['total_records_invalid']}")
    print(f"  Duplicate record IDs: {report['duplicate_record_ids']}")
    print(f"  Invalid store IDs   : {report['invalid_store_ids']}")
    print(f"  Timestamp range     : {report['timestamp_range']['min']} -> {report['timestamp_range']['max']}")
    for ch, stats in report["channel_counts"].items():
        print(f"  Channel {ch:20s} valid={stats['valid']:6d} invalid={stats['invalid']:4d}")


if __name__ == "__main__":
    ingest()

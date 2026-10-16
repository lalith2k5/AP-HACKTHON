"""
StoreSignal AI - Text Normalization
===================================
Reads the unified raw Parquet from ingestion and produces a normalized text
column ready for classification. Handles Unicode NFKC, zero-width chars,
control chars, whitespace collapse, safe English abbreviation expansion,
and defensive PII redaction.

Outputs:
  $HOME/storesignal-ai/data/processed/normalized_feedback.parquet
  $HOME/storesignal-ai/data/processed/normalization_report.json
"""

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

from storesignal.paths import (
    CODE_ROOT,
    PROCESSED_DIR,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HOME = Path.home()
ROOT = CODE_ROOT
DATA_PROCESSED = PROCESSED_DIR

IN_PARQUET = DATA_PROCESSED / "raw_feedback.parquet"
OUT_PARQUET = DATA_PROCESSED / "normalized_feedback.parquet"
REPORT_PATH = DATA_PROCESSED / "normalization_report.json"

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------
ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
WHITESPACE_RE = re.compile(r"\s+")

PHONE_RE = re.compile(r"(?:\+91[\s-]?)?\b[6-9]\d{9}\b")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
AADHAAR_RE = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")

# Conservative English-only expansion. We avoid ambiguous swaps (u -> you,
# r -> are) because they would corrupt Tamil/Marathi transliteration.
ABBREVIATION_MAP = [
    (re.compile(r"\bpls\b",  re.IGNORECASE), "please"),
    (re.compile(r"\bplz\b",  re.IGNORECASE), "please"),
    (re.compile(r"\bthx\b",  re.IGNORECASE), "thanks"),
    (re.compile(r"\btnx\b",  re.IGNORECASE), "thanks"),
    (re.compile(r"\bgr8\b",  re.IGNORECASE), "great"),
    (re.compile(r"\bmsg\b",  re.IGNORECASE), "message"),
    (re.compile(r"\binfo\b", re.IGNORECASE), "information"),
]


# ---------------------------------------------------------------------------
# Core normalization
# ---------------------------------------------------------------------------
def normalize_text(text):
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)

    text = unicodedata.normalize("NFKC", text)
    text = ZERO_WIDTH_RE.sub("", text)
    text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    text = CONTROL_RE.sub(" ", text)
    text = WHITESPACE_RE.sub(" ", text).strip()

    for pattern, replacement in ABBREVIATION_MAP:
        text = pattern.sub(replacement, text)

    text = PHONE_RE.sub("[PHONE]", text)
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = AADHAAR_RE.sub("[AADHAAR]", text)
    text = PAN_RE.sub("[PAN]", text)

    text = WHITESPACE_RE.sub(" ", text).strip()
    return text


def char_summary(series: pd.Series) -> dict:
    if len(series) == 0:
        return {"min": 0, "max": 0, "mean": 0.0, "median": 0.0}
    return {
        "min": int(series.min()),
        "max": int(series.max()),
        "mean": float(series.mean()),
        "median": float(series.median()),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def normalize():
    if not IN_PARQUET.exists():
        raise FileNotFoundError(
            f"Missing {IN_PARQUET}. Run ingestion.py first."
        )

    print(f"[normalization] Reading {IN_PARQUET}...")
    df = pd.read_parquet(IN_PARQUET, engine="pyarrow")
    print(f"[normalization] Loaded {len(df)} rows")

    df["text_norm"] = df["text_redacted"].apply(normalize_text)

    before = len(df)
    df = df[df["text_norm"].str.len() > 0].reset_index(drop=True)
    dropped = before - len(df)

    df["text_norm_chars"] = df["text_norm"].str.len()
    df["text_raw_chars"] = df["text_raw"].str.len()

    df.to_parquet(OUT_PARQUET, engine="pyarrow", index=False)
    print(f"[normalization] Wrote -> {OUT_PARQUET} ({len(df)} rows)")

    report = {
        "input_path": str(IN_PARQUET),
        "output_path": str(OUT_PARQUET),
        "rows_in": before,
        "rows_out": len(df),
        "rows_dropped_empty": dropped,
        "raw_char_counts": char_summary(df["text_raw_chars"]),
        "normalized_char_counts": char_summary(df["text_norm_chars"]),
        "channel_breakdown": df["channel"].value_counts().to_dict(),
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[normalization] Wrote report -> {REPORT_PATH}")

    print("")
    print("[normalization] SUMMARY")
    print(f"  Rows in / out           : {report['rows_in']} / {report['rows_out']}")
    print(f"  Dropped (empty)         : {report['rows_dropped_empty']}")
    print(f"  Raw chars (mean/median) : {report['raw_char_counts']['mean']:.1f} / {report['raw_char_counts']['median']:.0f}")
    print(f"  Norm chars (mean/median): {report['normalized_char_counts']['mean']:.1f} / {report['normalized_char_counts']['median']:.0f}")
    print("  Channel breakdown:")
    for ch, n in report["channel_breakdown"].items():
        print(f"    {ch:20s} {n}")


if __name__ == "__main__":
    normalize()

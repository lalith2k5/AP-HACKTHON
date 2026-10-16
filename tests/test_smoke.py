"""
StoreSignal AI — smoke tests
=============================
These tests do not re-run the pipeline. They verify that generated artifacts
exist and satisfy the invariants required by the spec.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path.home() / "storesignal-ai"
PROC = ROOT / "data" / "processed"
REF = ROOT / "data" / "reference"
RAW = ROOT / "data" / "raw"

MANDATORY = {"safety_hazard", "allergen_or_labeling",
             "food_safety_or_hygiene", "staff_misconduct"}


def test_reference_files_exist():
    assert (REF / "store_master.csv").exists()
    assert (REF / "taxonomy.csv").exists()


def test_raw_files_exist():
    for f in ["reviews.jsonl", "app_feedback.jsonl", "staff_notes.jsonl",
              "call_transcripts.jsonl", "hidden_labels.jsonl", "seeded_incidents.json"]:
        assert (RAW / f).exists(), f"missing {f}"


def test_unified_parquet_exists():
    assert (PROC / "normalized_feedback.parquet").exists()
    df = pd.read_parquet(PROC / "normalized_feedback.parquet")
    assert len(df) > 39000
    assert {"record_id", "channel", "store_id", "text_norm"} <= set(df.columns)
    assert df["text_norm"].str.len().min() > 0


def test_predictions_shape():
    df = pd.read_parquet(PROC / "predictions.parquet")
    assert len(df) > 39000
    assert {"record_id", "predicted_category", "confidence", "severity", "actionable"} <= set(df.columns)
    assert df["confidence"].between(0, 1).all()


def test_mandatory_categories_escalated_regardless_of_confidence():
    """Policy invariant: mandatory categories must escalate even at low confidence."""
    preds = pd.read_parquet(PROC / "predictions.parquet")
    esc = pd.read_parquet(PROC / "escalations.parquet")
    mandatory_rows = preds[preds["predicted_category"].isin(MANDATORY)]
    esc_ids = set(esc["record_id"].tolist())
    mandatory_ids = set(mandatory_rows["record_id"].tolist())
    missing = mandatory_ids - esc_ids
    assert not missing, f"{len(missing)} mandatory rows missing from escalations"


def test_escalation_low_confidence_invariant():
    """Mandatory escalations must not be silently dropped at low confidence."""
    esc = pd.read_parquet(PROC / "escalations.parquet")
    if len(esc) == 0:
        pytest.skip("no escalations")

    preds = pd.read_parquet(PROC / "predictions.parquet")
    low_conf_mandatory = preds[
        (preds["confidence"] < 0.4)
        & (preds["predicted_category"].isin(MANDATORY))
    ]
    low_conf_ids = set(low_conf_mandatory["record_id"].tolist())
    esc_ids = set(esc["record_id"].tolist())
    assert low_conf_ids <= esc_ids, "low-confidence mandatory rows were dropped"


def test_evaluation_report():
    p = ROOT / "data" / "evaluation" / "reports" / "evaluation_report.json"
    assert p.exists()
    r = json.loads(p.read_text())
    assert r["classification"]["macro_f1"] > 0.5
    assert r["seeded_incidents"]["total"] == 3
    assert r["seeded_incidents"]["detected"] >= 1


def test_incidents_and_alerts():
    inc = pd.read_parquet(PROC / "incidents.parquet")
    alerts = pd.read_parquet(PROC / "alerts.parquet")
    assert len(inc) > 0
    assert len(alerts) > 0
    assert {"incident_id", "store_id", "predicted_category", "severity"} <= set(inc.columns)
    assert {"alert_id", "trigger_type", "severity", "priority"} <= set(alerts.columns)


def test_briefs_generated():
    briefs_dir = PROC / "briefs"
    assert briefs_dir.exists()
    md_files = list(briefs_dir.glob("brief_*.md"))
    assert len(md_files) >= 1

"""
StoreSignal AI — risk policy invariant tests
=============================================
Verifies that the mandatory-escalation engine operates independently of
classifier confidence and volume.
"""

from pathlib import Path

import pandas as pd

ROOT = Path.home() / "storesignal-ai"
PROC = ROOT / "data" / "processed"

MANDATORY = {"safety_hazard", "allergen_or_labeling",
             "food_safety_or_hygiene", "staff_misconduct"}


def test_all_mandatory_predicted_categories_escalated():
    preds = pd.read_parquet(PROC / "predictions.parquet")
    esc = pd.read_parquet(PROC / "escalations.parquet")
    esc_ids = set(esc["record_id"].tolist())
    for cat in MANDATORY:
        subset = preds[preds["predicted_category"] == cat]
        if len(subset) == 0:
            continue
        for rid in subset["record_id"].tolist():
            assert rid in esc_ids, f"{cat} row {rid} was not escalated"


def test_escalation_reasons_are_populated():
    esc = pd.read_parquet(PROC / "escalations.parquet")
    assert (esc["escalation_reason"].str.len() > 0).all()

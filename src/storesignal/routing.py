"""
StoreSignal AI - Routing
========================
Maps each prediction to its owning function (Store Ops / Supply Chain /
Merchandising / Digital / HR) using the supplied taxonomy, and provides a
recommended next action and SLA.
"""

import json

import pandas as pd

from storesignal.config_loader import load_config
from storesignal.paths import (
    CODE_ROOT,
    PROCESSED_DIR,
    REFERENCE_DIR,
)

_cfg = load_config()

ROOT = CODE_ROOT
TAXONOMY_CSV = REFERENCE_DIR / "taxonomy.csv"
PRED_PARQUET = PROCESSED_DIR / "predictions.parquet"
ESC_PARQUET = PROCESSED_DIR / "escalations.parquet"
OUT_PARQUET = PROCESSED_DIR / "routing.parquet"
REPORT_PATH = PROCESSED_DIR / "routing_report.json"

# Next actions per owner (generic defaults; spec allows extension)
NEXT_ACTION_BY_OWNER = {
    "Store Ops":     "Dispatch store ops review within 24h; verify on-site condition.",
    "Supply Chain":  "Confirm stock position and reallocate from nearest DC.",
    "Merchandising": "Verify shelf/price/promo execution; correct labels on site.",
    "Digital":       "File product bug and attach affected order/offer IDs.",
    "HR":            "Open HR case; preserve evidence; assign reviewer.",
}

SLA_HOURS_BY_SEVERITY = {
    "critical": 4,
    "review_required": 4,
    "high": 24,
    "medium": 72,
    "low": 168,
}


def route():
    taxonomy = pd.read_csv(TAXONOMY_CSV)
    owner_map = dict(zip(taxonomy["category_id"], taxonomy["default_owner"]))

    preds = pd.read_parquet(PRED_PARQUET, engine="pyarrow")
    print(f"[routing] Loaded {len(preds)} predictions")

    preds["owner_function"] = preds["predicted_category"].map(owner_map).fillna("Store Ops")
    preds["next_action"] = preds["owner_function"].map(NEXT_ACTION_BY_OWNER)
    preds["sla_hours"] = preds["severity"].map(SLA_HOURS_BY_SEVERITY).fillna(72).astype(int)

    # Escalation rule per issue (R5 brief: "with the escalation rule stated")
    mandatory = set(_cfg.risk_policy.mandatory_categories)
    def _rule(cat, sev):
        if cat in mandatory:
            return "mandatory_policy:high_risk_category"
        if sev in ("critical", "review_required"):
            return "severity_based:critical"
        if sev == "high":
            return "severity_based:high"
        return "routine_review"
    preds["escalation_rule"] = [
        _rule(c, s) for c, s in zip(preds["predicted_category"], preds["severity"])
    ]

    out_cols = [
        "record_id", "channel", "store_id", "timestamp",
        "predicted_category", "weak_category", "confidence",
        "severity", "actionable", "owner_function",
        "next_action", "sla_hours", "escalation_rule",
    ]
    preds[out_cols].to_parquet(OUT_PARQUET, engine="pyarrow", index=False)
    print(f"[routing] Wrote routing -> {OUT_PARQUET}")

    # Owner distribution
    owner_counts = preds["owner_function"].value_counts().to_dict()

    # Owner distribution among escalated records only
    esc = pd.read_parquet(ESC_PARQUET, engine="pyarrow")
    esc = esc.merge(
        preds[["record_id", "owner_function"]], on="record_id", how="left"
    )
    escalated_owner_counts = esc["owner_function"].value_counts().to_dict()

    report = {
        "total_routed": int(len(preds)),
        "owner_function_counts": owner_counts,
        "escalated_owner_function_counts": escalated_owner_counts,
        "sla_hours_by_severity": SLA_HOURS_BY_SEVERITY,
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[routing] Wrote report -> {REPORT_PATH}")

    print("")
    print("[routing] SUMMARY")
    print("  Owner distribution (all records):")
    for owner, n in owner_counts.items():
        print(f"    {owner:16s} {n}")
    print("  Owner distribution (escalated):")
    for owner, n in escalated_owner_counts.items():
        print(f"    {owner:16s} {n}")


if __name__ == "__main__":
    route()

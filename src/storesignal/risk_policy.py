"""
StoreSignal AI — Mandatory Risk Policy Engine
==============================================
Applies mandatory escalation to predictions in a way that is independent of:
  - complaint volume
  - classifier confidence

Rules (from R5 spec):
  - Any record whose PREDICTED category OR weak_category is in the mandatory
    set is escalated, even at confidence 0.
  - Escalation cannot be suppressed by low confidence.
  - Escalation reason is recorded for auditability.
"""

import json
from pathlib import Path

import pandas as pd
import yaml

from storesignal.paths import (
    CODE_ROOT,
    DATA_DIR,
    PROCESSED_DIR,
    RAW_DIR,
    REFERENCE_DIR,
    REPORTS_DIR,
)

ROOT = CODE_ROOT
CONFIG_PATH = ROOT / "config" / "config.yaml"
PRED_PARQUET = PROCESSED_DIR / "predictions.parquet"
OUT_PARQUET = PROCESSED_DIR / "escalations.parquet"
REPORT_PATH = PROCESSED_DIR / "risk_policy_report.json"


def load_policy():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return set(cfg["risk_policy"]["mandatory_categories"])


def apply_policy():
    mandatory = load_policy()
    print(f"[risk_policy] Mandatory categories: {sorted(mandatory)}")

    df = pd.read_parquet(PRED_PARQUET, engine="pyarrow")
    print(f"[risk_policy] Loaded {len(df)} predictions")

    # Escalation triggers — evaluated independently of confidence
    cat_trigger = df["predicted_category"].isin(mandatory)
    weak_trigger = df["weak_category"].isin(mandatory)
    sev_trigger = df["severity"].isin(["critical", "review_required"])

    df["policy_escalation"] = (cat_trigger | weak_trigger | sev_trigger).astype(bool)

    reasons = []
    for i, row in df.iterrows():
        rs = []
        if row["predicted_category"] in mandatory:
            rs.append(f"predicted_category:{row['predicted_category']}")
        if row["weak_category"] in mandatory:
            rs.append(f"weak_category:{row['weak_category']}")
        if row["severity"] in ("critical", "review_required"):
            rs.append(f"severity:{row['severity']}")
        reasons.append("|".join(rs) if rs else "")
    df["escalation_reason"] = reasons

    escalated = df[df["policy_escalation"]].copy()
    escalated = escalated.sort_values(
        ["policy_escalation", "severity", "confidence"],
        ascending=[False, True, False],
    ).reset_index(drop=True)

    escalated.to_parquet(OUT_PARQUET, engine="pyarrow", index=False)
    print(f"[risk_policy] Wrote escalated records -> {OUT_PARQUET} ({len(escalated)} rows)")

    report = {
        "total_predictions": int(len(df)),
        "total_escalated": int(len(escalated)),
        "escalation_rate": round(len(escalated) / max(len(df), 1), 4),
        "mandatory_categories": sorted(mandatory),
        "escalated_by_category": escalated["predicted_category"].value_counts().to_dict(),
        "escalated_by_severity": escalated["severity"].value_counts().to_dict(),
        "escalated_low_confidence_count": int(
            ((escalated["confidence"] < 0.4)).sum()
        ),
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[risk_policy] Wrote report -> {REPORT_PATH}")

    print("")
    print("[risk_policy] SUMMARY")
    print(f"  Total predictions            : {report['total_predictions']}")
    print(f"  Total escalated              : {report['total_escalated']}")
    print(f"  Escalation rate              : {report['escalation_rate']}")
    print(f"  Escalated @ confidence < 0.4 : {report['escalated_low_confidence_count']}")
    print("  Escalated by severity:")
    for sev, n in report["escalated_by_severity"].items():
        print(f"    {sev:16s} {n}")


if __name__ == "__main__":
    apply_policy()

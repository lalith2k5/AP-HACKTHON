"""
StoreSignal AI - Evaluation
============================
Computes the three scorecard metrics required by the R5 brief:

  1. Classification quality (accuracy, macro-F1, weighted-F1)
     scored against the hidden labels.

  2. Escalation quality
     - Precision: of the records we escalated that have hidden labels,
       what fraction are truly actionable?
     - Recall: of the hidden-labelled records that are truly actionable,
       what fraction did we escalate?

  3. Seeded-incident lead time
     For each of the 3 planted incidents, find the day the Early-Warning
     Radar first flagged the same (store, category), and compute how many
     days earlier that is than the incident's PEAK day.

IMPORTANT: This is the ONLY script that reads hidden_labels.jsonl.
Hidden labels are never used for training, tuning, or detection.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, f1_score

from versioning import stamp_run

HOME = Path.home()
ROOT = HOME / "storesignal-ai"

HIDDEN = ROOT / "data" / "raw" / "hidden_labels.jsonl"
SEEDS = ROOT / "data" / "raw" / "seeded_incidents.json"
PRED_PARQUET = ROOT / "data" / "processed" / "predictions.parquet"
ESC_PARQUET = ROOT / "data" / "processed" / "escalations.parquet"
FLAGS_PARQUET = ROOT / "data" / "processed" / "radar_flags.parquet"
PROC_ALERTS = ROOT / "data" / "processed" / "alerts.parquet"
PROC_INCIDENTS = ROOT / "data" / "processed" / "incidents.parquet"
MANDATORY_CATS = {"safety_hazard", "allergen_or_labeling", "food_safety_or_hygiene", "staff_misconduct"}

OUT_DIR = ROOT / "data" / "evaluation" / "reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "evaluation_report.json"
OUT_MD = OUT_DIR / "evaluation_report.md"


def read_jsonl(path: Path) -> list:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main():
    print("[evaluate] Loading artifacts...")
    hidden = pd.DataFrame(read_jsonl(HIDDEN)).rename(columns={
        "issue_category": "true_category",
        "severity": "true_severity",
        "actionable": "true_actionable",
    })
    preds = pd.read_parquet(PRED_PARQUET, engine="pyarrow")
    escalations = pd.read_parquet(ESC_PARQUET, engine="pyarrow")
    flags = pd.read_parquet(FLAGS_PARQUET, engine="pyarrow")

    seeds = json.loads(SEEDS.read_text())

    print(f"  hidden labels : {len(hidden)}")
    print(f"  predictions   : {len(preds)}")
    print(f"  escalations   : {len(escalations)}")
    print(f"  radar flags   : {len(flags)}")
    print(f"  seeded        : {len(seeds)}")

    # ------------------------------------------------------------------
    # 1. Classification quality on hidden labels
    # ------------------------------------------------------------------
    merged = hidden.merge(
        preds[["record_id", "predicted_category", "confidence"]],
        on="record_id", how="inner",
    )
    print(f"[evaluate] Matched {len(merged)} hidden-labelled records")

    if len(merged) == 0:
        raise RuntimeError("No overlap between hidden labels and predictions.")

    y_true = merged["true_category"].astype(str)
    y_pred = merged["predicted_category"].astype(str)

    accuracy = float((y_true == y_pred).mean())
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
    per_class = classification_report(y_true, y_pred, output_dict=True, zero_division=0)

    print(f"[evaluate] Accuracy   : {accuracy:.4f}")
    print(f"[evaluate] Macro-F1   : {macro_f1:.4f}")
    print(f"[evaluate] Weighted-F1: {weighted_f1:.4f}")

    # ------------------------------------------------------------------
    # 2. Escalation precision / recall
    # ------------------------------------------------------------------
    esc_ids = set(escalations["record_id"].tolist())
    actionable_ids = set(
        hidden[hidden["true_actionable"] == True]["record_id"].tolist()
    )

    hidden_for_esc = hidden[hidden["record_id"].isin(esc_ids)]
    esc_labelled_count = int(len(hidden_for_esc))
    esc_precision = (
        float(hidden_for_esc["true_actionable"].mean())
        if esc_labelled_count > 0 else None
    )

    actionable_escalated = actionable_ids & esc_ids
    esc_recall = (
        float(len(actionable_escalated) / len(actionable_ids))
        if len(actionable_ids) > 0 else None
    )

    print(f"[evaluate] Escalated (total)         : {len(esc_ids)}")
    print(f"[evaluate] Escalated with hidden lbl : {esc_labelled_count}")
    print(f"[evaluate] Escalation precision      : {esc_precision}")
    print(f"[evaluate] Escalation recall         : {esc_recall}")

    # ------------------------------------------------------------------
    # 3. Seeded-incident lead time
    # ------------------------------------------------------------------
    preds_ts = preds.copy()
    preds_ts["timestamp"] = pd.to_datetime(preds_ts["timestamp"], utc=True)
    preds_ts["day"] = preds_ts["timestamp"].dt.normalize()

    if not flags.empty:
        flags_ts = flags.copy()
        flags_ts["day"] = pd.to_datetime(flags_ts["day"], utc=True).dt.normalize()
    else:
        flags_ts = flags

    seed_results = []

    for seed in seeds:
        store = seed["store_id"]
        cat = seed["category_id"]
        first_seen = pd.to_datetime(seed["first_seen"], utc=True).normalize()

        # Ground-truth record population for this seed (predicted OR weak)
        seed_preds = preds_ts[
            (preds_ts["store_id"] == store)
            & ((preds_ts["predicted_category"] == cat)
               | (preds_ts["weak_category"] == cat))
        ]

        peak_day = None
        first_record_day = None
        if len(seed_preds) > 0:
            daily_counts = seed_preds.groupby("day").size()
            peak_day = daily_counts.idxmax().normalize()
            first_record_day = daily_counts.index.min().normalize()

        # Radar match (predicted category)
        flag_match = (
            flags_ts[(flags_ts["store_id"] == store)
                     & (flags_ts["predicted_category"] == cat)]
            if not flags_ts.empty else flags_ts
        )

        # Fallback: any flag for this store on a day the seed's records appear
        if (flag_match is None or len(flag_match) == 0) and len(seed_preds) > 0:
            seed_days = set(seed_preds["day"].tolist())
            flag_match = (
                flags_ts[(flags_ts["store_id"] == store)
                         & (flags_ts["day"].isin(seed_days))]
                if not flags_ts.empty else flags_ts
            )

        first_flag_day = (
            flag_match["day"].min().normalize()
            if flag_match is not None and len(flag_match) > 0 else None
        )

        lead_vs_first_seen = (
            int((first_seen - first_flag_day).days)
            if first_flag_day is not None else None
        )
        lead_vs_peak = (
            int((peak_day - first_flag_day).days)
            if first_flag_day is not None and peak_day is not None else None
        )
        lead_vs_first_record = (
            int((first_record_day - first_flag_day).days)
            if first_flag_day is not None and first_record_day is not None else None
        )

        seed_results.append({
            "incident_id": seed["incident_id"],
            "store_id": store,
            "category_id": cat,
            "severity": seed["severity"],
            "record_count": seed["record_count"],
            "first_seen": first_seen.date().isoformat(),
            "first_record_day": first_record_day.date().isoformat() if first_record_day is not None else None,
            "peak_day": peak_day.date().isoformat() if peak_day is not None else None,
            "first_flag_day": first_flag_day.date().isoformat() if first_flag_day is not None else None,
            "detected": first_flag_day is not None,
            "lead_days_vs_first_seen": lead_vs_first_seen,
            "lead_days_vs_first_record": lead_vs_first_record,
            "lead_days_vs_peak": lead_vs_peak,
        })

        print(f"[evaluate] Seed {seed['incident_id']}: "
              f"detected={first_flag_day is not None} "
              f"first_flag={first_flag_day.date() if first_flag_day is not None else None} "
              f"peak={peak_day.date() if peak_day is not None else None} "
              f"lead_vs_peak={lead_vs_peak}")

    detected = sum(1 for s in seed_results if s["detected"])
    lead_values = [s["lead_days_vs_peak"] for s in seed_results
                   if s["lead_days_vs_peak"] is not None]
    mean_lead = float(np.mean(lead_values)) if lead_values else None

    # ------------------------------------------------------------------
    # 4. False alerts per store-week
    # ------------------------------------------------------------------
    preds_ts_all = preds_ts
    n_weeks = max((preds_ts_all["day"].max() - preds_ts_all["day"].min()).days / 7.0, 1.0)
    n_stores = preds_ts_all["store_id"].nunique()
    store_weeks = max(n_stores * n_weeks, 1.0)
    if (PROC_ALERTS).exists():
        alerts_df_for_metric = pd.read_parquet(PROC_ALERTS, engine="pyarrow")
        false_alerts_per_store_week = round(float(len(alerts_df_for_metric)) / store_weeks, 4)

    # ------------------------------------------------------------------
    # 5. Duplicate / fusion quality (cross-channel capture)
    # ------------------------------------------------------------------
    if (PROC_INCIDENTS).exists():
        inc_df = pd.read_parquet(PROC_INCIDENTS, engine="pyarrow")
        multi = int((inc_df["record_count"] > 1).sum())
        cross = int(inc_df["channels"].str.contains(r"\|").sum())
        total_inc = int(len(inc_df))
        fusion_quality = {
            "total_incidents": total_inc,
            "multi_record_incidents": multi,
            "cross_channel_incidents": cross,
            "multi_record_ratio": round(multi / max(total_inc, 1), 4),
            "cross_channel_ratio": round(cross / max(total_inc, 1), 4),
        }
    else:
        fusion_quality = {}

    # ------------------------------------------------------------------
    # 6. Channel + language coverage
    # ------------------------------------------------------------------
    preds_ts["channel"] = preds_ts["channel"].astype(str)
    channel_coverage = preds_ts["channel"].value_counts().to_dict()
    if "language_hint" in preds_ts.columns:
        lang_coverage = {
            str(k): int(v)
            for k, v in preds_ts["language_hint"].value_counts().to_dict().items()
        }
    else:
        # Fallback: join from normalized_feedback
        norm_path = ROOT / "data" / "processed" / "normalized_feedback.parquet"
        if norm_path.exists():
            norm_df = pd.read_parquet(norm_path, engine="pyarrow")[["record_id", "language_hint"]]
            merged = preds_ts.merge(norm_df, on="record_id", how="left", suffixes=("", "_norm"))
            hint_col = "language_hint_norm" if "language_hint_norm" in merged.columns else "language_hint"
            lang_coverage = {
                str(k): int(v)
                for k, v in merged[hint_col].value_counts().to_dict().items()
            }
        else:
            lang_coverage = {}

    # ------------------------------------------------------------------
    # 7. Policy compliance: mandatory-category records that were escalated
    # ------------------------------------------------------------------
    esc_ids_local = set(escalations["record_id"].tolist())
    mandatory_preds = preds_ts[preds_ts["predicted_category"].isin(MANDATORY_CATS)]
    mandatory_count = int(len(mandatory_preds))
    mandatory_escalated = int(mandatory_preds["record_id"].isin(esc_ids_local).sum())
    policy_compliance = (
        round(mandatory_escalated / mandatory_count, 4)
        if mandatory_count > 0 else 1.0
    )

    # ------------------------------------------------------------------
    # 8. Human override rate + resolution outcomes (from actions.jsonl)
    # ------------------------------------------------------------------
    actions_log = ROOT / "data" / "processed" / "actions.jsonl"
    override_count = 0
    resolve_count = 0
    total_events = 0
    if actions_log.exists():
        with open(actions_log, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                total_events += 1
                if ev.get("status") == "override" or ev.get("event_type") == "override":
                    override_count += 1
                if ev.get("event_type") == "resolve":
                    resolve_count += 1
    review_events = 0
    if actions_log.exists():
        with open(actions_log, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if ev.get("event_type") == "review":
                    review_events += 1
    human_override_rate = (
        round(override_count / review_events, 4) if review_events > 0 else 0.0
    )
    resolution_outcome_rate = (
        round(resolve_count / total_events, 4) if total_events > 0 else 0.0
    )

    # ------------------------------------------------------------------
    # Write reports
    # ------------------------------------------------------------------
    report = {
        "classification": {
            "hidden_labels_total": int(len(hidden)),
            "matched_records": int(len(merged)),
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
            "per_class_f1": {
                k: float(v["f1-score"])
                for k, v in per_class.items()
                if isinstance(v, dict) and "f1-score" in v
            },
        },
        "escalation": {
            "escalated_total": int(len(esc_ids)),
            "escalated_with_hidden_labels": esc_labelled_count,
            "actionable_total_in_hidden_labels": int(len(actionable_ids)),
            "escalation_precision": esc_precision,
            "escalation_recall": esc_recall,
        },
        "operational": {
            "false_alerts_per_store_week": false_alerts_per_store_week,
            "fusion_quality": fusion_quality,
            "channel_coverage": channel_coverage,
            "language_coverage": lang_coverage,
            "policy_compliance": policy_compliance,
            "mandatory_records": mandatory_count,
            "mandatory_escalated": mandatory_escalated,
            "human_override_rate": human_override_rate,
            "resolution_outcome_rate": resolution_outcome_rate,
            "total_action_events": total_events,
        },
        "seeded_incidents": {
            "total": len(seed_results),
            "detected": detected,
            "mean_lead_days_vs_peak": mean_lead,
            "details": seed_results,
        },
    }

    # Stamp the run with config/data/model hashes for reproducibility
    stamped = stamp_run({
        "macro_f1": macro_f1,
        "accuracy": accuracy,
        "escalation_precision": esc_precision,
        "seeded_detected": detected,
        "mean_lead_days_vs_peak": mean_lead,
    })
    report["run_id"] = stamped["run_id"]
    report["config_hash"] = stamped["config_hash"]
    report["data_hash"] = stamped["data_hash"]
    report["model_hash"] = stamped["model_hash"]

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[evaluate] Wrote JSON -> {OUT_JSON}")

    md = []
    md.append("# StoreSignal AI - Evaluation Report")
    md.append("")
    md.append("## 1. Classification quality on hidden labels")
    md.append("")
    md.append(f"- Matched records: **{len(merged)}**")
    md.append(f"- Accuracy: **{accuracy:.4f}**")
    md.append(f"- Macro-F1: **{macro_f1:.4f}**")
    md.append(f"- Weighted-F1: **{weighted_f1:.4f}**")
    md.append("")
    md.append("## 2. Escalation quality")
    md.append("")
    md.append(f"- Escalated (total): **{len(esc_ids)}**")
    md.append(f"- Escalated with hidden labels: **{esc_labelled_count}**")
    md.append(f"- Truly actionable in hidden labels: **{len(actionable_ids)}**")
    md.append(f"- **Escalation precision**: **{esc_precision}**")
    md.append(f"- **Escalation recall**: **{esc_recall}**")
    md.append("")
    md.append("## 2b. Operational metrics")
    md.append("")
    md.append(f"- False alerts per store-week: **{false_alerts_per_store_week}**")
    md.append(f"- Policy compliance: **{policy_compliance}** ({mandatory_escalated}/{mandatory_count} mandatory records escalated)")
    md.append(f"- Fusion quality: multi-record ratio **{fusion_quality.get('multi_record_ratio', 0)}**, cross-channel ratio **{fusion_quality.get('cross_channel_ratio', 0)}**")
    md.append(f"- Human override rate: **{human_override_rate}**")
    md.append(f"- Resolution outcome rate: **{resolution_outcome_rate}**")
    md.append("")
    md.append("## 3. Seeded-incident lead time")
    md.append("")
    md.append(f"- Detected: **{detected}/{len(seed_results)}**")
    md.append(f"- Mean lead time vs peak: **{mean_lead} days**")
    md.append("")
    md.append("| Incident | Store | Category | First seen | First record | Peak | First flag | Lead vs peak (d) |")
    md.append("|---|---|---|---|---|---|---|---|")
    for s in seed_results:
        md.append(
            f"| {s['incident_id']} | {s['store_id']} | {s['category_id']} | "
            f"{s['first_seen']} | {s['first_record_day']} | {s['peak_day']} | "
            f"{s['first_flag_day']} | {s['lead_days_vs_peak']} |"
        )
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"[evaluate] Wrote MD   -> {OUT_MD}")

    print("")
    print("================= EVALUATION SUMMARY =================")
    print(f"  Accuracy               : {accuracy:.4f}")
    print(f"  Macro-F1 (hidden)      : {macro_f1:.4f}")
    print(f"  Weighted-F1 (hidden)   : {weighted_f1:.4f}")
    print(f"  Escalation precision   : {esc_precision}")
    print(f"  Escalation recall      : {esc_recall}")
    print(f"  Seeded detected        : {detected}/{len(seed_results)}")
    print(f"  Mean lead days vs peak : {mean_lead}")


if __name__ == "__main__":
    main()

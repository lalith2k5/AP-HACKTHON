"""
StoreSignal AI - Alert Generation
==================================
Builds evidence-backed alerts by combining:
  - policy escalations (mandatory risk)
  - radar flags (early-warning anomalies)
  - incident fusion (deduplicated evidence)

Each alert is prioritized and includes a human-readable reason and evidence
quotes pulled from the underlying incident.
"""

import json

import pandas as pd

from storesignal.paths import (
    CODE_ROOT,
    PROCESSED_DIR,
)

ROOT = CODE_ROOT
INCIDENTS_PARQUET = PROCESSED_DIR / "incidents.parquet"
LINKS_PARQUET = PROCESSED_DIR / "incident_links.parquet"
ESC_PARQUET = PROCESSED_DIR / "escalations.parquet"
FLAGS_PARQUET = PROCESSED_DIR / "radar_flags.parquet"
ROUTING_PARQUET = PROCESSED_DIR / "routing.parquet"

OUT_PARQUET = PROCESSED_DIR / "alerts.parquet"
REPORT_PATH = PROCESSED_DIR / "alerts_report.json"

SEV_RANK = {"critical": 4, "review_required": 4, "high": 3, "medium": 2, "low": 1}


def _evidence_from_incident(links_df, incident_id, routing_df, max_n=3):
    rec_ids = links_df[links_df["incident_id"] == incident_id]["record_id"].tolist()
    subset = routing_df[routing_df["record_id"].isin(rec_ids)].head(max_n)
    return subset["text_norm"].tolist() if "text_norm" in subset.columns else []


def build():
    incidents = pd.read_parquet(INCIDENTS_PARQUET, engine="pyarrow")
    links = pd.read_parquet(LINKS_PARQUET, engine="pyarrow")
    escalations = pd.read_parquet(ESC_PARQUET, engine="pyarrow")
    flags = pd.read_parquet(FLAGS_PARQUET, engine="pyarrow")
    routing = pd.read_parquet(ROUTING_PARQUET, engine="pyarrow")

    # Bring text_norm into routing view for evidence
    preds_text = pd.read_parquet(
        PROCESSED_DIR / "predictions.parquet", engine="pyarrow"
    )[["record_id", "text_norm"]]
    routing = routing.merge(preds_text, on="record_id", how="left")

    print(f"[alerts] Incidents: {len(incidents)} | Escalations: {len(escalations)} | Flags: {len(flags)}")

    alerts = []

    # ------------------------------------------------------------------
    # 1. Policy-driven alerts (from escalations)
    # ------------------------------------------------------------------
    escalated_ids = set(escalations["record_id"].tolist())
    link_of_record = links.set_index("record_id")["incident_id"].to_dict()

    # Group escalations by their incident
    inc_to_esc = {}
    for rid in escalated_ids:
        inc = link_of_record.get(rid)
        if inc:
            inc_to_esc.setdefault(inc, []).append(rid)

    incident_by_id = incidents.set_index("incident_id").to_dict(orient="index")

    for inc_id, rec_ids in inc_to_esc.items():
        inc = incident_by_id.get(inc_id)
        if not inc:
            continue
        evidence = _evidence_from_incident(links, inc_id, routing, max_n=3)
        alerts.append({
            "alert_id": f"AL-POL-{inc_id[-8:]}",
            "trigger_type": "policy_mandatory",
            "incident_id": inc_id,
            "store_id": inc["store_id"],
            "predicted_category": inc["predicted_category"],
            "owner_function": inc["owner_function"],
            "severity": inc["severity"],
            "priority": SEV_RANK.get(inc["severity"], 1) + 1,
            "reason": f"Mandatory policy trigger: {inc['predicted_category']}",
            "record_count": inc["record_count"],
            "escalated_count": len(rec_ids),
            "evidence": evidence,
            "first_seen": inc["first_seen"],
            "last_seen": inc["last_seen"],
        })

    # ------------------------------------------------------------------
    # 2. Radar-driven alerts (from early-warning flags)
    # ------------------------------------------------------------------
    if not flags.empty:
        flag_incident_keys = {
            (row["store_id"], row["predicted_category"])
            for _, row in flags.iterrows()
        }

        incidents_key = incidents.set_index(["store_id", "predicted_category"])

        for (store, cat) in flag_incident_keys:
            if (store, cat) not in incidents_key.index:
                continue
            row = incidents_key.loc[(store, cat)]
            if isinstance(row, pd.DataFrame):
                row = row.sort_values("record_count", ascending=False).iloc[0]

            flag_rows = flags[(flags["store_id"] == store) & (flags["predicted_category"] == cat)]
            max_z = float(flag_rows["robust_z"].max())
            first_flag = flag_rows["day"].min()

            evidence = _evidence_from_incident(links, row["incident_id"], routing, max_n=3)

            alerts.append({
                "alert_id": f"AL-RAD-{row['incident_id'][-8:]}",
                "trigger_type": "radar_anomaly",
                "incident_id": row["incident_id"],
                "store_id": store,
                "predicted_category": cat,
                "owner_function": row["owner_function"],
                "severity": row["severity"],
                "priority": SEV_RANK.get(row["severity"], 1) + 2,
                "reason": f"Early-warning anomaly: z={max_z:.2f}, first flagged {first_flag.date()}",
                "record_count": int(row["record_count"]),
                "escalated_count": 0,
                "evidence": evidence,
                "first_seen": row["first_seen"],
                "last_seen": row["last_seen"],
            })

    # ------------------------------------------------------------------
    # Attach uncertainty: 1 - mean confidence of contributing records
    # ------------------------------------------------------------------
    conf_by_inc = {}
    if len(links) > 0:
        preds_conf = pd.read_parquet(
            PROCESSED_DIR / "predictions.parquet", engine="pyarrow"
        )[["record_id", "confidence"]]
        link_conf = links.merge(preds_conf, on="record_id", how="left")
        conf_by_inc = link_conf.groupby("incident_id")["confidence"].mean().to_dict()

    for a in alerts:
        inc_id = a.get("incident_id")
        mean_conf = conf_by_inc.get(inc_id)
        if mean_conf is None or pd.isna(mean_conf):
            a["uncertainty"] = 1.0
        else:
            a["uncertainty"] = round(1.0 - float(mean_conf), 4)

    # Deduplicate by alert_id, prefer highest priority
    alerts_df = pd.DataFrame(alerts)
    if len(alerts_df) > 0:
        alerts_df = (
            alerts_df.sort_values("priority", ascending=False)
            .drop_duplicates(subset=["alert_id"], keep="first")
            .reset_index(drop=True)
        )
        alerts_df["evidence"] = alerts_df["evidence"].apply(
            lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, list) else "[]"
        )

    alerts_df.to_parquet(OUT_PARQUET, engine="pyarrow", index=False)
    print(f"[alerts] Wrote alerts -> {OUT_PARQUET} ({len(alerts_df)} rows)")

    report = {
        "total_alerts": int(len(alerts_df)),
        "by_trigger_type": (
            alerts_df["trigger_type"].value_counts().to_dict() if len(alerts_df) else {}
        ),
        "by_severity": (
            alerts_df["severity"].value_counts().to_dict() if len(alerts_df) else {}
        ),
        "by_owner_function": (
            alerts_df["owner_function"].value_counts().to_dict() if len(alerts_df) else {}
        ),
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[alerts] Wrote report -> {REPORT_PATH}")

    print("")
    print("[alerts] SUMMARY")
    print(f"  Total alerts           : {report['total_alerts']}")
    print(f"  By trigger             : {report['by_trigger_type']}")
    print(f"  By severity            : {report['by_severity']}")
    print(f"  By owner function      : {report['by_owner_function']}")


if __name__ == "__main__":
    build()

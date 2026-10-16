"""
StoreSignal AI - Incident Fusion (deduplication)
================================================
Groups near-duplicate reports into candidate incidents within the same
(store, category, day-bucket) using RapidFuzz token-set ratio on
normalized text.

Outputs a many-to-many link table (incident_id <-> record_id) so that
source evidence is preserved.
"""

import json
import uuid

import pandas as pd
from rapidfuzz import fuzz

from storesignal.paths import (
    CODE_ROOT,
    PROCESSED_DIR,
    REPORTS_DIR,
)

ROOT = CODE_ROOT
PRED_PARQUET = PROCESSED_DIR / "predictions.parquet"
ROUTING_PARQUET = PROCESSED_DIR / "routing.parquet"

INCIDENTS_PARQUET = PROCESSED_DIR / "incidents.parquet"
LINKS_PARQUET = PROCESSED_DIR / "incident_links.parquet"
REPORT_PATH = PROCESSED_DIR / "fusion_report.json"

SIMILARITY_THRESHOLD = 88
ROLLING_WINDOW_DAYS = 7  # R5: fuse the same incident across up to a week


def fuse():
    preds = pd.read_parquet(PRED_PARQUET, engine="pyarrow")
    routing = pd.read_parquet(ROUTING_PARQUET, engine="pyarrow")

    df = preds.merge(
        routing[["record_id", "owner_function"]],
        on="record_id", how="left",
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    print(f"[fusion] Loaded {len(df)} records")

    incidents = []
    links = []

    # Iterate per (store, category) with a rolling time window so that the
    # same incident reported across multiple days (and channels) fuses once.
    groups = df.groupby(["store_id", "predicted_category"])
    print(f"[fusion] Processing {len(groups)} (store, category) groups with "
          f"{ROLLING_WINDOW_DAYS}-day rolling window...")

    WINDOW = pd.Timedelta(days=ROLLING_WINDOW_DAYS)

    for (store, cat), grp in groups:
        grp = grp.sort_values("timestamp").reset_index(drop=True)
        texts = grp["text_norm"].fillna("").tolist()
        times = grp["timestamp"].tolist()
        n = len(grp)

        cluster_id = [-1] * n
        cluster_anchors = {}   # cluster_id -> (first_ts, last_ts, representative_text)
        next_cluster = 0

        for i in range(n):
            placed = False
            # Try to attach to an existing cluster within the window and similar text
            for cid, (c_first, c_last, c_text) in cluster_anchors.items():
                if (times[i] - c_last) <= WINDOW and                    fuzz.token_set_ratio(texts[i], c_text) >= SIMILARITY_THRESHOLD:
                    cluster_id[i] = cid
                    cluster_anchors[cid] = (c_first, times[i], c_text)
                    placed = True
                    break
            if not placed:
                cluster_id[i] = next_cluster
                cluster_anchors[next_cluster] = (times[i], times[i], texts[i])
                next_cluster += 1

        for cid in range(next_cluster):
            member_idx = [k for k, c in enumerate(cluster_id) if c == cid]
            member_records = grp.iloc[member_idx]
            incident_id = f"INC-{uuid.uuid4().hex[:12].upper()}"

            first_ts = member_records["timestamp"].min()
            last_ts = member_records["timestamp"].max()

            # Severity = worst severity in cluster
            sev_rank = {"critical": 0, "review_required": 1, "high": 2, "medium": 3, "low": 4}
            worst_sev = min(
                member_records["severity"].tolist(),
                key=lambda s: sev_rank.get(s, 9),
            )

            incidents.append({
                "incident_id": incident_id,
                "store_id": store,
                "predicted_category": cat,
                "owner_function": member_records["owner_function"].iloc[0],
                "severity": worst_sev,
                "first_seen": first_ts,
                "last_seen": last_ts,
                "record_count": len(member_records),
                "channels": "|".join(sorted(set(member_records["channel"].tolist()))),
                "sample_text": texts[member_idx[0]][:240],
                "verification_status": "suspected",
            })

            for _, rec in member_records.iterrows():
                links.append({
                    "incident_id": incident_id,
                    "record_id": rec["record_id"],
                    "channel": rec["channel"],
                    "match_reason": "same_store_category_window",
                })

    incidents_df = pd.DataFrame(incidents)
    links_df = pd.DataFrame(links)

    # Merge externally-recorded verifications (from API review calls)
    verif_path = REPORTS_DIR.parent / "incident_verifications.jsonl"
    if verif_path.exists():
        latest = {}
        with open(verif_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    v = json.loads(line)
                except json.JSONDecodeError:
                    continue
                latest[v["incident_id"]] = v.get("status", "suspected")
        if latest:
            incidents_df["verification_status"] = (
                incidents_df["incident_id"]
                .map(latest)
                .fillna(incidents_df.get("verification_status", "suspected"))
            )
            print(f"[fusion] Applied {len(latest)} external verification(s)")

    incidents_df.to_parquet(INCIDENTS_PARQUET, engine="pyarrow", index=False)
    links_df.to_parquet(LINKS_PARQUET, engine="pyarrow", index=False)
    print(f"[fusion] Wrote {len(incidents_df)} incidents -> {INCIDENTS_PARQUET}")
    print(f"[fusion] Wrote {len(links_df)} links     -> {LINKS_PARQUET}")

    # Compression ratio
    total_records = len(df)
    total_incidents = len(incidents_df)
    compression = 1.0 - (total_incidents / max(total_records, 1))

    multi = incidents_df[incidents_df["record_count"] > 1]
    channel_fused = incidents_df[incidents_df["channels"].str.contains(r"\|")]
    cross_channel = int(len(channel_fused))

    report = {
        "total_records": total_records,
        "total_incidents": total_incidents,
        "compression_ratio": round(compression, 4),
        "multi_record_incidents": int(len(multi)),
        "cross_channel_incidents": cross_channel,
        "top_incidents_by_size": (
            incidents_df.sort_values("record_count", ascending=False)
            .head(10)
            .assign(
                first_seen=lambda d: d["first_seen"].astype(str),
                last_seen=lambda d: d["last_seen"].astype(str),
            )
            .to_dict(orient="records")
        ),
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[fusion] Wrote report -> {REPORT_PATH}")

    print("")
    print("[fusion] SUMMARY")
    print(f"  Total records              : {report['total_records']}")
    print(f"  Total incidents            : {report['total_incidents']}")
    print(f"  Compression ratio          : {report['compression_ratio']}")
    print(f"  Multi-record incidents     : {report['multi_record_incidents']}")
    print(f"  Cross-channel incidents    : {report['cross_channel_incidents']}")


if __name__ == "__main__":
    fuse()

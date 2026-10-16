"""
StoreSignal AI - Regional Weekly Briefs
========================================
Generates one-page weekly briefs per region, prioritized by risk/trend
(not raw count alone), including:
  - Top 5 issues
  - Evidence quotes
  - Affected stores
  - Trend arrow vs previous week
  - Owner and next action
"""

import json
from pathlib import Path

import pandas as pd

HOME = Path.home()
ROOT = HOME / "storesignal-ai"
PRED_PARQUET = ROOT / "data" / "processed" / "predictions.parquet"
ROUTING_PARQUET = ROOT / "data" / "processed" / "routing.parquet"
ALERTS_PARQUET = ROOT / "data" / "processed" / "alerts.parquet"
STORE_CSV = ROOT / "data" / "reference" / "store_master.csv"

OUT_DIR = ROOT / "data" / "processed" / "briefs"
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = ROOT / "data" / "processed" / "briefs_report.json"

SEV_RANK = {"critical": 4, "review_required": 4, "high": 3, "medium": 2, "low": 1}
WEEK_START_OVERRIDE = None  # None = use most recent 7 days in data


def _arrow(current, previous):
    if previous == 0:
        return "NEW" if current > 0 else "FLAT"
    ratio = current / previous
    if ratio >= 1.25:
        return "UP"
    if ratio <= 0.80:
        return "DOWN"
    return "FLAT"


def build():
    preds = pd.read_parquet(PRED_PARQUET, engine="pyarrow")
    routing = pd.read_parquet(ROUTING_PARQUET, engine="pyarrow")
    alerts = pd.read_parquet(ALERTS_PARQUET, engine="pyarrow")
    stores = pd.read_csv(STORE_CSV)

    df = preds.merge(
        routing[["record_id", "owner_function", "next_action", "escalation_rule"]],
        on="record_id", how="left",
    ).merge(
        stores[["store_id", "region_id", "region_name"]],
        on="store_id", how="left",
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    if WEEK_START_OVERRIDE is None:
        max_ts = df["timestamp"].max()
        week_end = max_ts.normalize() + pd.Timedelta(days=1)
        week_start = week_end - pd.Timedelta(days=7)
        prev_start = week_start - pd.Timedelta(days=7)
    else:
        week_start = pd.Timestamp(WEEK_START_OVERRIDE, tz="UTC")
        week_end = week_start + pd.Timedelta(days=7)
        prev_start = week_start - pd.Timedelta(days=7)

    print(f"[briefs] Week window: {week_start.date()} -> {week_end.date()}")
    print(f"[briefs] Prev window: {prev_start.date()} -> {week_start.date()}")

    current = df[(df["timestamp"] >= week_start) & (df["timestamp"] < week_end)].copy()
    previous = df[(df["timestamp"] >= prev_start) & (df["timestamp"] < week_start)].copy()

    print(f"[briefs] Current week rows: {len(current)} | Previous week rows: {len(previous)}")

    brief_index = []

    for region_id, region_name in stores[["region_id", "region_name"]].drop_duplicates().itertuples(index=False):
        cur_r = current[current["region_id"] == region_id]
        prev_r = previous[previous["region_id"] == region_id]

        if len(cur_r) == 0 and len(prev_r) == 0:
            continue

        # Aggregate by category
        cur_counts = cur_r.groupby("predicted_category").size().to_dict()
        prev_counts = prev_r.groupby("predicted_category").size().to_dict()

        # Aggregate severity per category (max)
        sev_by_cat = cur_r.groupby("predicted_category")["severity"].apply(
            lambda s: max(s, key=lambda x: SEV_RANK.get(x, 0))
        ).to_dict()

        owner_by_cat = cur_r.groupby("predicted_category")["owner_function"].agg(
            lambda s: s.mode().iloc[0] if len(s.mode()) else "Store Ops"
        ).to_dict()

        next_action_by_cat = cur_r.groupby("predicted_category")["next_action"].agg(
            lambda s: s.mode().iloc[0] if len(s.mode()) else ""
        ).to_dict()

        escalation_rule_by_cat = cur_r.groupby("predicted_category")["escalation_rule"].agg(
            lambda s: s.mode().iloc[0] if len(s.mode()) else "routine_review"
        ).to_dict()

        # Build candidate issue list with priority = severity_rank * 10 + count + trend_bonus
        rows = []
        for cat, cur_n in cur_counts.items():
            prev_n = prev_counts.get(cat, 0)
            arrow = _arrow(cur_n, prev_n)
            sev = sev_by_cat.get(cat, "medium")
            sev_r = SEV_RANK.get(sev, 1)
            trend_bonus = 3 if arrow == "UP" else (1 if arrow == "NEW" else 0)
            priority = sev_r * 10 + trend_bonus * 2 + min(cur_n, 20) / 20.0
            rows.append({
                "category": cat,
                "current_count": int(cur_n),
                "previous_count": int(prev_n),
                "trend": arrow,
                "severity": sev,
                "owner_function": owner_by_cat.get(cat, "Store Ops"),
                "next_action": next_action_by_cat.get(cat, ""),
                "escalation_rule": escalation_rule_by_cat.get(cat, "routine_review"),
                "priority": round(float(priority), 4),
            })

        top5 = sorted(rows, key=lambda r: r["priority"], reverse=True)[:5]

        # Attach affected stores and evidence quotes
        for issue in top5:
            cat = issue["category"]
            store_subset = (
                cur_r[cur_r["predicted_category"] == cat]
                .groupby("store_id")
                .size()
                .sort_values(ascending=False)
                .head(5)
            )
            issue["affected_stores"] = [
                {"store_id": sid, "count": int(n)}
                for sid, n in store_subset.items()
            ]
            issue["evidence_quotes"] = (
                cur_r[cur_r["predicted_category"] == cat]["text_norm"]
                .dropna().astype(str).head(3).tolist()
            )

        # Region-level escalated alerts in this window
        region_stores = set(stores[stores["region_id"] == region_id]["store_id"].tolist())
        region_alerts = alerts[alerts["store_id"].isin(region_stores)] if len(alerts) else alerts

        brief = {
            "region_id": region_id,
            "region_name": region_name,
            "week_start": week_start.date().isoformat(),
            "week_end": (week_end - pd.Timedelta(days=1)).date().isoformat(),
            "total_feedback": int(len(cur_r)),
            "total_feedback_previous_week": int(len(prev_r)),
            "top_issues": top5,
            "region_alert_count": int(len(region_alerts)),
            "data_limitations": (
                "Feedback is unverified; single reports may not indicate systemic issues. "
                "Counts shown are raw, not exposure-normalized."
            ),
        }

        out_path = OUT_DIR / f"brief_{region_id}_{week_start.date().isoformat()}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(brief, f, indent=2, ensure_ascii=False)

        # Also write a Markdown 1-pager
        md_path = OUT_DIR / f"brief_{region_id}_{week_start.date().isoformat()}.md"
        md = []
        md.append(f"# {region_name} Region - Weekly Action Brief")
        md.append(f"**Week**: {brief['week_start']} to {brief['week_end']}")
        md.append("")
        md.append(f"Total feedback this week: **{brief['total_feedback']}** "
                  f"(prev: {brief['total_feedback_previous_week']})")
        md.append(f"Escalated alerts in region: **{brief['region_alert_count']}**")
        md.append("")
        md.append("## Top 5 Prioritized Issues")
        md.append("")
        for i, issue in enumerate(top5, start=1):
            md.append(f"### {i}. {issue['category']} ({issue['severity'].upper()}) — trend {issue['trend']}")
            md.append(f"- Count: **{issue['current_count']}** this week "
                      f"(prev {issue['previous_count']})")
            md.append(f"- Owner: **{issue['owner_function']}**")
            md.append(f"- Escalation rule: `{issue['escalation_rule']}`")
            md.append(f"- Next action: {issue['next_action']}")
            md.append(f"- Affected stores: "
                      f"{', '.join(s['store_id'] + ' (' + str(s['count']) + ')' for s in issue['affected_stores'])}")
            if issue["evidence_quotes"]:
                md.append("- Evidence quotes:")
                for q in issue["evidence_quotes"]:
                    md.append(f"  - “{q}”")
            md.append("")
        md.append(f"> _{brief['data_limitations']}_")
        md_path.write_text("\n".join(md), encoding="utf-8")

        brief_index.append({
            "region_id": region_id,
            "region_name": region_name,
            "week_start": brief["week_start"],
            "total_feedback": brief["total_feedback"],
            "top_issue": top5[0]["category"] if top5 else None,
            "json_path": str(out_path),
            "md_path": str(md_path),
        })

    report = {
        "week_start": week_start.date().isoformat(),
        "week_end": (week_end - pd.Timedelta(days=1)).date().isoformat(),
        "num_regions": len(brief_index),
        "brief_index": brief_index,
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str, ensure_ascii=False)
    print(f"[briefs] Wrote report -> {REPORT_PATH}")

    print("")
    print("[briefs] SUMMARY")
    print(f"  Regions covered: {len(brief_index)}")
    for b in brief_index:
        print(f"    {b['region_id']:10s} {b['region_name']:8s} "
              f"total={b['total_feedback']:5d} top_issue={b['top_issue']}")


if __name__ == "__main__":
    build()

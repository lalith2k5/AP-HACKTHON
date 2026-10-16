"""
StoreSignal AI - Streamlit dashboard
=====================================
Five logical views matching the R5 spec:
  1. Command Center
  2. Early-Warning Radar
  3. Incident Explorer
  4. Regional Action Brief
  5. Model & Trust

All views read the same pipeline Parquet/JSON artifacts.
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

HOME = Path.home()
ROOT = HOME / "storesignal-ai"
PROC = ROOT / "data" / "processed"
REF = ROOT / "data" / "reference"

st.set_page_config(page_title="StoreSignal AI", layout="wide")
st.title("StoreSignal AI — Voice-of-Store Engine")
st.caption("Simulated data. Illustrative metrics only until evaluation passes.")

SIDEBAR = st.sidebar
SIDEBAR.header("Navigation")
view = SIDEBAR.radio("View", [
    "Command Center",
    "Early-Warning Radar",
    "Incident Explorer",
    "Regional Action Brief",
    "Model & Trust",
])


@st.cache_data(show_spinner=False)
def load(name):
    p = PROC / name
    if not p.exists():
        return None
    if p.suffix == ".parquet":
        return pd.read_parquet(p, engine="pyarrow")
    return json.loads(p.read_text())


preds = load("predictions.parquet")
routing = load("routing.parquet")
escalations = load("escalations.parquet")
incidents = load("incidents.parquet")
alerts = load("alerts.parquet")
radar = load("radar_flags.parquet")
stores = pd.read_csv(REF / "store_master.csv") if (REF / "store_master.csv").exists() else None

if preds is None:
    st.error("Pipeline artifacts missing. Run `make pipeline` first.")
    st.stop()

# ---------------------------------------------------------------------------
# View 1 — Command Center
# ---------------------------------------------------------------------------
if view == "Command Center":
    st.header("Command Center")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total records", f"{len(preds):,}")
    c2.metric("Escalations", f"{len(escalations):,}" if escalations is not None else "—")
    c3.metric("Alerts", f"{len(alerts):,}" if alerts is not None else "—")
    c4.metric("Incidents", f"{len(incidents):,}" if incidents is not None else "—")

    st.subheader("Top priority alerts")
    if alerts is not None:
        top = alerts.sort_values("priority", ascending=False).head(15)[[
            "alert_id", "trigger_type", "store_id", "predicted_category",
            "severity", "owner_function", "priority",
        ]]
        st.dataframe(top, width="stretch")

    st.subheader("Recent feedback")
    st.dataframe(
        preds.sort_values("timestamp", ascending=False).head(20)[[
            "record_id", "channel", "store_id", "predicted_category",
            "confidence", "severity", "actionable",
        ]],
        width="stretch",
    )

# ---------------------------------------------------------------------------
# View 2 — Early-Warning Radar
# ---------------------------------------------------------------------------
elif view == "Early-Warning Radar":
    st.header("Early-Warning Radar")
    if radar is None or len(radar) == 0:
        st.info("No radar flags yet. Run storesignal/detection.py.")
    else:
        r = radar.copy()
        r["day"] = pd.to_datetime(r["day"], utc=True)
        stores_flagged = sorted(r["store_id"].unique())
        store_sel = st.selectbox("Store", ["ALL"] + stores_flagged)
        r_view = r if store_sel == "ALL" else r[r["store_id"] == store_sel]

        st.metric("Flagged rows", len(r_view))
        st.metric("Unique (store, category)", r_view[["store_id", "predicted_category"]].drop_duplicates().shape[0])
        st.metric("Max robust z", round(float(r_view["robust_z"].max()), 2))

        st.subheader("Flags")
        st.dataframe(
            r_view.sort_values("robust_z", ascending=False).head(200)[[
                "store_id", "predicted_category", "day", "count",
                "baseline_median", "robust_z", "rate_ratio", "rate_per_10k",
            ]],
            width="stretch",
        )

        st.subheader("Daily flag counts")
        chart = r_view.groupby("day").size().rename("flags").reset_index()
        st.line_chart(chart, x="day", y="flags")

# ---------------------------------------------------------------------------
# View 3 — Incident Explorer
# ---------------------------------------------------------------------------
elif view == "Incident Explorer":
    st.header("Incident Explorer")
    if incidents is None:
        st.info("No incidents yet. Run storesignal/fusion.py.")
    else:
        c1, c2, c3 = st.columns(3)
        cat_sel = c1.selectbox("Category", ["ALL"] + sorted(incidents["predicted_category"].unique()))
        store_sel = c2.selectbox("Store", ["ALL"] + sorted(incidents["store_id"].unique()))
        sev_sel = c3.selectbox("Severity", ["ALL", "critical", "review_required", "high", "medium", "low"])

        view_df = incidents.copy()
        if cat_sel != "ALL": view_df = view_df[view_df["predicted_category"] == cat_sel]
        if store_sel != "ALL": view_df = view_df[view_df["store_id"] == store_sel]
        if sev_sel != "ALL": view_df = view_df[view_df["severity"] == sev_sel]

        st.metric("Incidents matched", len(view_df))
        st.dataframe(
            view_df.sort_values("record_count", ascending=False).head(100)[[
                "incident_id", "store_id", "predicted_category", "severity",
                "owner_function", "record_count", "channels", "first_seen", "last_seen",
            ]],
            width="stretch",
        )

        if len(view_df) > 0:
            st.subheader("Incident detail")
            inc_id = st.selectbox("Select incident", view_df["incident_id"].head(50).tolist())
            row = incidents[incidents["incident_id"] == inc_id].iloc[0]
            st.json(row.to_dict())

# ---------------------------------------------------------------------------
# View 4 — Regional Action Brief
# ---------------------------------------------------------------------------
elif view == "Regional Action Brief":
    st.header("Regional Action Brief")
    briefs_dir = PROC / "briefs"
    if not briefs_dir.exists():
        st.info("No briefs yet. Run storesignal/briefs.py.")
    else:
        files = sorted(briefs_dir.glob("brief_*.json"))
        if not files:
            st.info("No briefs found.")
        else:
            region_ids = sorted({f.name.split("_")[1] for f in files})
            sel = st.selectbox("Region", region_ids)
            match = [f for f in files if f.name.startswith(f"brief_{sel}_")]
            if match:
                data = json.loads(match[-1].read_text())
                st.subheader(f"{data['region_name']} — week {data['week_start']} → {data['week_end']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Total feedback", f"{data['total_feedback']:,}")
                c2.metric("Prev week", f"{data['total_feedback_previous_week']:,}")
                c3.metric("Escalated alerts", data["region_alert_count"])

                st.subheader("Top 5 prioritized issues")
                for i, issue in enumerate(data["top_issues"], start=1):
                    with st.expander(f"{i}. {issue['category']} — {issue['severity']} — trend {issue['trend']}"):
                        st.write(f"**Owner:** {issue['owner_function']}")
                        st.write(f"**Next action:** {issue['next_action']}")
                        st.write(f"**Current count:** {issue['current_count']} (prev {issue['previous_count']})")
                        st.write("**Affected stores:**")
                        st.dataframe(pd.DataFrame(issue["affected_stores"]), width="stretch")
                        st.write("**Evidence quotes:**")
                        for q in issue["evidence_quotes"]:
                            st.markdown(f"> {q}")
                st.caption(data["data_limitations"])

# ---------------------------------------------------------------------------
# View 5 — Model & Trust
# ---------------------------------------------------------------------------
elif view == "Model & Trust":
    st.header("Model & Trust")
    report = load(ROOT / "data" / "evaluation" / "reports" / "evaluation_report.json")
    if not report:
        st.info("Evaluation report not found. Run storesignal/evaluate.py.")
    else:
        cls = report.get("classification", {})
        esc = report.get("escalation", {})
        seed = report.get("seeded_incidents", {})

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Accuracy (hidden)", f"{cls.get('accuracy', 0):.4f}")
        c2.metric("Macro-F1 (hidden)", f"{cls.get('macro_f1', 0):.4f}")
        c3.metric("Escalation precision", f"{esc.get('escalation_precision', 0) or 0:.4f}")
        c4.metric("Seeded detected", f"{seed.get('detected', 0)}/{seed.get('total', 0)}")

        st.metric("Mean lead time (vs peak)", f"{seed.get('mean_lead_days_vs_peak', 0) or 0:.2f} days")

        st.subheader("Seeded incident replay")
        st.dataframe(pd.DataFrame(seed.get("details", [])), width="stretch")

        st.subheader("Per-class F1 (hidden labels)")
        per_class = cls.get("per_class_f1", {})
        if per_class:
            st.dataframe(
                pd.DataFrame([{"category": k, "f1": v} for k, v in per_class.items()])
                .sort_values("f1", ascending=False),
                width="stretch",
            )

        st.caption("Hidden labels are only consumed inside evaluate.py — never for training.")

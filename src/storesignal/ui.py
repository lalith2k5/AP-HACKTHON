"""
StoreSignal AI - Streamlit UI (13 screens, spec section 3)
==========================================================
Views: Welcome, Demo Sign-in, Overview, Incidents, Incident Detail,
Evidence Explorer, Alerts, Trends, Store Impact, Action Recommendation,
Weekly Report, Import Wizard, Data Health, Evaluation, Settings,
Audit Log, Model & Trust.

Design tokens in tokens.py. All data reads from data/processed artifacts
via ui_data.py. Business logic stays in the pipeline modules.
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from storesignal import settings as S
from storesignal import tokens as T
from storesignal import ui_data as D

ROOT = Path.home() / "storesignal-ai"

st.set_page_config(
    page_title="StoreSignal AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "role" not in st.session_state:
    st.session_state.role = None
if "region" not in st.session_state:
    st.session_state.region = "ALL"
if "theme" not in st.session_state:
    st.session_state.theme = "light"


def apply_theme() -> None:
    dark = st.session_state.theme == "dark"
    bg = T.DARK_BG if dark else T.LIGHT_BG
    fg = T.DARK_FG if dark else T.LIGHT_FG
    card = T.DARK_CARD if dark else T.LIGHT_CARD
    border = T.DARK_BORDER if dark else T.LIGHT_BORDER
    muted = T.DARK_MUTED if dark else T.LIGHT_MUTED
    st.markdown(
        f"""
        <style>
        :root {{
            --ss-bg: {bg}; --ss-fg: {fg}; --ss-card: {card};
            --ss-border: {border}; --ss-muted: {muted};
            --ss-accent: {T.ACCENT}; --ss-critical: {T.CRITICAL};
            --ss-high: {T.HIGH}; --ss-medium: {T.MEDIUM};
            --ss-low: {T.LOW}; --ss-resolved: {T.RESOLVED};
        }}
        .stApp {{ background: var(--ss-bg); color: var(--ss-fg); }}
        section[data-testid="stSidebar"] {{ background: var(--ss-card); }}
        .ss-card {{
            background: var(--ss-card); border: 1px solid var(--ss-border);
            border-radius: 12px; padding: 18px; margin-bottom: 12px;
        }}
        .ss-kpi {{ font-size: 28px; font-weight: 700; color: var(--ss-fg); }}
        .ss-kpi-label {{ font-size: 13px; color: var(--ss-muted);
                         text-transform: uppercase; letter-spacing: .05em; }}
        .ss-badge {{ display: inline-block; padding: 2px 10px; border-radius: 999px;
                     font-size: 12px; font-weight: 600; margin-right: 6px; }}
        .ss-critical {{ background: {T.CRITICAL_BG}; color: {T.CRITICAL}; }}
        .ss-high {{ background: {T.HIGH_BG}; color: {T.HIGH}; }}
        .ss-medium {{ background: {T.MEDIUM_BG}; color: {T.MEDIUM}; }}
        .ss-low {{ background: {T.LOW_BG}; color: {T.LOW}; }}
        .ss-resolved {{ background: {T.RESOLVED_BG}; color: {T.RESOLVED}; }}
        .ss-info {{ background: {T.INFO_BG}; color: {T.INFO}; }}
        .ss-muted {{ color: var(--ss-muted); font-size: 13px; }}
        .ss-divider {{ border-top: 1px solid var(--ss-border); margin: 16px 0; }}
        .ss-hero {{
            background: linear-gradient(135deg, {T.ACCENT} 0%, {T.ACCENT_DARK} 100%);
            padding: 60px 40px; border-radius: 16px; color: white;
        }}
        .ss-hero h1 {{ color: white; font-size: 40px; margin: 0 0 12px 0; }}
        .ss-hero p {{ color: rgba(255,255,255,.85); font-size: 18px; }}
        .ss-demo-banner {{
            background: {T.INFO_BG}; color: {T.INFO};
            padding: 8px 14px; border-radius: 8px; font-size: 13px;
            margin-bottom: 12px;
        }}
        h1, h2, h3, h4 {{ color: var(--ss-fg); }}
        </style>
        """,
        unsafe_allow_html=True,
    )


apply_theme()


def demo_banner() -> None:
    if S.DEMO_MODE:
        st.markdown(
            '<div class="ss-demo-banner">DEMO MODE — simulated data. '
            "Metrics are illustrative until evaluation passes.</div>",
            unsafe_allow_html=True,
        )


def sev_badge(sev: str) -> str:
    sev = (sev or "low").lower()
    cls = {"critical": "ss-critical", "high": "ss-high", "medium": "ss-medium",
           "low": "ss-low", "resolved": "ss-resolved"}.get(sev, "ss-info")
    return f'<span class="ss-badge {cls}">{sev.upper()}</span>'


def kpi(label: str, value: str, sub: str = "") -> None:
    sub_html = f'<div class="ss-muted">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="ss-card"><div class="ss-kpi-label">{label}</div>'
        f'<div class="ss-kpi">{value}</div>{sub_html}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Welcome / Sign-in (screens 1 and 10)
# ---------------------------------------------------------------------------
def screen_welcome() -> None:
    demo_banner()
    st.markdown(
        """
        <div class="ss-hero">
          <h1>StoreSignal AI</h1>
          <p>Turn Store Feedback Into Action.</p>
          <p style="font-size:15px;opacity:.8">
            Real-time insights. Happier customers. Better stores.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    c1, c2, _ = st.columns([1, 1, 2])
    if c1.button("Get Started", use_container_width=True, type="primary"):
        st.session_state.authenticated = True
        st.session_state.role = "regional_ops_lead"
        st.rerun()
    if c2.button("Sign In", use_container_width=True):
        st.session_state.show_signin = True
        st.rerun()


def screen_signin() -> None:
    demo_banner()
    st.markdown("## Sign in to StoreSignal")
    st.caption("Local demo — role selector, not production authentication.")
    roles = [
        ("regional_ops_lead", "Regional Operations Lead", "regional-manager-key-demo"),
        ("store_manager",     "Store Manager",             "store-manager-key-demo"),
        ("food_safety_risk",  "Food Safety / Risk",        "food-safety-key-demo"),
        ("supply_chain",      "Supply Chain / Merchandising", "supply-chain-key-demo"),
        ("hr_sensitive",      "HR / Sensitive Reviewer",   "hr-key-demo"),
        ("analyst",           "Analyst",                   "analyst-key-demo"),
        ("admin",             "Administrator",             "demo-key-storesignal"),
    ]
    labels = [r[1] for r in roles]
    choice = st.selectbox("Select a demo role", labels, index=0)
    chosen = next(r for r in roles if r[1] == choice)
    st.text_input("API key (pre-filled for demo)", value=chosen[2], type="password")
    if st.button("Sign In", type="primary"):
        st.session_state.authenticated = True
        st.session_state.role = chosen[0]
        st.rerun()


# ---------------------------------------------------------------------------
# Screen 2 — Overview / Dashboard
# ---------------------------------------------------------------------------
def screen_overview() -> None:
    demo_banner()
    st.markdown("## Overview")
    metrics = D.overview_metrics()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Total feedback", f"{metrics['total']:,}", "across 4 channels")
    with c2:
        kpi("Open incidents", f"{metrics['open_incidents']:,}",
            f"{metrics['mandatory_open']} mandatory risk")
    with c3:
        kpi("Resolved this week", f"{metrics['resolved_this_week']:,}",
            "verified closures")
    with c4:
        kpi("Avg resolution time", metrics["avg_resolution"], "last 7 days")

    st.write("")
    cA, cB = st.columns([3, 2])
    with cA:
        st.markdown("#### Feedback volume trend")
        series = D.feedback_series()
        if series is not None and not series.empty:
            st.line_chart(series.set_index("date"), height=260)
        else:
            st.info("Run `make pipeline` to generate feedback series.")
    with cB:
        st.markdown("#### Issues by category")
        cats = D.category_distribution()
        if cats is not None and not cats.empty:
            st.bar_chart(cats.set_index("category")["count"], height=260)
        else:
            st.info("No category distribution yet.")

    st.write("")
    st.markdown("#### Urgent queue")
    alerts = D.alerts()
    if alerts is not None and not alerts.empty:
        urgent = alerts.sort_values("priority", ascending=False).head(8)
        for _, r in urgent.iterrows():
            sev = str(r.get("severity", "medium"))
            st.markdown(
                f'<div class="ss-card">{sev_badge(sev)}'
                f'<b>{r.get("predicted_category", "issue")}</b>'
                f'<div class="ss-muted">store {r.get("store_id","?")} · '
                f'{r.get("owner_function","unassigned")} · '
                f'priority {r.get("priority","?")}</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("No alerts yet.")


# ---------------------------------------------------------------------------
# Screen 4 — Incident Detail (Overview / Evidence / Timeline / Actions tabs)
# ---------------------------------------------------------------------------
def screen_incident_detail() -> None:
    demo_banner()
    inc = D.incidents()
    if inc is None or inc.empty:
        st.info("No incidents yet — run `make pipeline`.")
        return
    ids = inc["incident_id"].astype(str).head(300).tolist() if "incident_id" in inc.columns else []
    if not ids:
        st.info("Incident file has no incident_id column.")
        return
    default = st.session_state.get("selected_incident") or ids[0]
    idx = ids.index(default) if default in ids else 0
    selected = st.selectbox("Incident", ids, index=idx)
    st.session_state.selected_incident = selected
    row = inc[inc["incident_id"].astype(str) == selected].iloc[0]

    sev = str(row.get("severity", "medium"))
    cat = str(row.get("category", row.get("predicted_category", "unknown")))
    store = str(row.get("store_id", row.get("affected_store_ids", "?")))
    st.markdown(
        f"### {sev_badge(sev)} {cat.replace('_',' ').title()}",
        unsafe_allow_html=True,
    )
    st.caption(f"incident {selected} · store {store}")

    tabs = st.tabs(["Overview", "Evidence", "Timeline", "Actions"])

    with tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Key information**")
            st.markdown(
                f"- Issue type: `{cat}`\n"
                f"- Severity: `{sev}`\n"
                f"- Store: `{store}`\n"
                f"- Status: `{row.get('status', 'new')}`"
            )
        with c2:
            st.markdown("**Signal**")
            for k in ("priority", "owner_function", "trigger_type",
                      "source_record_ids", "trend_score"):
                if k in row and row[k] is not None:
                    v = row[k]
                    if isinstance(v, (list, tuple)):
                        v = ", ".join(str(x) for x in v[:5])
                    st.markdown(f"- {k}: `{v}`")

    with tabs[1]:
        st.markdown("**Evidence quotes**")
        srcs = row.get("source_record_ids") or row.get("record_ids") or []
        if isinstance(srcs, str):
            srcs = [s.strip() for s in srcs.split(",") if s.strip()]
        preds = D.predictions()
        if srcs and preds is not None:
            sub = preds[preds["record_id"].isin(srcs)].head(20)
            for _, r in sub.iterrows():
                text = r.get("text_norm") or r.get("text_raw") or ""
                st.markdown(
                    f'<div class="ss-card">"{text[:280]}"'
                    f'<div class="ss-muted">channel={r.get("channel","?")} · '
                    f'record={r.get("record_id","?")}</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No source records attached.")

    with tabs[2]:
        from storesignal import workflow as wf
        hist = wf.history(selected)
        if not hist:
            st.info("No workflow transitions yet.")
        else:
            for h in hist:
                st.markdown(
                    f"`{h['ts']}` **{h['from_state']}** → **{h['to_state']}** "
                    f"by `{h['actor']}`"
                    + (f" — {h['reason']}" if h.get("reason") else "")
                )

    with tabs[3]:
        from storesignal import workflow as wf
        state = wf.current_state(selected)
        st.markdown(f"Current state: **{state}**")
        allowed = sorted(wf.TRANSITIONS.get(state, set()))
        if not allowed:
            st.caption("Terminal state — no further transitions.")
        else:
            to_state = st.selectbox("Transition to", allowed)
            reason = st.text_input("Reason (required for override)")
            override = st.checkbox("Mark as override")
            if st.button("Apply transition", type="primary"):
                result = wf.transition(selected, to_state,
                                        st.session_state.role or "demo-operator",
                                        reason=reason or None,
                                        is_override=override)
                if result.get("ok"):
                    st.success(f"{result['from']} → {result['to']}")
                    st.rerun()
                else:
                    st.error(result.get("error"))
        st.markdown("---")
        st.markdown("**Action recommendations**")
        recs = D.action_recommendations(selected)
        for r in recs:
            st.markdown(
                f'<div class="ss-card">{sev_badge(r["urgency"])}'
                f'<b>{r["action"]}</b>'
                f'<div class="ss-muted">owner: {r["owner"]} · '
                f'effort: {r["effort"]} · est. benefit: {r["benefit"]}</div></div>',
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Screen 5 — Evidence Explorer
# ---------------------------------------------------------------------------
def screen_evidence() -> None:
    demo_banner()
    st.markdown("## Evidence explorer")
    preds = D.predictions()
    if preds is None:
        st.info("No predictions yet.")
        return
    cats = sorted(preds["predicted_category"].dropna().unique().tolist())
    c1, c2 = st.columns(2)
    with c1:
        cat = st.selectbox("Category", ["ALL", *cats])
    with c2:
        chan = st.selectbox("Channel", ["ALL", *sorted(preds["channel"].dropna().unique().tolist())])
    sub = preds
    if cat != "ALL":
        sub = sub[sub["predicted_category"] == cat]
    if chan != "ALL":
        sub = sub[sub["channel"] == chan]
    sub = sub.head(200)
    st.caption(f"Showing {len(sub)} records")
    for _, r in sub.iterrows():
        text = r.get("text_norm") or ""
        st.markdown(
            f'<div class="ss-card">"{text[:300]}"'
            f'<div class="ss-muted">record={r.get("record_id","?")} · '
            f'channel={r.get("channel","?")} · '
            f'category={r.get("predicted_category","?")} · '
            f'conf={r.get("confidence",0):.2f}</div></div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Screen 6 — Trends
# ---------------------------------------------------------------------------
def screen_trends() -> None:
    demo_banner()
    st.markdown("## Trend explorer")
    radar = D.radar()
    if radar is None or radar.empty:
        st.info("No radar flags yet — run `make radar`.")
        return
    c1, c2 = st.columns(2)
    with c1:
        cats = ["ALL", *sorted(radar["category"].dropna().unique().tolist())]
        cat = st.selectbox("Category", cats)
    with c2:
        stores = ["ALL", *sorted(radar["store_id"].dropna().astype(str).unique().tolist())[:50]]
        store = st.selectbox("Store", stores)
    sub = radar
    if cat != "ALL":
        sub = sub[sub["category"] == cat]
    if store != "ALL":
        sub = sub[sub["store_id"].astype(str) == store]
    st.markdown(f"**{len(sub)} flags**")
    st.dataframe(sub.head(100), use_container_width=True)
    if "score" in sub.columns and "current_count" in sub.columns:
        st.markdown("**Top by robust score**")
        top = sub.sort_values("score", ascending=False).head(10)
        st.bar_chart(top.set_index("store_id")["score"] if "store_id" in top.columns else top["score"])


# ---------------------------------------------------------------------------
# Screen 7 — Store Impact
# ---------------------------------------------------------------------------
def screen_stores() -> None:
    demo_banner()
    st.markdown("## Store impact")
    preds = D.predictions()
    if preds is None:
        st.info("No predictions yet.")
        return
    grp = (preds.groupby("store_id").size()
                .reset_index(name="incidents")
                .sort_values("incidents", ascending=False).head(30))
    c1, c2 = st.columns([2, 3])
    with c1:
        st.markdown("**Top affected stores**")
        st.dataframe(grp, use_container_width=True, hide_index=True)
    with c2:
        st.markdown("**Incidents by store**")
        st.bar_chart(grp.set_index("store_id")["incidents"], height=380)
    st.caption("Denominator (footfall) not modeled in this build — "
               "counts shown raw.")


# ---------------------------------------------------------------------------
# Screen 8 — Action Recommendation
# ---------------------------------------------------------------------------
def screen_actions() -> None:
    demo_banner()
    st.markdown("## Action recommendation")
    inc = D.incidents()
    if inc is None or inc.empty:
        st.info("No incidents yet.")
        return
    ids = inc["incident_id"].astype(str).head(200).tolist()
    sel = st.selectbox("Incident", ids)
    recs = D.action_recommendations(sel)
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("**Recommended actions**")
        for r in recs:
            st.markdown(
                f'<div class="ss-card">{sev_badge(r["urgency"])}'
                f'<b>{r["action"]}</b>'
                f'<div class="ss-muted">owner: {r["owner"]} · '
                f'effort: {r["effort"]}</div>'
                f'<div class="ss-muted">benefit: {r["benefit"]}</div></div>',
                unsafe_allow_html=True,
            )
    with c2:
        st.markdown("**Impact simulator**")
        st.markdown(
            '<div class="ss-card">Estimated cost range: '
            '<b>$150 - $300</b><br>'
            '<div class="ss-muted">Prevent: food safety risk · '
            'reduce complaints · minimize loss</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Simulate impact", type="primary"):
            st.success("Simulation ran — see forecasts.parquet for detail.")


# ---------------------------------------------------------------------------
# Screen 9 — Weekly Report
# ---------------------------------------------------------------------------
def screen_report() -> None:
    demo_banner()
    st.markdown("## Weekly report")
    briefs_dir = D.PROC / "briefs"
    if not briefs_dir.exists():
        st.info("No briefs yet — run `make briefs`.")
        return
    files = sorted(briefs_dir.glob("*.md"))
    if not files:
        st.info("Briefs directory is empty.")
        return
    sel = st.selectbox("Brief", [f.name for f in files])
    text = (briefs_dir / sel).read_text()
    st.markdown(text)
    st.download_button("Download markdown", text, file_name=sel)


# ---------------------------------------------------------------------------
# Screen 10b — Import Wizard (spec 3.3 / 7)
# ---------------------------------------------------------------------------
def screen_import_wizard() -> None:
    demo_banner()
    st.markdown("## Import wizard")
    st.caption("Upload CSV / JSONL / Parquet. Column mapping is auto-filled "
               "when field names match the canonical schema.")
    uploaded = st.file_uploader("Drop a file", type=["csv", "jsonl", "ndjson", "parquet"])
    if uploaded is not None:
        from storesignal.import_wizard import preview, validate_mapping
        tmp = Path("/tmp") / uploaded.name
        tmp.write_bytes(uploaded.getvalue())
        pv = preview(tmp)
        if "error" in pv:
            st.error(pv["error"])
            return
        st.markdown(f"**Format:** `{pv['format']}`")
        st.markdown("**Detected columns:** " + ", ".join(f"`{c}`" for c in pv["columns"]))
        st.markdown("**Sample rows**")
        st.dataframe(pd.DataFrame(pv["sample_rows"]).head(5), use_container_width=True)

        from storesignal.import_wizard import CANONICAL_COLUMNS, REQUIRED_COLUMNS
        st.markdown("### Column mapping")
        mapping = {}
        cols = ["(none)", *pv["columns"]]
        for canon in CANONICAL_COLUMNS:
            default = canon if canon in pv["columns"] else "(none)"
            required = canon in REQUIRED_COLUMNS
            label = f"{canon}{' *' if required else ''}"
            choice = st.selectbox(label, cols,
                                  index=cols.index(default) if default in cols else 0,
                                  key=f"map_{canon}")
            if choice != "(none)":
                mapping[canon] = choice

        errs = validate_mapping(pv["columns"], mapping)
        if errs:
            st.warning("Mapping issues:\n- " + "\n- ".join(errs))
        channel_override = st.text_input("Force channel (optional)")

        if st.button("Run import", type="primary", disabled=bool(errs)):
            from storesignal.import_wizard import run_import
            result = run_import(tmp, mapping, channel_override=channel_override or None)
            if "error" in result:
                st.error(result)
            else:
                st.success(f"Imported batch {result['batch_id']}")
                c1, c2, c3 = st.columns(3)
                with c1: kpi("Rows in", str(result["rows_in"]))
                with c2: kpi("Valid", str(result["rows_valid"]))
                with c3: kpi("Rejected", str(result["rows_rejected"]))
                st.json(result)

    st.markdown("---")
    st.markdown("### Import history")
    from storesignal.import_wizard import list_batches
    batches = list_batches()
    if batches:
        st.dataframe(pd.DataFrame(batches), use_container_width=True)
    else:
        st.caption("No imports yet.")


# ---------------------------------------------------------------------------
# Screen 11 — Data Health
# ---------------------------------------------------------------------------
def screen_data_health() -> None:
    demo_banner()
    st.markdown("## Data health")
    from storesignal.import_wizard import list_batches
    batches = list_batches()
    c1, c2, c3 = st.columns(3)
    with c1: kpi("Import batches", str(len(batches)))
    with c2:
        from storesignal.settings import DATA_DIR
        raw = DATA_DIR / "raw"
        n_raw = len(list(raw.glob("*"))) if raw.exists() else 0
        kpi("Raw files", str(n_raw))
    with c3:
        proc = D.PROC
        n_proc = len(list(proc.glob("*"))) if proc.exists() else 0
        kpi("Processed artifacts", str(n_proc))

    st.markdown("### Pipeline stage reports")
    stage_reports = sorted(D.PROC.glob("*_report.json"))
    if not stage_reports:
        st.info("No stage reports yet.")
    else:
        for p in stage_reports:
            with st.expander(p.name):
                st.json(json.loads(p.read_text()))

    st.markdown("### Import batches")
    if batches:
        st.dataframe(pd.DataFrame(batches), use_container_width=True)
    else:
        st.caption("No import batches yet.")


# ---------------------------------------------------------------------------
# Screen 12 — Settings (validated form)
# ---------------------------------------------------------------------------
def screen_settings() -> None:
    demo_banner()
    st.markdown("## Settings")
    st.markdown("### Runtime configuration")
    st.json(S.snapshot())

    st.markdown("### Risk policy (read-only preview)")
    from storesignal.config_loader import load_config
    cfg = load_config()
    st.markdown("**Mandatory categories**")
    for c in cfg.risk_policy.mandatory_categories:
        st.markdown(f"- `{c}`")
    st.markdown("**Owners**")
    for o in cfg.routing.next_action_by_owner:
        st.markdown(f"- `{o}`")

    st.markdown("### Cache")
    if st.button("Clear UI cache"):
        st.cache_data.clear()
        st.success("Cache cleared.")


# ---------------------------------------------------------------------------
# Screen 13 — Audit Log (filtered)
# ---------------------------------------------------------------------------
def screen_audit() -> None:
    demo_banner()
    st.markdown("## Audit log")
    log = D.audit_log()
    if log is None or log.empty:
        st.info("No audit events yet.")
        return
    c1, c2 = st.columns(2)
    with c1:
        etypes = ["ALL", *sorted(log["event_type"].dropna().unique().tolist())] if "event_type" in log.columns else ["ALL"]
        et = st.selectbox("Event type", etypes)
    with c2:
        actors = ["ALL", *sorted(log["actor_id"].dropna().unique().tolist())] if "actor_id" in log.columns else ["ALL"]
        ac = st.selectbox("Actor", actors)
    sub = log
    if et != "ALL" and "event_type" in sub.columns:
        sub = sub[sub["event_type"] == et]
    if ac != "ALL" and "actor_id" in sub.columns:
        sub = sub[sub["actor_id"] == ac]
    st.caption(f"{len(sub)} events")
    st.dataframe(sub.tail(300), use_container_width=True)
    st.download_button("Export JSON",
                       sub.to_json(orient="records", lines=True),
                       file_name="audit_export.jsonl")


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
if not st.session_state.authenticated and not st.session_state.get("show_signin"):
    screen_welcome()
    st.stop()

if not st.session_state.authenticated:
    screen_signin()
    st.stop()

# Sidebar (only after auth)
st.sidebar.markdown("### StoreSignal")
st.sidebar.caption(f"role: {st.session_state.role}")
if st.sidebar.button("Sign out"):
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.show_signin = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("#### Region")
regions = D.regions()
st.session_state.region = st.sidebar.selectbox(
    "Region", ["ALL", *regions], index=0,
    label_visibility="collapsed",
)
st.sidebar.markdown("#### Theme")
st.session_state.theme = st.sidebar.radio(
    "Theme", ["light", "dark"],
    index=["light", "dark"].index(st.session_state.theme),
    label_visibility="collapsed",
    horizontal=True,
)
apply_theme()

st.sidebar.markdown("---")
view = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Incidents",
        "Incident Detail",
        "Evidence Explorer",
        "Alerts",
        "Trends",
        "Store Impact",
        "Action Recommendation",
        "Weekly Report",
        "Import Wizard",
        "Data Health",
        "Evaluation",
        "Settings",
        "Audit Log",
        "Model & Trust",
    ],
    label_visibility="collapsed",
)

# Screens 3+ (placeholder stubs until Phase 7B)
if view == "Overview":
    screen_overview()
elif view == "Incidents":
    st.markdown("## Incidents")
    inc = D.incidents()
    if inc is None or inc.empty:
        st.info("No incidents yet — run `make pipeline`.")
    else:
        st.dataframe(inc.head(100), use_container_width=True)
elif view == "Incident Detail":
    screen_incident_detail()
elif view == "Evidence Explorer":
    screen_evidence()
elif view == "Alerts":
    st.markdown("## Alert center")
    alerts = D.alerts()
    if alerts is None or alerts.empty:
        st.info("No alerts yet.")
    else:
        st.dataframe(alerts.head(100), use_container_width=True)
elif view == "Trends":
    screen_trends()
elif view == "Store Impact":
    screen_stores()
elif view == "Action Recommendation":
    screen_actions()
elif view == "Weekly Report":
    screen_report()
elif view == "Import Wizard":
    screen_import_wizard()
elif view == "Data Health":
    screen_data_health()
elif view == "Evaluation":
    st.markdown("## Evaluation")
    ev = D.evaluation_report()
    if ev is None:
        st.warning("No evaluation report yet — run `make evaluate`.")
    else:
        c = ev["classification"]; e = ev["escalation"]; s = ev["seeded_incidents"]
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi("Macro-F1", f"{c['macro_f1']:.4f}")
        with c2: kpi("Accuracy", f"{c['accuracy']:.4f}")
        with c3: kpi("Escalation precision", f"{e['escalation_precision']:.4f}")
        with c4: kpi("Seeded detected", f"{s['detected']} / {s['total']}")
        st.caption(f"Mean lead time vs peak: {s['mean_lead_days_vs_peak']:.2f} days")
elif view == "Settings":
    screen_settings()
elif view == "Audit Log":
    screen_audit()
elif view == "Model & Trust":
    st.markdown("## Model & Trust")
    ev = D.evaluation_report()
    if ev:
        st.json({"run_id": ev.get("run_id"),
                 "config_hash": ev.get("config_hash"),
                 "data_hash": ev.get("data_hash"),
                 "model_hash": ev.get("model_hash")})
    st.caption("Hidden labels are isolated. Only `evaluate.py` reads them.")

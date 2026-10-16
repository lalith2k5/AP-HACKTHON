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
from storesignal import ui_data as D
from storesignal import tokens as T

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
        f"""
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
    st.info("Pick an incident from the Incidents list (Phase 7B).")
elif view == "Evidence Explorer":
    st.info("Evidence explorer (Phase 7B).")
elif view == "Alerts":
    st.markdown("## Alert center")
    alerts = D.alerts()
    if alerts is None or alerts.empty:
        st.info("No alerts yet.")
    else:
        st.dataframe(alerts.head(100), use_container_width=True)
elif view == "Trends":
    st.info("Trend explorer (Phase 7B).")
elif view == "Store Impact":
    st.info("Store impact (Phase 7B).")
elif view == "Action Recommendation":
    st.info("Action recommendations (Phase 7B).")
elif view == "Weekly Report":
    st.markdown("## Weekly report")
    st.info("Generate a brief from the CLI (`make briefs`) or the Reports API.")
elif view == "Import Wizard":
    st.markdown("## Import wizard")
    st.info("Run `make import-data FILE=path.csv` from the CLI, "
            "or POST to `/api/v1/ingest`. UI upload arrives in Phase 7C.")
elif view == "Data Health":
    st.info("Data health (Phase 7C).")
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
    st.markdown("## Settings")
    st.json(S.snapshot())
elif view == "Audit Log":
    st.markdown("## Audit log")
    log = D.audit_log()
    if log is None or log.empty:
        st.info("No audit events yet.")
    else:
        st.dataframe(log.tail(200), use_container_width=True)
elif view == "Model & Trust":
    st.markdown("## Model & Trust")
    ev = D.evaluation_report()
    if ev:
        st.json({"run_id": ev.get("run_id"),
                 "config_hash": ev.get("config_hash"),
                 "data_hash": ev.get("data_hash"),
                 "model_hash": ev.get("model_hash")})
    st.caption("Hidden labels are isolated. Only `evaluate.py` reads them.")

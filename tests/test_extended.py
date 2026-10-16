"""
StoreSignal AI — extended coverage for security, roles, idempotency,
verification status, and the new evaluation metrics.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path.home() / "storesignal-ai"
PROC = ROOT / "data" / "processed"

MANDATORY = {"safety_hazard", "allergen_or_labeling",
             "food_safety_or_hygiene", "staff_misconduct"}


def test_regions_entity_exists():
    p = PROC / "regions.parquet"
    assert p.exists(), "regions.parquet not exported"
    df = pd.read_parquet(p)
    assert {"region_id", "region_name"} <= set(df.columns)
    assert len(df) >= 1


def test_routing_rules_entity_exists():
    p = PROC / "routing_rules.parquet"
    assert p.exists(), "routing_rules.parquet not exported"
    df = pd.read_parquet(p)
    required = {"rule_id", "category_id", "owner_function",
                "severity", "sla_hours", "next_action"}
    assert required <= set(df.columns)
    assert len(df) >= 32


def test_incidents_have_verification_status():
    p = PROC / "incidents.parquet"
    df = pd.read_parquet(p)
    assert "verification_status" in df.columns
    assert df["verification_status"].isin(["suspected", "verified", "dismissed"]).all()


def test_alerts_have_uncertainty():
    p = PROC / "alerts.parquet"
    df = pd.read_parquet(p)
    assert "uncertainty" in df.columns
    assert df["uncertainty"].between(0, 1).all()


def test_evaluation_has_operational_metrics():
    p = ROOT / "data" / "evaluation" / "reports" / "evaluation_report.json"
    r = json.loads(p.read_text())
    assert "operational" in r
    op = r["operational"]
    for key in ["false_alerts_per_store_week", "fusion_quality",
                "channel_coverage", "language_coverage",
                "policy_compliance", "human_override_rate",
                "resolution_outcome_rate"]:
        assert key in op, f"missing operational metric: {key}"


def test_policy_compliance_is_one():
    """Every mandatory-category record must be escalated."""
    p = ROOT / "data" / "evaluation" / "reports" / "evaluation_report.json"
    r = json.loads(p.read_text())
    assert r["operational"]["policy_compliance"] == 1.0, (
        f"policy compliance not 100%: {r['operational']['policy_compliance']}"
    )


def test_security_module_roles():
    import sys
    from storesignal import security
    assert "admin" in security.PERMISSIONS
    assert "reviewer" in security.PERMISSIONS
    assert "regional_manager" in security.PERMISSIONS
    assert "store_manager" in security.PERMISSIONS

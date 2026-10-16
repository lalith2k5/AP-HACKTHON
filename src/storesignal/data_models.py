"""
StoreSignal AI — Logical Entity Exports
========================================
Spec §5.1 lists Region and RoutingRule as first-class logical entities.
We materialize them as standalone Parquet files for schema parity.
"""

import json

import pandas as pd

from storesignal.paths import (
    CODE_ROOT,
    PROCESSED_DIR,
    REFERENCE_DIR,
)

ROOT = CODE_ROOT
REF = REFERENCE_DIR
PROC = PROCESSED_DIR

REGIONS_PARQUET = PROC / "regions.parquet"
ROUTING_RULES_PARQUET = PROC / "routing_rules.parquet"
REPORT = PROC / "data_models_report.json"


def export_regions():
    stores = pd.read_csv(REF / "store_master.csv", dtype=str)
    if "region_id" not in stores.columns:
        raise ValueError("store_master.csv missing region_id")
    regions = (
        stores[["region_id", "region_name"]]
        .drop_duplicates()
        .sort_values("region_id")
        .reset_index(drop=True)
    )
    regions.to_parquet(REGIONS_PARQUET, engine="pyarrow", index=False)
    print(f"[data_models] Wrote regions -> {REGIONS_PARQUET} ({len(regions)} rows)")
    return len(regions)


def export_routing_rules():
    taxonomy = pd.read_csv(REF / "taxonomy.csv", dtype=str)
    cfg_path = ROOT / "config" / "routing.yaml"
    cfg = {}
    if cfg_path.exists():
        import yaml
        with open(cfg_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    next_action = cfg.get("next_action_by_owner", {})
    sla = cfg.get("sla_hours_by_severity", {})

    rows = []
    for _, r in taxonomy.iterrows():
        owner = r["default_owner"]
        for severity, hours in sla.items():
            rows.append({
                "rule_id": f"RR-{r['category_id']}-{severity}",
                "category_id": r["category_id"],
                "category_name": r["category_name"],
                "owner_function": owner,
                "mandatory_escalation": str(r.get("mandatory_escalation", "false")).lower() == "true",
                "severity": severity,
                "sla_hours": int(hours),
                "next_action": next_action.get(owner, ""),
            })
    df = pd.DataFrame(rows)
    df.to_parquet(ROUTING_RULES_PARQUET, engine="pyarrow", index=False)
    print(f"[data_models] Wrote routing_rules -> {ROUTING_RULES_PARQUET} ({len(df)} rows)")
    return len(df)


def build():
    n_regions = export_regions()
    n_rules = export_routing_rules()
    report = {
        "regions": n_regions,
        "routing_rules": n_rules,
        "paths": {
            "regions": str(REGIONS_PARQUET),
            "routing_rules": str(ROUTING_RULES_PARQUET),
        },
    }
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"[data_models] Wrote report -> {REPORT}")


if __name__ == "__main__":
    build()

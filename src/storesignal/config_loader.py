"""
StoreSignal AI — Typed Configuration Loader
===========================================
Loads and merges all config/*.yaml files, validates with Pydantic v2,
and returns a single typed object. Existing modules can keep reading
config.yaml directly for backward compatibility.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from storesignal import settings as _ssettings

from storesignal.paths import (
    CODE_ROOT,
    DATA_DIR,
    PROCESSED_DIR,
    RAW_DIR,
    REFERENCE_DIR,
    REPORTS_DIR,
)
ROOT = CODE_ROOT
CONFIG_DIR = _ssettings.CONFIG_DIR


class PathsCfg(BaseModel):
    data_raw: str = "data/raw"
    data_reference: str = "data/reference"
    data_processed: str = "data/processed"
    models: str = "models"


class ClassificationCfg(BaseModel):
    validation_days: int = 3
    tfidf_word_ngram_min: int = 1
    tfidf_word_ngram_max: int = 2
    tfidf_char_ngram_min: int = 3
    tfidf_char_ngram_max: int = 5
    tfidf_max_features_word: int = 20000
    tfidf_max_features_char: int = 30000
    tfidf_min_df: int = 2
    logistic_C: float = 4.0
    logistic_max_iter: int = 400
    logistic_class_weight: str = "balanced"


class DetectionCfg(BaseModel):
    historical_window_days: int = 28
    min_historical_periods: int = 14
    robust_z_threshold: float = 3.0
    min_count: int = 2
    min_rate_increase: float = 2.0


class RiskPolicyCfg(BaseModel):
    mandatory_categories: list[str] = Field(default_factory=list)
    min_confidence_for_suppression: float = 0.0


class RoutingCfg(BaseModel):
    next_action_by_owner: dict[str, str] = Field(default_factory=dict)
    sla_hours_by_severity: dict[str, int] = Field(default_factory=dict)


class TaxonomyCfg(BaseModel):
    severity_map: dict[str, list[str]] = Field(default_factory=dict)


class ApiCfg(BaseModel):
    require_api_key: bool = False
    api_key: str = "demo-key-storesignal"
    rate_limit_per_minute: int = 120


class AppConfig(BaseModel):
    random_seed: int = 20260214
    paths: PathsCfg = Field(default_factory=PathsCfg)
    classification: ClassificationCfg = Field(default_factory=ClassificationCfg)
    detection: DetectionCfg = Field(default_factory=DetectionCfg)
    risk_policy: RiskPolicyCfg = Field(default_factory=RiskPolicyCfg)
    routing: RoutingCfg = Field(default_factory=RoutingCfg)
    taxonomy: TaxonomyCfg = Field(default_factory=TaxonomyCfg)
    api: ApiCfg = Field(default_factory=ApiCfg)


def _read(name: str) -> dict[str, Any]:
    p = CONFIG_DIR / name
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config() -> AppConfig:
    """Load and merge all config files into a single typed object."""
    demo = _read("demo.yaml")
    thresholds = _read("thresholds.yaml")
    policy = _read("risk_policy.yaml")
    routing = _read("routing.yaml")
    taxonomy = _read("taxonomy.yaml")

    merged = {
        "random_seed": demo.get("random_seed", 20260214),
        "paths": demo.get("paths", {}),
        "classification": thresholds.get("classification", {}),
        "detection": thresholds.get("detection", {}),
        "risk_policy": policy,
        "routing": routing,
        "taxonomy": taxonomy,
        "api": demo.get("api", {}),
    }
    return AppConfig.model_validate(merged)


def category_to_severity(cfg: AppConfig) -> dict[str, str]:
    out: dict[str, str] = {}
    for sev, cats in cfg.taxonomy.severity_map.items():
        for c in cats:
            out[c] = sev
    return out


if __name__ == "__main__":
    c = load_config()
    print("random_seed          :", c.random_seed)
    print("mandatory_categories :", c.risk_policy.mandatory_categories)
    print("severity_map levels  :", list(c.taxonomy.severity_map.keys()))
    print("owners               :", list(c.routing.next_action_by_owner.keys()))
    print("api.require_api_key  :", c.api.require_api_key)
    print("ALL CONFIG LOADS OK")

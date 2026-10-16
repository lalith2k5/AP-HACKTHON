# Threshold Tuning Worksheet

Every config default needs a named approver before operational use. This
document exists because spec section 20.5 states "thresholds are configuration
defaults only. They must be validated against permitted validation data."

## config/thresholds.yaml

| Key | Current | Rationale | Approved by | Date |
|---|---|---|---|---|
| baseline_days | 28 | Standard for weekly retail cadence | | |
| minimum_baseline_days | 14 | Below this, mark insufficient coverage | | |
| incident_window_hours | 72 | Aligns with shift cycle | | |
| mad_score_threshold | 3.0 | Standard robust-anomaly cutoff | | |
| minimum_current_count | 2 | Below this, single-signal noise | | |
| minimum_rate_lift | 2.0 | Guards against tiny denominators | | |
| exposure_unit | per_10000_visits | Footfall from store_master.csv | | |
| fallback_score | zscore | When MAD unstable | | |
| cooldown_hours | 24 | Reduces alert fatigue | | |

## config/risk_policy.yaml

| Rule ID | Trigger | Severity | Route to | Approved by | Date |
|---|---|---|---|---|---|
| FOOD_SAFETY_URGENT | 1 signal | critical | food_safety, store_ops | | |
| ALLERGEN_URGENT | 1 signal | critical | food_safety, risk | | |
| STAFF_MISCONDUCT_URGENT | 1 signal | high | hr, risk | | |

## config/routing.yaml

Every category -> owner mapping is a business decision. Owner team lead
must confirm each row.

## Instructions

1. Ops lead fills Current column (already populated) and Rationale
2. Risk lead reviews every rule under config/risk_policy.yaml
3. Owner teams confirm their category mappings
4. Any value changed must be re-validated against permitted data
5. Return signed copy to the compliance folder

"""
StoreSignal AI - Early-Warning Radar
=====================================
Per-store, per-category robust anomaly detection using rolling historical
baselines and median absolute deviation (MAD).

Defaults (R5 spec / config.yaml):
  - historical_window = 28 days
  - min_historical_periods = 14 days
  - robust z threshold = 3.0
  - min_count = 2
  - min_rate_increase = 2x baseline

Exposure: rate per 10k weekly footfall is recorded alongside raw counts.
"""

import json

import numpy as np
import pandas as pd
import yaml

from storesignal.paths import (
    CODE_ROOT,
    PROCESSED_DIR,
    REFERENCE_DIR,
)

ROOT = CODE_ROOT
CONFIG_PATH = ROOT / "config" / "config.yaml"
PRED_PARQUET = PROCESSED_DIR / "predictions.parquet"
STORE_CSV = REFERENCE_DIR / "store_master.csv"
FLAGS_PARQUET = PROCESSED_DIR / "radar_flags.parquet"
SUMMARY_PARQUET = PROCESSED_DIR / "radar_summary.parquet"
REPORT_PATH = PROCESSED_DIR / "radar_report.json"

HISTORICAL_WINDOW_DAYS = 28
MIN_HISTORICAL_PERIODS = 14
Z_THRESHOLD = 3.0
MIN_COUNT = 2
MIN_RATE_INCREASE = 2.0


def robust_z_score(x: float, history: np.ndarray) -> float:
    """Robust z-score with a Poisson-style fallback when MAD is zero."""
    arr = np.asarray(history, dtype=float)
    if arr.size == 0:
        return 0.0
    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med)))
    if mad >= 1e-9:
        return float(0.6745 * (x - med) / mad)
    # Flat baseline — use sqrt(med) floor or 1.0 when med == 0
    std = max(np.sqrt(med), 1.0)
    return float((x - med) / std)


def detect():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        _ = yaml.safe_load(f)

    print("[radar] Loading predictions...")
    preds = pd.read_parquet(PRED_PARQUET, engine="pyarrow")
    preds["timestamp"] = pd.to_datetime(preds["timestamp"], utc=True)
    preds["day"] = preds["timestamp"].dt.normalize()
    print(f"[radar] Loaded {len(preds)} predictions")

    stores = pd.read_csv(STORE_CSV)
    footfall_map = dict(zip(stores["store_id"], stores["weekly_footfall"].astype(float)))

    daily = (
        preds.groupby(["store_id", "predicted_category", "day"])
        .size()
        .reset_index(name="count")
    )
    daily = daily.sort_values(["store_id", "predicted_category", "day"]).reset_index(drop=True)
    print(f"[radar] Aggregated {len(daily)} (store, category, day) rows")

    window_td = pd.Timedelta(days=HISTORICAL_WINDOW_DAYS)
    flags = []

    for (store, cat), grp in daily.groupby(["store_id", "predicted_category"]):
        grp = grp.sort_values("day").reset_index(drop=True)
        counts = grp.set_index("day")["count"]
        footfall = max(float(footfall_map.get(store, 1.0)), 1.0)

        for _, row in grp.iterrows():
            day = row["day"]
            cnt = int(row["count"])

            if cnt < MIN_COUNT:
                continue

            history_start = day - window_td
            history = counts[(counts.index >= history_start) & (counts.index < day)].values
            if len(history) < MIN_HISTORICAL_PERIODS:
                continue

            med = float(np.median(history))
            z = robust_z_score(cnt, history)

            baseline_for_ratio = max(med, 0.5)
            rate_ratio = cnt / baseline_for_ratio
            if rate_ratio < MIN_RATE_INCREASE:
                continue
            if z < Z_THRESHOLD:
                continue

            flags.append({
                "store_id": store,
                "predicted_category": cat,
                "day": day,
                "count": cnt,
                "baseline_median": med,
                "robust_z": round(z, 4),
                "rate_ratio": round(rate_ratio, 4),
                "rate_per_10k": round((cnt / footfall) * 10000.0, 4),
                "baseline_rate_per_10k": round((med / footfall) * 10000.0, 4),
                "weekly_footfall": footfall,
            })

    if flags:
        flags_df = pd.DataFrame(flags).sort_values(
            ["day", "robust_z"], ascending=[True, False]
        ).reset_index(drop=True)
        flags_df["is_first_flag"] = ~flags_df.duplicated(
            subset=["store_id", "predicted_category"], keep="first"
        )
    else:
        flags_df = pd.DataFrame(columns=[
            "store_id", "predicted_category", "day", "count", "baseline_median",
            "robust_z", "rate_ratio", "rate_per_10k",
            "baseline_rate_per_10k", "weekly_footfall", "is_first_flag",
        ])

    flags_df.to_parquet(FLAGS_PARQUET, engine="pyarrow", index=False)
    print(f"[radar] Wrote flags -> {FLAGS_PARQUET} ({len(flags_df)} rows)")

    if not flags_df.empty:
        summary = (
            flags_df.groupby(["store_id", "predicted_category"])
            .agg(
                first_flag_day=("day", "min"),
                last_flag_day=("day", "max"),
                num_flag_days=("day", "nunique"),
                max_robust_z=("robust_z", "max"),
                max_count=("count", "max"),
                total_flagged_count=("count", "sum"),
            )
            .reset_index()
            .sort_values("max_robust_z", ascending=False)
            .reset_index(drop=True)
        )
    else:
        summary = pd.DataFrame(columns=[
            "store_id", "predicted_category", "first_flag_day", "last_flag_day",
            "num_flag_days", "max_robust_z", "max_count", "total_flagged_count",
        ])

    summary.to_parquet(SUMMARY_PARQUET, engine="pyarrow", index=False)
    print(f"[radar] Wrote summary -> {SUMMARY_PARQUET} ({len(summary)} rows)")

    report = {
        "historical_window_days": HISTORICAL_WINDOW_DAYS,
        "min_historical_periods": MIN_HISTORICAL_PERIODS,
        "z_threshold": Z_THRESHOLD,
        "min_count": MIN_COUNT,
        "min_rate_increase": MIN_RATE_INCREASE,
        "total_flags": int(len(flags_df)),
        "unique_store_category_pairs": int(len(summary)),
        "unique_stores_flagged": int(flags_df["store_id"].nunique()) if not flags_df.empty else 0,
        "unique_categories_flagged": int(flags_df["predicted_category"].nunique()) if not flags_df.empty else 0,
        "top_10_summary": (
            summary.head(10).assign(
                first_flag_day=lambda d: d["first_flag_day"].astype(str),
                last_flag_day=lambda d: d["last_flag_day"].astype(str),
            ).to_dict(orient="records")
            if not summary.empty else []
        ),
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[radar] Wrote report -> {REPORT_PATH}")

    print("")
    print("[radar] SUMMARY")
    print(f"  Total flags              : {report['total_flags']}")
    print(f"  Unique (store, category) : {report['unique_store_category_pairs']}")
    print(f"  Unique stores flagged    : {report['unique_stores_flagged']}")
    print(f"  Unique categories flagged: {report['unique_categories_flagged']}")
    if not summary.empty:
        print("  Top 5 by max z-score:")
        print(summary.head(5).to_string(index=False))


if __name__ == "__main__":
    detect()

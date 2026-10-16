"""
StoreSignal AI — Forecasting & Action-Impact Simulator (P2 stretch)
===================================================================
Simple exponential-smoothing forecast per (store, category) over the
next N days, plus a "what-if" simulator that estimates the effect of
acting on an alert today vs. deferring.

Exports:
  data/processed/forecasts.parquet
  data/processed/forecast_report.json
"""

import json

import numpy as np
import pandas as pd

from storesignal.paths import (
    CODE_ROOT,
    PROCESSED_DIR,
)

ROOT = CODE_ROOT
PROC = PROCESSED_DIR
PRED_PARQUET = PROC / "predictions.parquet"
OUT_PARQUET = PROC / "forecasts.parquet"
REPORT = PROC / "forecast_report.json"

HORIZON_DAYS = 7
ALPHA = 0.4           # exponential smoothing factor
ACT_NOW_REDUCTION = 0.55   # assume 55% reduction if we act now
DEFER_REDUCTION = 0.15     # assume 15% reduction if we defer one week


def _forecast_series(counts: pd.Series, horizon: int, alpha: float) -> list[float]:
    vals = counts.astype(float).tolist()
    if not vals:
        return [0.0] * horizon
    level = vals[0]
    for v in vals[1:]:
        level = alpha * v + (1 - alpha) * level
    # Simple persistence + small trend from last 3 obs
    trend = 0.0
    if len(vals) >= 3:
        trend = (vals[-1] - vals[-3]) / 2.0
    return [max(0.0, level + trend * (i + 1)) for i in range(horizon)]


def build():
    preds = pd.read_parquet(PRED_PARQUET, engine="pyarrow")
    preds["timestamp"] = pd.to_datetime(preds["timestamp"], utc=True)
    preds["day"] = preds["timestamp"].dt.normalize()

    daily = preds.groupby(["store_id", "predicted_category", "day"]).size().reset_index(name="count")

    rows = []
    for (store, cat), grp in daily.groupby(["store_id", "predicted_category"]):
        grp = grp.sort_values("day")
        counts = grp["count"]

        if len(counts) < 5:
            continue

        fc = _forecast_series(counts, HORIZON_DAYS, ALPHA)
        fc_mean = float(np.mean(fc))
        baseline_mean = float(np.mean(counts.tail(7))) if len(counts) >= 7 else float(np.mean(counts))

        act_now_expected = baseline_mean * (1 - ACT_NOW_REDUCTION)
        defer_expected = baseline_mean * (1 - DEFER_REDUCTION)

        rows.append({
            "store_id": store,
            "predicted_category": cat,
            "baseline_7d_mean": round(baseline_mean, 3),
            "forecast_7d_mean": round(fc_mean, 3),
            "act_now_expected": round(act_now_expected, 3),
            "defer_expected": round(defer_expected, 3),
            "act_now_advantage": round(defer_expected - act_now_expected, 3),
        })

    df = pd.DataFrame(rows).sort_values("act_now_advantage", ascending=False).reset_index(drop=True)
    df.to_parquet(OUT_PARQUET, engine="pyarrow", index=False)
    print(f"[forecast] Wrote {OUT_PARQUET} ({len(df)} rows)")

    top = df.head(10).to_dict(orient="records") if len(df) else []
    report = {
        "horizon_days": HORIZON_DAYS,
        "alpha": ALPHA,
        "act_now_reduction": ACT_NOW_REDUCTION,
        "defer_reduction": DEFER_REDUCTION,
        "pairs_forecasted": int(len(df)),
        "top_act_now_opportunities": top,
    }
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[forecast] Wrote {REPORT}")
    if top:
        print("[forecast] Top 3 act-now opportunities:")
        for r in top[:3]:
            print(f"  {r['store_id']} {r['predicted_category']}: "
                  f"advantage={r['act_now_advantage']}")


if __name__ == "__main__":
    build()

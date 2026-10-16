"""Process an imported batch through classification and policy."""
import json
import sys

import joblib
import pandas as pd

from storesignal.paths import MODEL_DIR, PROCESSED_DIR

IMPORT_DIR = PROCESSED_DIR / "imports"


def process(batch_id: str) -> dict:
    batch_dir = IMPORT_DIR / batch_id
    raw_path = batch_dir / "raw.parquet"
    if not raw_path.exists():
        return {"error": f"batch {batch_id} not found at {batch_dir}"}
    df = pd.read_parquet(raw_path)
    if df.empty:
        return {"error": "imported batch has zero rows"}
    model_path = MODEL_DIR / "baseline_model.joblib"
    if not model_path.exists():
        return {"error": f"model artifact missing: {model_path}"}
    bundle = joblib.load(model_path)
    vectorizer = bundle["vectorizer"]
    clf = bundle["classifier"]
    labels = list(bundle["classifier"].classes_)
    severity_map = bundle["severity_map"]
    actionable_by_severity = bundle["actionable_by_severity"]
    mandatory = {c for c, sev in severity_map.items()
                 if sev in {"critical", "high"}}
    text = df["text_raw"].fillna("").astype(str)
    X = vectorizer.transform(text)
    probs = clf.predict_proba(X)
    rows = []
    escalations = []
    for i, (_, r) in enumerate(df.iterrows()):
        p = probs[i]
        top_idx = int(p.argmax())
        cat = labels[top_idx]
        conf = float(p[top_idx])
        sev = severity_map.get(cat, "medium")
        rows.append({
            "record_id": r["record_id"],
            "channel": r["channel"],
            "store_id": r["store_id"],
            "timestamp": r["timestamp"],
            "predicted_category": cat,
            "confidence": conf,
            "severity": sev,
            "actionable": bool(actionable_by_severity.get(sev, False)),
            "batch_id": batch_id,
        })
        if cat in mandatory:
            escalations.append({
                "record_id": r["record_id"],
                "store_id": r["store_id"],
                "predicted_category": cat,
                "severity": sev,
                "confidence": conf,
                "reason": f"mandatory policy: {cat}",
                "batch_id": batch_id,
            })
    pd.DataFrame(rows).to_parquet(batch_dir / "predictions.parquet", index=False)
    pd.DataFrame(escalations).to_parquet(batch_dir / "escalations.parquet", index=False)
    summary = {
        "batch_id": batch_id,
        "rows_processed": len(rows),
        "mandatory_escalations": len(escalations),
    }
    (batch_dir / "process_report.json").write_text(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python -m storesignal.process_import BATCH_ID")
        sys.exit(1)
    print(json.dumps(process(sys.argv[1]), indent=2))

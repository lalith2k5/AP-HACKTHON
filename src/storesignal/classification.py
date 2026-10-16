"""
StoreSignal AI — Baseline Classifier
====================================
Trains TF-IDF (word + char n-grams) + Logistic Regression on weak labels,
evaluates on a time-aware holdout, then predicts on the full dataset.
Severity and actionability are assigned by category using config.yaml rules.
"""

import json
from datetime import timedelta
from pathlib import Path

import joblib
import pandas as pd
import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.pipeline import FeatureUnion

from storesignal.weak_labels import weak_label_frame

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HOME = Path.home()
ROOT = HOME / "storesignal-ai"

CONFIG_PATH = ROOT / "config" / "config.yaml"
NORM_PARQUET = ROOT / "data" / "processed" / "normalized_feedback.parquet"
PRED_PARQUET = ROOT / "data" / "processed" / "predictions.parquet"
MODELS_DIR = ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODELS_DIR / "baseline_model.joblib"
REPORT_PATH = ROOT / "data" / "processed" / "classification_report.json"

SEVERITY_BY_CATEGORY = {}
ACTIONABLE_BY_SEVERITY = {
    "critical": True,
    "high": True,
    "medium": False,
    "low": False,
}


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_severity_map(cfg):
    global SEVERITY_BY_CATEGORY
    SEVERITY_BY_CATEGORY = {}
    for sev, cats in cfg["severity_map"].items():
        for c in cats:
            SEVERITY_BY_CATEGORY[c] = sev


def severity_for(category: str) -> str:
    return SEVERITY_BY_CATEGORY.get(category, "medium")


def actionable_for(severity: str) -> bool:
    return ACTIONABLE_BY_SEVERITY.get(severity, False)


def build_vectorizer(cfg):
    clf = cfg["classification"]
    word = TfidfVectorizer(
        analyzer="word",
        ngram_range=(clf["tfidf_word_ngram_min"], clf["tfidf_word_ngram_max"]),
        max_features=clf["tfidf_max_features_word"],
        min_df=clf["tfidf_min_df"],
        lowercase=True,
        sublinear_tf=True,
    )
    char = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(clf["tfidf_char_ngram_min"], clf["tfidf_char_ngram_max"]),
        max_features=clf["tfidf_max_features_char"],
        min_df=clf["tfidf_min_df"],
        lowercase=True,
        sublinear_tf=True,
    )
    return FeatureUnion([("word", word), ("char", char)])


def time_split(df: pd.DataFrame, val_days: int):
    cutoff = df["timestamp"].max() - timedelta(days=val_days)
    train = df[df["timestamp"] <= cutoff].reset_index(drop=True)
    val = df[df["timestamp"] > cutoff].reset_index(drop=True)
    return train, val, cutoff


def train_and_predict():
    cfg = load_config()
    build_severity_map(cfg)
    seed = cfg["random_seed"]

    print("[classification] Loading normalized parquet...")
    df = pd.read_parquet(NORM_PARQUET, engine="pyarrow")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    print(f"[classification] Loaded {len(df)} rows")

    print("[classification] Generating weak labels (training signal only)...")
    df = weak_label_frame(df)
    print("[classification] Weak category distribution:")
    print(df["weak_category"].value_counts().to_string())

    print("[classification] Time-aware train/val split...")
    train_df, val_df, cutoff = time_split(df, cfg["classification"]["validation_days"])
    print(f"  cutoff = {cutoff.isoformat()}")
    print(f"  train  = {len(train_df)} rows")
    print(f"  val    = {len(val_df)} rows")

    if len(train_df) < 100 or len(val_df) < 20:
        raise RuntimeError("Train/val split too small. Check data.")

    print("[classification] Building TF-IDF vectorizer...")
    vec = build_vectorizer(cfg)

    print("[classification] Fitting vectorizer on training text...")
    X_train = vec.fit_transform(train_df["text_norm"].values)
    X_val = vec.transform(val_df["text_norm"].values)
    print(f"  feature dims = {X_train.shape[1]}")

    print("[classification] Training LogisticRegression...")
    clf = LogisticRegression(
        C=cfg["classification"]["logistic_C"],
        max_iter=cfg["classification"]["logistic_max_iter"],
        class_weight=cfg["classification"]["logistic_class_weight"],
        random_state=seed,
    )
    clf.fit(X_train, train_df["weak_category"].values)

    print("[classification] Evaluating on time holdout vs weak labels...")
    val_pred = clf.predict(X_val)
    macro_f1 = f1_score(val_df["weak_category"], val_pred, average="macro", zero_division=0)
    print(f"  validation macro-F1 vs weak labels = {macro_f1:.4f}")

    report_text = classification_report(
        val_df["weak_category"], val_pred, zero_division=0, output_dict=True
    )

    print("[classification] Predicting on full dataset...")
    X_all = vec.transform(df["text_norm"].values)
    df["predicted_category"] = clf.predict(X_all)

    proba = clf.predict_proba(X_all)
    df["confidence"] = proba.max(axis=1).round(4)

    df["severity"] = df["predicted_category"].apply(severity_for)
    df["actionable"] = df["severity"].apply(actionable_for)

    # Save model bundle
    bundle = {
        "vectorizer": vec,
        "classifier": clf,
        "severity_map": SEVERITY_BY_CATEGORY,
        "actionable_by_severity": ACTIONABLE_BY_SEVERITY,
        "macro_f1_val": macro_f1,
        "validation_cutoff": cutoff.isoformat(),
    }
    joblib.dump(bundle, MODEL_PATH)
    print(f"[classification] Saved model bundle -> {MODEL_PATH}")

    # Save predictions parquet
    pred_cols = [
        "record_id", "channel", "store_id", "timestamp",
        "language_hint",
        "text_norm", "weak_category",
        "predicted_category", "confidence",
        "severity", "actionable",
    ]
    df[pred_cols].to_parquet(PRED_PARQUET, engine="pyarrow", index=False)
    print(f"[classification] Wrote predictions -> {PRED_PARQUET} ({len(df)} rows)")

    # Save report
    report = {
        "rows_total": int(len(df)),
        "rows_train": int(len(train_df)),
        "rows_val": int(len(val_df)),
        "validation_cutoff": cutoff.isoformat(),
        "validation_macro_f1_vs_weak": float(macro_f1),
        "num_categories_predicted": int(df["predicted_category"].nunique()),
        "predicted_category_counts": df["predicted_category"].value_counts().to_dict(),
        "severity_counts": df["severity"].value_counts().to_dict(),
        "actionable_true_count": int(df["actionable"].sum()),
        "mean_confidence": float(df["confidence"].mean()),
        "per_class_report": report_text,
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[classification] Wrote report    -> {REPORT_PATH}")

    print("")
    print("[classification] SUMMARY")
    print(f"  Total rows          : {report['rows_total']}")
    print(f"  Predicted categories: {report['num_categories_predicted']}")
    print(f"  Actionable (True)   : {report['actionable_true_count']}")
    print(f"  Mean confidence     : {report['mean_confidence']:.4f}")
    print(f"  Validation macro-F1 : {macro_f1:.4f}")
    print("  Severity counts:")
    for sev, n in report["severity_counts"].items():
        print(f"    {sev:16s} {n}")


if __name__ == "__main__":
    train_and_predict()

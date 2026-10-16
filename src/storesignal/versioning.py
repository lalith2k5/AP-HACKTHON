"""
StoreSignal AI — Versioning & Reproducibility
==============================================
Computes SHA-256 hashes over:
  - config files (config_hash)
  - raw data files (data_hash)
  - model bundle (model_hash)
Stamps every evaluation run with a run_id and records it in a
versioned evaluation log.
"""

import hashlib
import json
import time
import uuid
from pathlib import Path

from storesignal.paths import (
    CODE_ROOT,
    RAW_DIR,
    REPORTS_DIR,
)

ROOT = CODE_ROOT
CONFIG_DIR = ROOT / "config"
DATA_RAW = RAW_DIR
MODEL_PATH = ROOT / "models" / "baseline_model.joblib"
RUNS_LOG = REPORTS_DIR.parent / "runs.jsonl"
RUNS_LOG.parent.mkdir(parents=True, exist_ok=True)


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_of_concat(files: list[Path]) -> str:
    h = hashlib.sha256()
    for p in sorted(files):
        if p.exists():
            h.update(p.name.encode("utf-8"))
            h.update(_sha256_file(p).encode("utf-8"))
    return h.hexdigest()


def config_hash() -> str:
    return _sha256_of_concat(list(CONFIG_DIR.glob("*.yaml")))


def data_hash() -> str:
    names = ["reviews.jsonl", "app_feedback.jsonl", "staff_notes.jsonl",
             "call_transcripts.jsonl", "hidden_labels.jsonl", "seeded_incidents.json"]
    return _sha256_of_concat([DATA_RAW / n for n in names])


def model_hash() -> str:
    return _sha256_file(MODEL_PATH)


def new_run_id() -> str:
    return f"run-{int(time.time())}-{uuid.uuid4().hex[:8]}"


def stamp_run(metrics: dict) -> dict:
    run = {
        "run_id": new_run_id(),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config_hash": config_hash(),
        "data_hash": data_hash(),
        "model_hash": model_hash(),
        "model_version": "baseline-v1",
        "metrics": metrics,
    }
    with open(RUNS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(run, default=str) + "\n")
    return run


if __name__ == "__main__":
    print("config_hash :", config_hash()[:16], "...")
    print("data_hash   :", data_hash()[:16], "...")
    print("model_hash  :", model_hash()[:16], "...")
    print("ALL HASHES COMPUTED OK")

"""
StoreSignal AI — Full pipeline orchestrator
============================================
Runs every stage including relationship graph, forecasting, and
stamps the evaluation with hashes.
"""

import subprocess
import sys
import time

from storesignal.logging_setup import get_logger, log_event
from storesignal.paths import (
    CODE_ROOT,
)

ROOT = CODE_ROOT
PY = ROOT / ".venv" / "bin" / "python"
log = get_logger("pipeline")

STAGES = [
    ("generate_mock_data", "Generate mock dataset (40k, 3 seeded)"),
    ("ingestion",          "Ingest + validate -> raw_feedback.parquet"),
    ("normalization",      "Normalize -> normalized_feedback.parquet"),
    ("classification",     "Train baseline -> predictions.parquet"),
    ("risk_policy",        "Mandatory escalation -> escalations.parquet"),
    ("detection",          "Early-Warning Radar -> radar_flags.parquet"),
    ("routing",            "Owner routing -> routing.parquet"),
    ("fusion",             "Deduplicate -> incidents.parquet"),
    ("alerts",             "Alerts -> alerts.parquet"),
    ("briefs",             "Weekly regional briefs -> briefs/*.md"),
    ("data_models",        "Export regions + routing_rules entities"),
    ("relationship_graph", "Relationship graph -> graphml + json"),
    ("forecasting",        "Forecasts + simulator -> forecasts.parquet"),
    ("evaluate",           "Hidden-label + lead-time evaluation"),
]


def run():
    t0 = time.time()
    log_event(log, "pipeline.start", stage="all")
    for module, desc in STAGES:
        print()
        print("=" * 72)
        print(f"[pipeline] {desc}")
        print(f"[pipeline] storesignal.{module}")
        print("=" * 72)
        t_stage = time.time()
        log_event(log, "stage.start", stage=module)
        r = subprocess.run(
            [str(PY), "-m", f"storesignal.{module}"],
            check=False, cwd=str(ROOT),
        )
        dur = int((time.time() - t_stage) * 1000)
        if r.returncode != 0:
            log_event(log, "stage.failed", level="error", stage=module,
                      duration_ms=dur, error_code=f"exit_{r.returncode}")
            print(f"[pipeline] FAILED: {module}", file=sys.stderr)
            sys.exit(r.returncode)
        log_event(log, "stage.done", stage=module, duration_ms=dur)
    print()
    print("=" * 72)
    print(f"[pipeline] DONE in {time.time() - t0:.1f}s")
    print("=" * 72)
    log_event(log, "pipeline.done", duration_ms=int((time.time() - t0) * 1000))

if __name__ == "__main__":
    run()

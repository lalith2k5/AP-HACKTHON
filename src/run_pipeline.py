"""
StoreSignal AI — Full pipeline orchestrator
============================================
Runs every stage including relationship graph, forecasting, and
stamps the evaluation with hashes.
"""

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path.home() / "storesignal-ai"
PY = ROOT / ".venv" / "bin" / "python"
SRC = ROOT / "src"

STAGES = [
    ("generate_mock_data.py", "Generate mock dataset (40k, 3 seeded)"),
    ("ingestion.py",          "Ingest + validate -> raw_feedback.parquet"),
    ("normalization.py",      "Normalize -> normalized_feedback.parquet"),
    ("classification.py",     "Train baseline -> predictions.parquet"),
    ("risk_policy.py",        "Mandatory escalation -> escalations.parquet"),
    ("detection.py",          "Early-Warning Radar -> radar_flags.parquet"),
    ("routing.py",            "Owner routing -> routing.parquet"),
    ("fusion.py",             "Deduplicate -> incidents.parquet"),
    ("alerts.py",             "Alerts -> alerts.parquet"),
    ("briefs.py",             "Weekly regional briefs -> briefs/*.md"),
    ("data_models.py",        "Export regions + routing_rules entities"),
    ("relationship_graph.py", "Relationship graph -> graphml + json"),
    ("forecasting.py",        "Forecasts + simulator -> forecasts.parquet"),
    ("evaluate.py",           "Hidden-label + lead-time evaluation"),
]


def run():
    t0 = time.time()
    for script, desc in STAGES:
        path = SRC / script
        if not path.exists():
            print(f"[pipeline] MISSING {path}", file=sys.stderr)
            sys.exit(1)
        print()
        print("=" * 72)
        print(f"[pipeline] {desc}")
        print(f"[pipeline] {path.name}")
        print("=" * 72)
        r = subprocess.run([str(PY), str(path)], check=False, cwd=str(SRC))
        if r.returncode != 0:
            print(f"[pipeline] FAILED: {path.name}", file=sys.stderr)
            sys.exit(r.returncode)
    print()
    print("=" * 72)
    print(f"[pipeline] DONE in {time.time() - t0:.1f}s")
    print("=" * 72)


if __name__ == "__main__":
    run()

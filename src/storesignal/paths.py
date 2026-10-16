"""
Central path resolution.
========================
Reads DATA_DIR / MODEL_DIR / CONFIG_DIR / LOG_DIR / REPORT_DIR from
settings.py, which honors STORESIGNAL_* env vars (spec section 5.1).

Every pipeline module should import path constants from here instead of
hardcoding Path.home() / "storesignal-ai" / "data" / ...
"""
from pathlib import Path

from storesignal import settings as S

CODE_ROOT = Path.home() / "storesignal-ai"
CONFIG_DIR = S.CONFIG_DIR
DATA_DIR = S.DATA_DIR
RAW_DIR = DATA_DIR / "raw"
REFERENCE_DIR = DATA_DIR / "reference"
PROCESSED_DIR = DATA_DIR / "processed"
EVALUATION_DIR = DATA_DIR / "evaluation"
REPORTS_DIR = EVALUATION_DIR / "reports"
MODEL_DIR = S.MODEL_DIR
LOG_DIR = S.LOG_DIR

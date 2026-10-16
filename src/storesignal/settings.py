"""
StoreSignal AI - Environment variable settings
==============================================
Honors all 12 STORESIGNAL_* env vars from spec section 5.1.
Defaults are chosen so the local demo runs with zero env configuration.
"""
import os
from pathlib import Path

ROOT = Path.home() / "storesignal-ai"


def _bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


ENV = os.getenv("STORESIGNAL_ENV", "development")
DATA_DIR = Path(os.getenv("STORESIGNAL_DATA_DIR", str(ROOT / "data")))
CONFIG_DIR = Path(os.getenv("STORESIGNAL_CONFIG_DIR", str(ROOT / "config")))
MODEL_DIR = Path(os.getenv("STORESIGNAL_MODEL_DIR", str(ROOT / "models")))
REPORT_DIR = Path(os.getenv("STORESIGNAL_REPORT_DIR", str(ROOT / "reports")))
LOG_DIR = Path(os.getenv("STORESIGNAL_LOG_DIR", str(ROOT / "logs")))
LOG_LEVEL = os.getenv("STORESIGNAL_LOG_LEVEL", "INFO")
DEMO_MODE = _bool("STORESIGNAL_DEMO_MODE", True)
API_KEY = os.getenv("STORESIGNAL_API_KEY", "demo-key-storesignal")
ALLOW_HIDDEN_EVAL = _bool("STORESIGNAL_ALLOW_HIDDEN_EVAL", ENV == "development")
MAX_UPLOAD_MB = _int("STORESIGNAL_MAX_UPLOAD_MB", 100)
MAX_ROWS = _int("STORESIGNAL_MAX_ROWS", 500000)
TIMEZONE = os.getenv("STORESIGNAL_TIMEZONE", "Asia/Kolkata")


def ensure_dirs() -> None:
    for d in (DATA_DIR, REPORT_DIR, LOG_DIR, MODEL_DIR):
        try:
            d.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass


def validate_startup() -> list[str]:
    errors: list[str] = []
    if not CONFIG_DIR.exists():
        errors.append(f"config directory not found: {CONFIG_DIR}")
    if not (ROOT / "src" / "storesignal" / "api.py").exists():
        errors.append("api module missing from package")
    if not (ROOT / "src" / "storesignal" / "ui.py").exists():
        errors.append("ui module missing from package")
    return errors


def snapshot() -> dict:
    return {
        "env": ENV,
        "demo_mode": DEMO_MODE,
        "allow_hidden_eval": ALLOW_HIDDEN_EVAL,
        "max_upload_mb": MAX_UPLOAD_MB,
        "max_rows": MAX_ROWS,
        "timezone": TIMEZONE,
        "log_level": LOG_LEVEL,
        "data_dir": str(DATA_DIR),
        "config_dir": str(CONFIG_DIR),
        "model_dir": str(MODEL_DIR),
        "report_dir": str(REPORT_DIR),
        "log_dir": str(LOG_DIR),
    }

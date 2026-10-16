"""
Structured JSON logging (spec section 19.1).
=============================================
Emits one JSON object per line with the fields:
  timestamp, level, component, event, request_id, run_id,
  stage, duration_ms, records_in, records_out, error_code

Call configure() once at process start; then use get_logger(component).
"""
from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any

from storesignal import settings as S

_configured = False


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "component": record.name,
            "event": getattr(record, "event", record.getMessage()),
        }
        for key in ("request_id", "run_id", "stage", "duration_ms",
                    "records_in", "records_out", "error_code"):
            v = getattr(record, key, None)
            if v is not None:
                payload[key] = v
        if record.exc_info:
            payload["error_code"] = record.exc_info[0].__name__ if record.exc_info[0] else None
        return json.dumps(payload, default=str)


def configure(level: str | None = None) -> None:
    global _configured
    if _configured:
        return
    lvl = (level or S.LOG_LEVEL).upper()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger("storesignal")
    root.setLevel(lvl)
    root.handlers[:] = [handler]
    root.propagate = False
    _configured = True


def get_logger(component: str) -> logging.Logger:
    configure()
    return logging.getLogger(f"storesignal.{component}")


def log_event(logger: logging.Logger, event: str, level: str = "info", **fields: Any) -> None:
    getattr(logger, level)(event, extra={"event": event, **fields})

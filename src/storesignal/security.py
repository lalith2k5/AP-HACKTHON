"""
StoreSignal AI — Security Layer
================================
- API key authentication with role assignment
- In-memory token-bucket rate limiting
- Audit logging
- Request correlation IDs
- Idempotency key store
"""

import json
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from pathlib import Path

from fastapi import Header, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from storesignal.config_loader import load_config

ROOT = Path.home() / "storesignal-ai"
AUDIT_LOG = ROOT / "data" / "processed" / "audit.log"
AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
IDEMPOTENCY_DB = ROOT / "data" / "processed" / "idempotency.jsonl"
IDEMPOTENCY_DB.parent.mkdir(parents=True, exist_ok=True)

_cfg = load_config()

ROLE_KEYS = {
    _cfg.api.api_key: "admin",
    "reviewer-key-demo": "reviewer",
    "store-manager-key-demo": "store_manager",
    "regional-manager-key-demo": "regional_manager",
}

PERMISSIONS = {
    "reviewer":          {"review_alert", "assign_alert", "record_action"},
    "store_manager":     {"review_alert", "assign_alert", "record_action"},
    "regional_manager":  {"review_alert", "assign_alert", "record_action", "generate_brief"},
    "admin":             {"review_alert", "assign_alert", "record_action", "generate_brief", "reset", "ingest"},
}


def resolve_role(api_key):
    if not api_key:
        return "anonymous" if not _cfg.api.require_api_key else None
    return ROLE_KEYS.get(api_key)


def has_permission(role, permission):
    return permission in PERMISSIONS.get(role, set())


def audit(event_type, actor, detail="", **extra):
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event_type": event_type,
        "actor": actor,
        "detail": detail,
    }
    rec.update(extra)
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


async def require_api_key(
    x_api_key: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
):
    role = resolve_role(x_api_key)
    if role is None:
        audit("auth_failed", "unknown", "invalid or missing api key",
              request_id=x_request_id or "?")
        raise HTTPException(status_code=401, detail="invalid or missing API key")
    return {"role": role, "request_id": x_request_id}


def require_permission(permission):
    async def _dep(
        x_api_key: str | None = Header(default=None),
        x_request_id: str | None = Header(default=None),
    ):
        role = resolve_role(x_api_key)
        if role is None:
            raise HTTPException(status_code=401, detail="invalid or missing API key")
        if not has_permission(role, permission):
            audit("permission_denied", role, permission,
                  request_id=x_request_id or "?")
            raise HTTPException(
                status_code=403,
                detail=f"role '{role}' lacks permission '{permission}'",
            )
        return {"role": role, "request_id": x_request_id}
    return _dep


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        incoming = request.headers.get("x-request-id")
        cid = incoming or f"req-{uuid.uuid4().hex[:12]}"
        request.state.correlation_id = cid
        response = await call_next(request)
        response.headers["X-Request-ID"] = cid
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, per_minute: int = 120):
        super().__init__(app)
        self.per_minute = per_minute
        self.window = 60.0
        self.buckets = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable):
        client = request.client.host if request.client else "unknown"
        now = time.time()
        q = self.buckets[client]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.per_minute:
            audit("rate_limited", client, request.url.path)
            return JSONResponse(status_code=429,
                                content={"detail": "rate limit exceeded"})
        q.append(now)
        return await call_next(request)


def _load_idempotency():
    if not IDEMPOTENCY_DB.exists():
        return {}
    seen = {}
    with open(IDEMPOTENCY_DB, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            seen[rec["key"]] = rec
    return seen


def check_idempotency(key):
    if not key:
        return None
    return _load_idempotency().get(key)


def store_idempotency(key, endpoint, response):
    if not key:
        return
    rec = {
        "key": key,
        "endpoint": endpoint,
        "response": response,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(IDEMPOTENCY_DB, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def install_security(app):
    app.add_middleware(RateLimitMiddleware,
                       per_minute=_cfg.api.rate_limit_per_minute)
    app.add_middleware(CorrelationIdMiddleware)

    @app.exception_handler(HTTPException)
    async def http_exc_handler(request: Request, exc: HTTPException):
        cid = getattr(request.state, "correlation_id", "?")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "status_code": exc.status_code,
                "detail": exc.detail,
                "request_id": cid,
            },
            headers={"X-Request-ID": cid},
        )

    audit("startup", "system",
          f"rate_limit={_cfg.api.rate_limit_per_minute}/min",
          api_key_required=_cfg.api.require_api_key,
          roles=list(PERMISSIONS.keys()))

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

from fastapi import Header, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from storesignal import auth_oidc
from storesignal.config_loader import load_config
from storesignal.paths import (
    CODE_ROOT,
    PROCESSED_DIR,
)

ROOT = CODE_ROOT
AUDIT_LOG = PROCESSED_DIR / "audit.log"
AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
IDEMPOTENCY_DB = PROCESSED_DIR / "idempotency.jsonl"
IDEMPOTENCY_DB.parent.mkdir(parents=True, exist_ok=True)

_cfg = load_config()

ROLE_KEYS = {
    _cfg.api.api_key:               "admin",
    "reviewer-key-demo":            "reviewer",
    "store-manager-key-demo":       "store_manager",
    "regional-manager-key-demo":    "regional_ops_lead",
    "food-safety-key-demo":         "food_safety_risk",
    "supply-chain-key-demo":        "supply_chain",
    "hr-key-demo":                  "hr_sensitive",
    "analyst-key-demo":             "analyst",
}

_READ = {"read_overview", "read_incidents", "read_alerts", "read_trends",
         "read_stores", "read_briefs", "read_audit", "read_evaluation",
         "read_data_health"}
_WRITE = {"review_alert", "assign_alert", "record_action"}

PERMISSIONS = {
    "regional_ops_lead": _READ | _WRITE | {"generate_brief", "read_reports"},
    "store_manager":     _READ | _WRITE,
    "food_safety_risk":  _READ | _WRITE | {"review_mandatory_risk"},
    "supply_chain":      _READ | _WRITE,
    "hr_sensitive":      {"read_incidents", "read_alerts", "review_alert",
                          "assign_alert", "record_action", "review_mandatory_risk"},
    "reviewer":          _READ | _WRITE,
    "analyst":           _READ | {"run_pipeline", "run_evaluation",
                                  "annotate_classification"},
    "admin":             _READ | _WRITE | {"generate_brief", "reset", "ingest",
                                            "manage_config", "read_reports",
                                            "run_pipeline", "run_evaluation",
                                            "annotate_classification",
                                            "review_mandatory_risk"},
}

SENSITIVE_CATEGORIES = {"staff_misconduct", "staff_conduct", "allergen_or_labeling"}


def is_sensitive_category(cat: str) -> bool:
    return cat in SENSITIVE_CATEGORIES


def can_access_sensitive(role: str) -> bool:
    return role in {"admin", "hr_sensitive", "food_safety_risk"}


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
    authorization: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
):
    # OIDC path (takes precedence when enabled)
    if auth_oidc.enabled() and authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        try:
            claims = auth_oidc.verify_token(token)
        except auth_oidc.OIDCError as e:
            audit("auth_failed", "oidc", f"token rejected: {e}",
                  request_id=x_request_id or "?")
            raise HTTPException(status_code=401, detail=f"invalid token: {e}")
        role = auth_oidc.role_from_claims(claims)
        if role is None:
            audit("auth_failed", claims.get("sub", "unknown"),
                  "token has no recognized role",
                  request_id=x_request_id or "?")
            raise HTTPException(status_code=403, detail="no recognized role")
        return {"role": role, "request_id": x_request_id,
                "sub": claims.get("sub"), "via": "oidc"}

    # Legacy static key path
    role = resolve_role(x_api_key)
    if role is None:
        audit("auth_failed", "unknown", "invalid or missing api key",
              request_id=x_request_id or "?")
        raise HTTPException(status_code=401, detail="invalid or missing API key")
    return {"role": role, "request_id": x_request_id, "via": "static_key"}


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

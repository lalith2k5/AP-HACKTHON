"""Provider-agnostic OIDC token verifier.

Works with any standards-compliant OIDC provider: Auth0, Keycloak,
Google Workspace, Azure AD / Entra ID, Okta, etc.

Enable by setting:
    STORESIGNAL_OIDC_ENABLED=true
    STORESIGNAL_OIDC_ISSUER=https://your-idp.example.com/realms/storesignal
    STORESIGNAL_OIDC_AUDIENCE=storesignal-api
    STORESIGNAL_OIDC_ROLE_CLAIM=roles   # JWT claim that carries role(s)

When disabled, the legacy static x-api-key path is used unchanged.
"""
from __future__ import annotations

import os
import time
from typing import Any

import httpx
import jwt

# JWKS cache
_JWKS: dict[str, Any] = {"keys": [], "fetched_at": 0.0}
_JWKS_TTL = 3600.0


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


def enabled() -> bool:
    return _env_bool("STORESIGNAL_OIDC_ENABLED", False)


def _issuer() -> str:
    return os.environ.get("STORESIGNAL_OIDC_ISSUER", "").rstrip("/")


def _audience() -> str:
    return os.environ.get("STORESIGNAL_OIDC_AUDIENCE", "storesignal-api")


def _role_claim() -> str:
    return os.environ.get("STORESIGNAL_OIDC_ROLE_CLAIM", "roles")


def _discovery_url() -> str:
    return f"{_issuer()}/.well-known/openid-configuration"


def _jwks_url() -> str:
    explicit = os.environ.get("STORESIGNAL_OIDC_JWKS_URL")
    if explicit:
        return explicit
    with httpx.Client(timeout=10.0) as c:
        r = c.get(_discovery_url())
        r.raise_for_status()
        return r.json()["jwks_uri"]


def _fetch_jwks(force: bool = False) -> list[dict]:
    now = time.time()
    if not force and _JWKS["keys"] and now - _JWKS["fetched_at"] < _JWKS_TTL:
        return _JWKS["keys"]
    with httpx.Client(timeout=10.0) as c:
        r = c.get(_jwks_url())
        r.raise_for_status()
        keys = r.json().get("keys", [])
    _JWKS["keys"] = keys
    _JWKS["fetched_at"] = now
    return keys


def _key_for_kid(kid: str) -> dict | None:
    for k in _fetch_jwks():
        if k.get("kid") == kid:
            return k
    # Cache miss → refetch once
    for k in _fetch_jwks(force=True):
        if k.get("kid") == kid:
            return k
    return None


class OIDCError(Exception):
    pass


def verify_token(token: str) -> dict:
    """Verify a JWT and return the claims. Raises OIDCError on failure."""
    try:
        headers = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as e:
        raise OIDCError(f"malformed token: {e}") from e

    kid = headers.get("kid")
    if not kid:
        raise OIDCError("token missing kid header")

    key = _key_for_kid(kid)
    if key is None:
        raise OIDCError(f"no JWKS key matches kid={kid}")

    try:
        pubkey = jwt.algorithms.RSAAlgorithm.from_jwk(key)
    except Exception as e:
        raise OIDCError(f"could not build public key: {e}") from e

    try:
        claims = jwt.decode(
            token,
            pubkey,
            algorithms=[key.get("alg", "RS256")],
            audience=_audience(),
            issuer=_issuer(),
            options={"verify_exp": True, "verify_aud": True, "verify_iss": True},
        )
    except jwt.ExpiredSignatureError as e:
        raise OIDCError("token expired") from e
    except jwt.InvalidTokenError as e:
        raise OIDCError(f"invalid token: {e}") from e

    return claims


def role_from_claims(claims: dict) -> str | None:
    """Extract a StoreSignal role from the configured claim.

    Returns the first value that matches a known role. Accepts list or
    space-delimited string. If nothing matches, returns None.
    """
    known = {
        "admin", "analyst", "regional_ops_lead", "store_manager",
        "hr_sensitive", "food_safety_risk", "reviewer", "supply_chain",
    }
    raw = claims.get(_role_claim())
    if raw is None:
        return None
    if isinstance(raw, str):
        candidates = raw.replace(",", " ").split()
    elif isinstance(raw, list):
        candidates = [str(x) for x in raw]
    else:
        return None
    for c in candidates:
        if c in known:
            return c
    return None

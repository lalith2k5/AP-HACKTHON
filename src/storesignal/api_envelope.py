"""
StoreSignal AI - API response envelope + cursor pagination helpers (spec 14.1/14.4).
"""
from __future__ import annotations
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def error_response(
    code: str,
    message: str,
    request_id: str | None = None,
    status_code: int = 400,
    details: list[dict] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
                "details": details or [],
            }
        },
    )


def install(app) -> None:
    """Attach envelope-style exception handlers to a FastAPI app."""

    @app.exception_handler(StarletteHTTPException)
    async def _http_exc(request: Request, exc: StarletteHTTPException):
        rid = request.headers.get("x-request-id")
        code = {400: "BAD_REQUEST", 401: "UNAUTHENTICATED", 403: "FORBIDDEN",
                404: "NOT_FOUND", 409: "CONFLICT", 413: "PAYLOAD_TOO_LARGE",
                422: "VALIDATION_ERROR", 429: "RATE_LIMITED",
                500: "INTERNAL_ERROR"}.get(exc.status_code, "ERROR")
        return error_response(code, str(exc.detail), rid, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _val_exc(request: Request, exc: RequestValidationError):
        rid = request.headers.get("x-request-id")
        details = [{"field": ".".join(str(x) for x in e["loc"]), "issue": e["msg"]}
                   for e in exc.errors()]
        return error_response("VALIDATION_ERROR",
                              "request body failed schema validation",
                              rid, 422, details)


def paginate(items: list[Any], cursor: int = 0, limit: int = 50) -> dict:
    limit = max(1, min(limit, 200))
    start = max(0, cursor)
    end = start + limit
    page = items[start:end]
    return {
        "items": page,
        "next_cursor": end if end < len(items) else None,
        "count": len(page),
        "total": len(items),
    }

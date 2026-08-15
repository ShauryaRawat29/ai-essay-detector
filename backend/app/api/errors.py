"""Shared API error helpers (standard error format per api-contracts skill).

Error body: {"error": {"code", "message", "details"?}}
No stack traces are ever included in responses.
"""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.api.errors")


def error_response(
    code: str, message: str, details: dict | None = None
) -> dict:
    body: dict = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return body


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_response(
            "VALIDATION_ERROR",
            "Request validation failed.",
            details=jsonable_encoder(exc.errors()),
        ),
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    # Preserve the standard error shape for HTTP errors raised by routes.
    code = {
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        503: "MODEL_UNAVAILABLE",
    }.get(exc.status_code, "INTERNAL_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(code, str(exc.detail)),
        headers=exc.headers,
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception("Unhandled exception during request", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=error_response(
            "INTERNAL_ERROR", "An unexpected error occurred."
        ),
    )

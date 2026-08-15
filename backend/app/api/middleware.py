"""ASGI middleware: API version header + rate limiting (ADR-006).

Rate-limit headers (``X-RateLimit-*``, ``X-API-Version``) are added to every
HTTP response. Requests over the per-IP limit receive a 429 with the standard
error format and a ``Retry-After`` header.
"""

from __future__ import annotations

import time

from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api.errors import error_response
from app.api.rate_limit import InMemorySlidingWindowLimiter

API_VERSION = "1.0"


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp, limiter: InMemorySlidingWindowLimiter) -> None:
        self.app = app
        self.limiter = limiter

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = scope
        client = request.get("client") or ("unknown", None)
        ip = client[0] if isinstance(client, tuple) else "unknown"

        allowed, remaining, limit, reset = self.limiter.check(ip)
        common_headers = {
            "X-API-Version": API_VERSION,
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset),
        }

        if not allowed:
            headers = dict(common_headers)
            headers["Retry-After"] = str(max(reset - int(time.time()), 0))
            response = JSONResponse(
                status_code=429,
                content=error_response(
                    "RATE_LIMITED",
                    "Rate limit exceeded, please retry later.",
                ),
                headers=headers,
            )
            await response(scope, receive, send)
            return

        async def send_with_headers(message) -> None:
            if message["type"] == "http.response.start":
                existing = {k.decode(): v.decode() for k, v in message.get("headers", [])}
                existing.update(common_headers)
                message["headers"] = [
                    (k.encode(), v.encode()) for k, v in existing.items()
                ]
            await send(message)

        await self.app(scope, receive, send_with_headers)

"""In-memory sliding-window rate limiter (ADR-006, dev-only).

Single-process only. A Redis-backed limiter is required for staging/production
(see ADR-006). The limiter is implemented here rather than via the
``fastapi-throttle`` package so it is deterministic and trivially testable; the
ADR's architectural choice (in-memory sliding window, 60 req/min/IP) is kept.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque


class InMemorySlidingWindowLimiter:
    """Per-IP sliding window rate limiter.

    ``check`` returns ``(allowed, remaining, limit, reset_timestamp)`` and
    records a hit for the IP when the request is allowed.
    """

    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        if limit <= 0:
            raise ValueError("limit must be > 0")
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(
        self, ip: str, now: float | None = None
    ) -> tuple[bool, int, int, int]:
        now = time.time() if now is None else now
        window = self._hits[ip]
        cutoff = now - self.window_seconds
        while window and window[0] <= cutoff:
            window.popleft()
        reset = int(now) + self.window_seconds
        if len(window) >= self.limit:
            return False, 0, self.limit, reset
        window.append(now)
        remaining = max(self.limit - len(window), 0)
        return True, remaining, self.limit, reset

    def reset(self) -> None:
        self._hits.clear()

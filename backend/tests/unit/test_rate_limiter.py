from app.api.rate_limit import InMemorySlidingWindowLimiter


def test_allows_up_to_limit():
    limiter = InMemorySlidingWindowLimiter(limit=2, window_seconds=60)
    t = 1_000.0
    assert limiter.check("1.2.3.4", now=t) == (True, 1, 2, 1060)
    assert limiter.check("1.2.3.4", now=t + 1) == (True, 0, 2, 1061)
    allowed, remaining, limit, reset = limiter.check("1.2.3.4", now=t + 2)
    assert allowed is False
    assert remaining == 0


def test_per_ip_isolation():
    limiter = InMemorySlidingWindowLimiter(limit=1, window_seconds=60)
    t = 1_000.0
    assert limiter.check("a", now=t)[0] is True
    assert limiter.check("a", now=t + 1)[0] is False
    assert limiter.check("b", now=t + 2)[0] is True


def test_window_expiry_frees_slots():
    limiter = InMemorySlidingWindowLimiter(limit=1, window_seconds=60)
    t = 1_000.0
    assert limiter.check("ip", now=t)[0] is True
    assert limiter.check("ip", now=t + 1)[0] is False
    # After the window elapses the slot expires.
    assert limiter.check("ip", now=t + 61)[0] is True


def test_reset_clears_all():
    limiter = InMemorySlidingWindowLimiter(limit=1, window_seconds=60)
    t = 1_000.0
    limiter.check("ip", now=t)
    limiter.check("ip", now=t + 1)
    limiter.reset()
    assert limiter.check("ip", now=t + 2)[0] is True


def test_invalid_limit():
    try:
        InMemorySlidingWindowLimiter(limit=0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for limit=0")

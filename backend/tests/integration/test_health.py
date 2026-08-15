import platform

from app import __version__
from app.config import LM_MODEL_REVISION_DEFAULT
from app.models.device import detect_device


def test_health_ok(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "ok"
    assert data["app_version"] == __version__
    assert data["python_version"] == platform.python_version()
    assert data["environment"] == "development"
    # Feature orchestration is served by /api/v1/analyze.
    assert data["feature_version"] == "f0.3.0"

    device = data["device"]
    assert set(device) == {
        "cuda_available",
        "device_count",
        "gpu_name",
        "cuda_version",
        "torch_version",
        "device",
    }
    assert device["device"] in {"cpu", "cuda:0"}

    models = data["models"]
    assert "lm_instrument" in models
    lm = models["lm_instrument"]
    assert lm["name"] == "gpt2-medium"
    assert lm["kind"] == "lm_instrument"
    assert lm["revision"] == LM_MODEL_REVISION_DEFAULT
    assert lm["status"] == "not_loaded"
    assert lm["loaded"] is False


def test_health_never_loads_models(client):
    """The health endpoint must never load GPT-2; status stays not_loaded."""
    for _ in range(3):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["models"]["lm_instrument"]["status"] == "not_loaded"


def test_health_reports_gpu_when_available(client):
    data = client.get("/api/v1/health").json()
    device = data["device"]
    if detect_device().cuda_available:
        assert device["cuda_available"] is True
        assert device["gpu_name"] is not None
    else:
        assert device["cuda_available"] is False
        assert device["gpu_name"] is None


def test_health_headers(client):
    resp = client.get("/api/v1/health")
    assert resp.headers["x-api-version"] == "1.0"
    assert resp.headers["x-ratelimit-limit"] == "10000"
    assert int(resp.headers["x-ratelimit-remaining"]) <= 10000
    assert resp.headers["x-ratelimit-reset"]


def test_rate_limit_returns_429_with_headers(low_limit_client):
    client = low_limit_client
    first = client.get("/api/v1/health")
    assert first.status_code == 200
    second = client.get("/api/v1/health")
    assert second.status_code == 200
    third = client.get("/api/v1/health")
    assert third.status_code == 429
    assert third.headers["retry-after"]
    assert third.headers["x-ratelimit-remaining"] == "0"
    body = third.json()
    assert body["error"]["code"] == "RATE_LIMITED"
    assert body["error"]["message"]


def test_unknown_route_returns_404(client):
    resp = client.get("/api/v1/nope")
    assert resp.status_code == 404


def test_cors_header_for_allowed_origin(client):
    resp = client.get(
        "/api/v1/health", headers={"Origin": "http://localhost:3000"}
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_error_format_no_stacktrace(client):
    """Validation errors use the standard error shape and no traceback."""
    resp = client.post("/api/v1/analyze", json={})
    # Missing required field -> validation error (422), not a crash.
    assert resp.status_code == 422
    assert "Traceback" not in resp.text

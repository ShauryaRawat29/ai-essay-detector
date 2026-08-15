import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client():
    """Test client with a generous rate limit so ordinary tests never trip it."""
    settings = Settings(rate_limit_per_minute=10000)
    app = create_app(settings)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def low_limit_client():
    """Test client configured with a tiny rate limit for 429 coverage."""
    settings = Settings(rate_limit_per_minute=2)
    app = create_app(settings)
    with TestClient(app) as c:
        yield c

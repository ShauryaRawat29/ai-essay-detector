from app.config import LM_MODEL_REVISION_DEFAULT, Settings


def test_defaults(monkeypatch):
    for key in (
        "ENVIRONMENT",
        "API_HOST",
        "API_PORT",
        "FEATURE_VERSION",
        "MODEL_VERSION",
        "RATE_LIMIT_PER_MINUTE",
        "LM_MODEL_NAME",
        "LM_MODEL_REVISION",
    ):
        monkeypatch.delenv(key, raising=False)

    s = Settings.from_env()
    assert s.environment == "development"
    assert s.api_host == "0.0.0.0"
    assert s.api_port == 8000
    # Feature pipeline not implemented yet -> None in health responses.
    assert s.feature_version is None
    assert s.default_model_version == "0.1.0"
    assert s.rate_limit_per_minute == 60
    assert s.lm_model_name == "gpt2-medium"
    assert s.lm_model_revision == LM_MODEL_REVISION_DEFAULT


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("FEATURE_VERSION", "0.2.0")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "10")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("ENVIRONMENT", "test")

    s = Settings.from_env()
    assert s.feature_version == "0.2.0"
    assert s.rate_limit_per_minute == 10
    assert s.api_port == 9000
    assert s.environment == "test"


def test_empty_feature_version_means_none(monkeypatch):
    monkeypatch.setenv("FEATURE_VERSION", "")
    assert Settings.from_env().feature_version is None

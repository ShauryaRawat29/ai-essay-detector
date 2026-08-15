import pytest

from app.models.loader import ModelRegistry, ModelSpec, ModelStatus


def make_spec(**overrides) -> ModelSpec:
    params = {
        "key": "test_model",
        "name": "test",
        "version": "0.1.0",
        "kind": "classifier",
    }
    params.update(overrides)
    return ModelSpec(**params)


def test_register_and_status():
    registry = ModelRegistry()
    spec = make_spec(key="lm", name="gpt2-medium", kind="lm_instrument")
    registry.register(spec)

    status = registry.status()
    assert "lm" in status
    state = status["lm"]
    assert state["name"] == "gpt2-medium"
    assert state["status"] == "not_loaded"
    assert state["loaded"] is False


def test_duplicate_register_raises():
    registry = ModelRegistry()
    registry.register(make_spec(key="a"))
    with pytest.raises(ValueError):
        registry.register(make_spec(key="a"))


def test_get_unknown_raises():
    registry = ModelRegistry()
    with pytest.raises(KeyError):
        registry.get("missing")


def test_mark_ready_and_is_ready():
    registry = ModelRegistry(device="cpu")
    registry.register(make_spec(key="a"))
    assert registry.is_ready("a") is False
    registry.mark_ready("a")
    assert registry.is_ready("a") is True
    state = registry.get("a")
    assert state.status == ModelStatus.READY
    assert state.loaded_at is not None
    assert registry.status()["a"]["loaded"] is True


def test_mark_error():
    registry = ModelRegistry()
    registry.register(make_spec(key="a"))
    registry.mark_error("a", "failed to download")
    state = registry.get("a")
    assert state.status == ModelStatus.ERROR
    assert state.error == "failed to download"
    assert registry.status()["a"]["loaded"] is False


def test_device_property_lazy_resolution():
    registry = ModelRegistry(device="cuda:0")
    assert registry.device == "cuda:0"

    registry2 = ModelRegistry()
    assert registry2.device in {"cpu", "cuda:0"}

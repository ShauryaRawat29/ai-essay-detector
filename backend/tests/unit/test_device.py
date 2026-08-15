from app.models.device import detect_device


def test_detect_device_shape():
    info = detect_device()
    assert isinstance(info.cuda_available, bool)
    assert info.device_count >= 0
    assert info.device in {"cpu", "cuda:0"}
    if info.cuda_available:
        assert info.device_count > 0
        assert info.gpu_name is not None
        assert info.device == "cuda:0"


def test_to_dict_matches_fields():
    info = detect_device()
    data = info.to_dict()
    assert set(data) == {
        "cuda_available",
        "device_count",
        "gpu_name",
        "cuda_version",
        "torch_version",
        "device",
    }

import pytest

from app.features.registry import (
    FEATURE_REGISTRY_VERSION,
    FeatureMatrix,
    FeatureRegistry,
    extract_essay,
)

ESSAY = (
    "The quiet student carefully reviewed the lengthy essay before submitting it. "
    "She checked every paragraph twice. "
    "Finally, she pressed send."
)


def test_registry_version():
    assert FeatureRegistry().version == FEATURE_REGISTRY_VERSION
    assert FEATURE_REGISTRY_VERSION.startswith("f0.")


def test_registry_feature_names():
    registry = FeatureRegistry()
    names = set(registry.feature_names)
    assert "ttr" in names
    assert "pos_entropy" in names
    assert "mattr" in names
    assert "mtld" in names


def test_registry_status():
    registry = FeatureRegistry()
    assert registry.status("ttr") == "implemented"
    assert registry.status("perplexity") == "implemented"
    assert registry.status("hdd") == "planned"
    with pytest.raises(KeyError):
        registry.status("not_a_feature")


def test_extract_essay_shape():
    matrix = extract_essay(ESSAY)
    assert isinstance(matrix, FeatureMatrix)
    assert matrix.feature_version == FEATURE_REGISTRY_VERSION
    # 3 sentences, window 3, stride 1 -> a single passage covering all three.
    assert len(matrix.sentence_features) == 3
    assert len(matrix.passage_features) == 1
    assert matrix.passage_sentence_indices == ((0, 1, 2),)


def test_sentence_feature_keys():
    matrix = extract_essay(ESSAY)
    keys = set(matrix.sentence_features[0])
    assert {
        "ttr",
        "word_length_mean",
        "flesch_kincaid_grade",
        "punct_density",
        "sent_len",
        "pos_entropy",
        "dep_depth_mean",
        "clause_density",
    } <= keys


def test_passage_aggregate_keys():
    matrix = extract_essay(ESSAY)
    pk = set(matrix.passage_features[0])
    assert "ttr_mean" in pk
    assert "ttr_std" in pk
    assert "ttr_p95" in pk
    assert "mattr" in pk
    assert "mtld" in pk


def test_extract_essay_deterministic():
    a = extract_essay(ESSAY)
    b = extract_essay(ESSAY)
    assert a.sentence_features == b.sentence_features
    assert a.passage_features == b.passage_features
    assert a.passage_sentence_indices == b.passage_sentence_indices

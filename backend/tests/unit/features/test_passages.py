import pytest

from app.features.passages import (
    Passage,
    PassageExtractor,
    aggregate,
    build_passages,
)


def test_build_passages_default_window_stride():
    result = build_passages(5, window=3, stride=1)
    assert result == (
        Passage((0, 1, 2)),
        Passage((1, 2, 3)),
        Passage((2, 3, 4)),
    )


def test_build_passages_stride_2():
    result = build_passages(5, window=3, stride=2)
    assert result == (
        Passage((0, 1, 2)),
        Passage((2, 3, 4)),
    )


def test_build_passages_empty():
    assert build_passages(0) == ()


def test_build_passages_window_larger_than_count():
    assert build_passages(2, window=3) == ()


def test_build_passages_respects_paragraph_breaks():
    result = build_passages(6, window=3, stride=1, paragraph_breaks=frozenset({0, 3}))
    assert result == (
        Passage((0, 1, 2)),
        Passage((3, 4, 5)),
    )


def test_aggregate_basic_stats():
    vecs = [{"x": 1.0}, {"x": 2.0}, {"x": 3.0}, {"x": 4.0}]
    out = aggregate(vecs, ("x",))
    assert out["x_mean"] == pytest.approx(2.5)
    assert out["x_std"] == pytest.approx(1.11803398875)  # population std
    assert out["x_cv"] == pytest.approx(0.4472135955)
    assert out["x_min"] == 1.0
    assert out["x_max"] == 4.0
    assert out["x_p5"] == pytest.approx(1.15)
    assert out["x_p25"] == pytest.approx(1.75)
    assert out["x_p50"] == pytest.approx(2.5)
    assert out["x_p75"] == pytest.approx(3.25)
    assert out["x_p95"] == pytest.approx(3.85)


def test_aggregate_single_value():
    out = aggregate([{"x": 2.5}], ("x",))
    assert out["x_mean"] == pytest.approx(2.5)
    assert out["x_std"] == 0.0
    assert out["x_min"] == out["x_max"] == 2.5


def test_mattr_all_unique_returns_one():
    tokens = " ".join(f"w{i}" for i in range(60))
    assert PassageExtractor().mattr(tokens) == pytest.approx(1.0)


def test_mattr_short_text_falls_back_to_ttr():
    tokens = "the cat sat on the mat"
    # 6 tokens, 5 unique -> plain TTR fallback
    assert PassageExtractor().mattr(tokens) == pytest.approx(5 / 6)


def test_mtld_repeated_pairs():
    # Hand-traced standard MTLD (factor 0.72): each segment closes at TTR<=0.72,
    # which for "a a a a b b b b" happens every 2 tokens -> 4 segments forward,
    # 4 backward -> MTLD 4.0.
    tokens = "a a a a b b b b"
    assert PassageExtractor().mtld(tokens) == pytest.approx(4.0)


def test_mtld_all_unique():
    # With all unique tokens TTR stays 1.0 (never <= 0.72), so one trailing
    # segment covers everything: ratio = (100/100)/0.72 per direction.
    tokens = " ".join(f"w{i}" for i in range(100))
    assert PassageExtractor().mtld(tokens) == pytest.approx(1.0 / 0.72)


def test_mtld_deterministic():
    tokens = "the quick brown fox jumps over the lazy dog and then the dog sleeps"
    assert PassageExtractor().mtld(tokens) == PassageExtractor().mtld(tokens)

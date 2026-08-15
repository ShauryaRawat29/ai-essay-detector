"""Unit tests for the baseline pipeline (ADR-004).

Synthetic inputs only: these tests verify the MACHINERY (bucketing, min-N
merging, statistics, artifact versioning, persistence). No real baselines are
claimed — real values require the human training split (dataset v0.1.0).
"""

import pytest

from app.evaluation.baselines import (
    BUCKET_NAMES,
    BaselineEssay,
    compute_baselines,
    default_filename,
    length_bucket,
    load_baselines,
    save_baselines,
)

FIXED_AT = "2026-08-15T00:00:00Z"


def make_essay(word_count, n_sentences, start_value=1.0):
    sents = tuple(
        {"perplexity": start_value + float(i), "ttr": 0.5}
        for i in range(n_sentences)
    )
    return BaselineEssay(word_count=word_count, sentence_features=sents)


# --- bucket assignment ------------------------------------------------------


def test_length_bucket_boundaries():
    assert length_bucket(0) == "short"
    assert length_bucket(199) == "short"
    assert length_bucket(200) == "standard"
    assert length_bucket(499) == "standard"
    assert length_bucket(500) == "long"
    assert length_bucket(799) == "long"
    assert length_bucket(800) == "xlong"
    assert length_bucket(5000) == "xlong"


# --- statistics --------------------------------------------------------------


def test_compute_baselines_stats():
    essays = [
        make_essay(300, 2, start_value=1.0),
        make_essay(400, 2, start_value=3.0),
    ]
    artifact = compute_baselines(essays, computed_at=FIXED_AT)
    # perplexity values across the two "standard" essays: [1,2,3,4]
    stats = artifact.buckets["standard"]["perplexity"]
    assert stats.n == 4
    assert stats.mean == pytest.approx(2.5)
    assert stats.std == pytest.approx(1.11803398875)
    assert stats.p5 == pytest.approx(1.15)
    assert stats.p25 == pytest.approx(1.75)
    assert stats.p50 == pytest.approx(2.5)
    assert stats.p75 == pytest.approx(3.25)
    assert stats.p95 == pytest.approx(3.85)
    # ttr is constant 0.5 -> std 0, all percentiles 0.5
    ttr = artifact.buckets["standard"]["ttr"]
    assert ttr.std == pytest.approx(0.0)
    assert ttr.p50 == pytest.approx(0.5)


def test_empty_buckets_reported_zero():
    essays = [make_essay(300, 3)]
    artifact = compute_baselines(essays, computed_at=FIXED_AT)
    assert artifact.n_essays["short"] == 0
    assert artifact.n_essays["standard"] == 1
    assert "short" not in artifact.buckets  # no samples survived
    assert "standard" in artifact.buckets


# --- min-N merge fallback ----------------------------------------------------


def test_merge_adjacent_buckets_left_to_right():
    # short: 5 sentences, standard: 10, long: 100. short and standard both fall
    # below min_n=30 and must merge into long.
    essays = [
        make_essay(100, 5),
        make_essay(300, 10),
        make_essay(600, 100),
    ]
    artifact = compute_baselines(essays, min_n=30, computed_at=FIXED_AT)
    assert set(artifact.buckets) == {"long"}
    assert artifact.buckets["long"]["perplexity"].n == 115
    assert len(artifact.merge_log) == 2
    assert any("short+standard" in m for m in artifact.merge_log)
    assert any("standard+long" in m for m in artifact.merge_log)


def test_single_small_bucket_kept_with_warning():
    essays = [make_essay(300, 2)]
    artifact = compute_baselines(essays, min_n=30, computed_at=FIXED_AT)
    assert set(artifact.buckets) == {"standard"}
    assert artifact.buckets["standard"]["perplexity"].n == 2
    assert artifact.merge_log == ["standard kept with N=2 < min_n=30 (no neighbors)"]


def test_min_n_satisfied_no_merge():
    essays = [make_essay(300, 40), make_essay(600, 50)]
    artifact = compute_baselines(essays, min_n=30, computed_at=FIXED_AT)
    assert set(artifact.buckets) == {"standard", "long"}
    assert artifact.merge_log == []


# --- artifact versioning / persistence ---------------------------------------


def test_artifact_records_versions():
    artifact = compute_baselines(
        [make_essay(300, 40)],
        feature_version="f0.3.0",
        dataset_version="v0.1.0",
        computed_at=FIXED_AT,
    )
    assert artifact.schema_version == "1.0"
    assert artifact.feature_version == "f0.3.0"
    assert artifact.dataset_version == "v0.1.0"
    assert artifact.computed_at == FIXED_AT


def test_default_filename():
    assert default_filename("f0.3.0") == "baselines_f0.3.0.json"


def test_save_load_roundtrip(tmp_path):
    artifact = compute_baselines([make_essay(300, 40)], computed_at=FIXED_AT)
    path = save_baselines(artifact, tmp_path / default_filename("f0.3.0"))
    loaded = load_baselines(path)
    assert loaded.to_dict() == artifact.to_dict()


# --- determinism / edge cases ------------------------------------------------


def test_compute_deterministic():
    a = compute_baselines([make_essay(300, 40)], computed_at=FIXED_AT)
    b = compute_baselines([make_essay(300, 40)], computed_at=FIXED_AT)
    assert a.to_dict() == b.to_dict()


def test_empty_essays_raises():
    with pytest.raises(ValueError):
        compute_baselines([], computed_at=FIXED_AT)


def test_feature_keys_preserved():
    essay = BaselineEssay(
        word_count=300,
        sentence_features=({"perplexity": 1.0, "sent_len": 5}, {"perplexity": 2.0}),
    )
    artifact = compute_baselines([essay], min_n=1, computed_at=FIXED_AT)
    feats = artifact.buckets["standard"]
    assert "perplexity" in feats
    assert "sent_len" in feats
    assert feats["perplexity"].n == 2
    assert feats["sent_len"].n == 1


def test_bucket_names_constant():
    assert BUCKET_NAMES == ("short", "standard", "long", "xlong")

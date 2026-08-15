from __future__ import annotations

from app.evaluation.baselines import BaselineArtifact, BucketStats
from app.features.base import FeatureMatrix
from app.pipeline.analysis import score_essay


def _stats(mean: float = 100.0, std: float = 10.0) -> BucketStats:
    return BucketStats(n=40, mean=mean, std=std, p5=80.0, p25=95.0, p50=100.0, p75=105.0, p95=120.0)


def _matrix(sentence_features, passage_features=(), indices=()) -> FeatureMatrix:
    return FeatureMatrix(
        feature_version="f0.3.0",
        sentence_features=tuple(sentence_features),
        passage_features=tuple(passage_features),
        passage_sentence_indices=tuple(indices),
    )


def _baselines(bucket_feats=None) -> BaselineArtifact:
    feats = (
        {"perplexity": _stats(), "ttr": _stats(mean=0.5, std=0.1)}
        if bucket_feats is None
        else bucket_feats
    )
    return BaselineArtifact(
        feature_version="f0.3.0",
        dataset_version="v0.1.0",
        n_essays={"short": 1, "standard": 2, "long": 3, "xlong": 0},
        n_sentences={"short": 5, "standard": 6, "long": 7, "xlong": 0},
        buckets={"standard": feats},
    )


def test_scores_sentence_against_baseline_bucket() -> None:
    baselines = _baselines()
    # perplexity 40 is -6 sigma from the baseline mean of 100 -> high signal
    matrix = _matrix([{"perplexity": 40.0, "ttr": 0.5}], (), ())
    outcome = score_essay(
        matrix, ("This is a sentence.",), baselines, word_count=300, token_count=380
    )

    sent = outcome.sentence_evidence[0]
    assert sent.evidence_strength == "high"
    assert sent.signal_count == 1
    assert sent.signals[0].feature == "perplexity"
    assert "machine-like" in sent.summary
    assert outcome.length_bucket == "standard"
    assert outcome.baseline_bucket == "standard"
    assert outcome.summary["signal_sentences"] == 1
    assert outcome.summary["high"] == 1


def test_typical_sentence_is_low() -> None:
    baselines = _baselines()
    matrix = _matrix([{"perplexity": 101.0, "ttr": 0.51}], (), ())
    outcome = score_essay(
        matrix, ("A normal sentence.",), baselines, word_count=300, token_count=370
    )

    sent = outcome.sentence_evidence[0]
    assert sent.evidence_strength == "low"
    assert sent.signal_count == 0
    assert "typical human baseline range" in sent.summary
    assert outcome.summary["signal_sentences"] == 0


def test_missing_bucket_falls_back_and_reports_limit() -> None:
    baselines = _baselines()
    matrix = _matrix([{"perplexity": 40.0}], (), ())
    outcome = score_essay(matrix, ("An essay.",), baselines, word_count=900, token_count=1100)

    assert outcome.length_bucket == "xlong"
    assert outcome.baseline_bucket == "standard"
    assert outcome.fallback_bucket == "standard"
    assert any("no baseline bucket" in lim for lim in outcome.limitations)


def test_unknown_features_are_not_scored() -> None:
    baselines = _baselines()
    matrix = _matrix([{"perplexity": 40.0, "made_up_feature": 1.0}], (), ())
    outcome = score_essay(matrix, ("A sentence.",), baselines, word_count=300, token_count=360)

    sent = outcome.sentence_evidence[0]
    names = [s.feature for s in sent.signals]
    assert "made_up_feature" not in names
    assert sent.evidence_strength == "high"


def test_no_comparable_features_is_uncertain() -> None:
    baselines = _baselines({})
    matrix = _matrix([{"perplexity": 40.0}], (), ())
    outcome = score_essay(matrix, ("A sentence.",), baselines, word_count=300, token_count=360)

    sent = outcome.sentence_evidence[0]
    assert sent.evidence_strength == "uncertain"
    assert sent.signals == ()
    assert outcome.summary["uncertain"] == 1
    assert any("could not be compared" in lim for lim in outcome.limitations)


def test_passage_evidence_aligns_to_sentence_indices() -> None:
    baselines = _baselines()
    matrix = _matrix(
        [{"perplexity": 40.0}, {"perplexity": 102.0}],
        [{"perplexity": 70.0, "mattr": 0.7}],
        ((0, 1),),
    )
    outcome = score_essay(
        matrix,
        ("First sentence here.", "Second sentence here."),
        baselines,
        word_count=300,
        token_count=380,
    )

    assert len(outcome.passage_evidence) == 1
    passage = outcome.passage_evidence[0]
    assert passage.sentence_indices == (0, 1)
    assert passage.evidence_strength == "high"
    assert passage.signal_count == 1


def test_empty_sentences_report_counts() -> None:
    baselines = _baselines()
    matrix = _matrix([], (), ())
    outcome = score_essay(matrix, (), baselines, word_count=10, token_count=20)

    assert outcome.summary["sentence_count"] == 0
    assert outcome.sentence_evidence == ()

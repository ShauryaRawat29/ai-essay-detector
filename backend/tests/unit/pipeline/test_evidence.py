from __future__ import annotations

import pytest

from app.evaluation.baselines import BucketStats
from app.pipeline.evidence import build_signal_evidence


def stats(mean: float = 100.0, std: float = 10.0) -> BucketStats:
    return BucketStats(n=40, mean=mean, std=std, p5=80.0, p25=95.0, p50=100.0, p75=105.0, p95=120.0)


def test_evidence_cites_measured_value_and_human_baseline() -> None:
    evidence = build_signal_evidence("perplexity", 70.0, stats())

    assert evidence.evidence == "high"
    assert evidence.z_score == pytest.approx(-3.0)
    assert "perplexity: 70.00" in evidence.summary
    assert "human baseline: 100.00 ± 10.00" in evidence.summary


def test_evidence_marks_values_without_variance_uncertain() -> None:
    evidence = build_signal_evidence("token_entropy_mean", 2.0, stats(std=0.0))

    assert evidence.evidence == "uncertain"
    assert "variance unavailable" in evidence.summary


def test_evidence_marks_near_baseline_signal_low() -> None:
    evidence = build_signal_evidence("ttr", 104.0, stats())

    assert evidence.evidence == "low"
    assert evidence.direction == "higher"

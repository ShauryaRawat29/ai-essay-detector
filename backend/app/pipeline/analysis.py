"""Evidence scoring of a FeatureMatrix against human baselines.

Pure scoring: no model loads, no IO. Consumes a :class:`FeatureMatrix` (from
the feature registry) and a :class:`BaselineArtifact` (ADR-004 human baselines)
and produces sentence- and passage-level evidence in the API response shape.

Evidence strength is derived ONLY from measured feature values compared to
human-reference distributions (z-scores). No authorship verdict is produced —
the response reports machine-like signals and uncertainty.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from app.evaluation.baselines import BaselineArtifact, BucketStats, length_bucket
from app.features.base import FeatureMatrix
from app.pipeline.evidence import build_signal_evidence

EvidenceLevel = Literal["low", "medium", "high", "uncertain"]


@dataclass(frozen=True)
class Signal:
    feature: str
    value: float
    baseline_mean: float
    baseline_std: float
    z_score: float | None
    direction: Literal["lower", "higher", "typical", "unknown"]
    evidence: EvidenceLevel
    summary: str


@dataclass(frozen=True)
class SentenceEvidence:
    index: int
    text: str
    signals: tuple[Signal, ...]
    signal_count: int
    evidence_strength: EvidenceLevel
    summary: str


@dataclass(frozen=True)
class PassageEvidence:
    sentence_indices: tuple[int, ...]
    signals: tuple[Signal, ...]
    signal_count: int
    evidence_strength: EvidenceLevel
    summary: str


@dataclass(frozen=True)
class AnalysisOutcome:
    sentence_evidence: tuple[SentenceEvidence, ...]
    passage_evidence: tuple[PassageEvidence, ...]
    length_bucket: str
    baseline_bucket: str
    fallback_bucket: str | None
    summary: dict
    limitations: tuple[str, ...]


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _evidence_level(signals: tuple[Signal, ...]) -> EvidenceLevel:
    if not signals:
        return "uncertain"
    if any(s.evidence == "high" for s in signals):
        return "high"
    if any(s.evidence == "medium" for s in signals):
        return "medium"
    return "low"


def _score_vector(
    feature_vec: dict[str, float], bucket_stats: dict[str, BucketStats]
) -> tuple[Signal, ...]:
    signals: list[Signal] = []
    for feature, value in feature_vec.items():
        stats = bucket_stats.get(feature)
        if stats is None or not _finite(value):
            continue
        ev = build_signal_evidence(feature, float(value), stats)
        signals.append(
            Signal(
                feature=feature,
                value=float(value),
                baseline_mean=float(stats.mean),
                baseline_std=float(stats.std),
                z_score=ev.z_score,
                direction=ev.direction,
                evidence=ev.evidence,
                summary=ev.summary,
            )
        )
    signals.sort(
        key=lambda s: abs(s.z_score) if s.z_score is not None else 0.0, reverse=True
    )
    return tuple(signals)


def _flagged(signals: tuple[Signal, ...]) -> int:
    return sum(1 for s in signals if s.evidence in ("medium", "high"))


def _unit_summary(kind: str, index: int, signals: tuple[Signal, ...]) -> str:
    n_scored = len(signals)
    flagged = _flagged(signals)
    if n_scored == 0:
        return (
            f"{kind} {index}: no features could be compared "
            "(baseline distribution unavailable)"
        )
    if flagged == 0:
        return (
            f"{kind} {index}: all {n_scored} scored features fall within the "
            "typical human baseline range"
        )
    top = signals[0]
    return (
        f"{kind} {index}: {flagged} of {n_scored} scored features show "
        f"machine-like signals (top: {top.feature} {top.direction} than the "
        "human baseline)"
    )


def _resolve_bucket(
    baselines: BaselineArtifact, word_count: int
) -> tuple[str, dict[str, BucketStats], str | None]:
    """Pick the baseline bucket for an essay, falling back to the nearest."""
    bucket = length_bucket(word_count)
    stats = baselines.buckets.get(bucket)
    if stats is not None:
        return bucket, stats, None
    for candidate in ("long", "standard", "short"):
        if candidate in baselines.buckets:
            return bucket, baselines.buckets[candidate], candidate
    return bucket, {}, None


def _limitations(
    outcome_bucket: str,
    baseline_bucket: str,
    fallback_bucket: str | None,
    n_sentences: int,
    n_uncertain: int,
    n_essays: dict[str, int],
) -> tuple[str, ...]:
    total_essays = sum(n_essays.values())
    limits = [
        (
            "This analysis measures machine-like writing signals using "
            "statistical and language-model measurements; it is evidence, "
            "not a claim of authorship."
        ),
        (
            "The language model is an instrument for measurable token signals "
            "only; it never judges whether text was written by an AI."
        ),
        (
            f"Human baselines come from the training split of dataset v0.1.0 "
            f"({total_essays} human admissions essays); behavior on other "
            "populations is unknown and may differ."
        ),
        (
            "Features without a baseline distribution are not scored; "
            "evidence covers only features comparable to the human sample."
        ),
        (
            "Short, heavily edited, or second-language essays can produce "
            "unusual signals for reasons unrelated to AI writing."
        ),
    ]
    if fallback_bucket is not None:
        limits.append(
            f"Essays in the '{outcome_bucket}' length range have no baseline "
            f"bucket; signals were compared to the '{fallback_bucket}' "
            "distribution instead."
        )
    if n_uncertain:
        limits.append(
            f"{n_uncertain} of {n_sentences} sentences could not be compared "
            "to any baseline and are reported as uncertain."
        )
    return tuple(limits)


def score_essay(
    feature_matrix: FeatureMatrix,
    sentences: tuple[str, ...],
    baselines: BaselineArtifact,
    *,
    word_count: int,
    token_count: int,
) -> AnalysisOutcome:
    """Score an extracted essay against human baselines (pure function)."""
    bucket, bucket_stats, fallback = _resolve_bucket(baselines, word_count)

    sentence_evidence: list[SentenceEvidence] = []
    for i, (text, vec) in enumerate(
        zip(sentences, feature_matrix.sentence_features, strict=True)
    ):
        signals = _score_vector(vec, bucket_stats)
        sentence_evidence.append(
            SentenceEvidence(
                index=i,
                text=text,
                signals=signals,
                signal_count=_flagged(signals),
                evidence_strength=_evidence_level(signals),
                summary=_unit_summary("sentence", i, signals),
            )
        )

    passage_evidence: list[PassageEvidence] = []
    for j, (indices, vec) in enumerate(
        zip(
            feature_matrix.passage_sentence_indices,
            feature_matrix.passage_features,
            strict=True,
        )
    ):
        signals = _score_vector(vec, bucket_stats)
        passage_evidence.append(
            PassageEvidence(
                sentence_indices=tuple(indices),
                signals=signals,
                signal_count=_flagged(signals),
                evidence_strength=_evidence_level(signals),
                summary=_unit_summary("passage", j, signals),
            )
        )

    count = {level: 0 for level in ("high", "medium", "low", "uncertain")}
    for s in sentence_evidence:
        count[s.evidence_strength] += 1
    signal_sentences = count["high"] + count["medium"]

    summary = {
        "sentence_count": len(sentence_evidence),
        "signal_sentences": signal_sentences,
        "high": count["high"],
        "medium": count["medium"],
        "low": count["low"],
        "uncertain": count["uncertain"],
    }
    limitations = _limitations(
        outcome_bucket=bucket,
        baseline_bucket=fallback or bucket,
        fallback_bucket=fallback,
        n_sentences=len(sentence_evidence),
        n_uncertain=count["uncertain"],
        n_essays=baselines.n_essays,
    )
    return AnalysisOutcome(
        sentence_evidence=tuple(sentence_evidence),
        passage_evidence=tuple(passage_evidence),
        length_bucket=bucket,
        baseline_bucket=fallback or bucket,
        fallback_bucket=fallback,
        summary=summary,
        limitations=limitations,
    )

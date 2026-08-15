from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.evaluation.baselines import BucketStats

EvidenceLevel = Literal["low", "medium", "high", "uncertain"]


@dataclass(frozen=True)
class SignalEvidence:
    feature: str
    value: float
    baseline_mean: float
    baseline_std: float
    z_score: float | None
    direction: Literal["lower", "higher", "typical", "unknown"]
    evidence: EvidenceLevel
    summary: str


def build_signal_evidence(feature: str, value: float, baseline: BucketStats) -> SignalEvidence:
    measured = float(value)
    mean = float(baseline.mean)
    std = float(baseline.std)
    if std <= 0:
        return SignalEvidence(
            feature=feature,
            value=measured,
            baseline_mean=mean,
            baseline_std=std,
            z_score=None,
            direction="unknown",
            evidence="uncertain",
            summary=(
                f"{feature}: {measured:.2f} (human baseline: {mean:.2f} ± {std:.2f}) — "
                "uncertain because baseline variance unavailable"
            ),
        )

    z_score = (measured - mean) / std
    magnitude = abs(z_score)
    if magnitude >= 2:
        level: EvidenceLevel = "high"
    elif magnitude >= 1:
        level = "medium"
    else:
        level = "low"
    if z_score < 0:
        direction: Literal["lower", "higher", "typical", "unknown"] = "lower"
    else:
        direction = "higher"
    if magnitude < 1:
        qualifier = "within the typical human baseline range"
    elif direction == "lower":
        qualifier = "unusually lower than the human baseline"
    else:
        qualifier = "unusually higher than the human baseline"
    return SignalEvidence(
        feature=feature,
        value=measured,
        baseline_mean=mean,
        baseline_std=std,
        z_score=z_score,
        direction=direction,
        evidence=level,
        summary=(
            f"{feature}: {measured:.2f} (human baseline: {mean:.2f} ± {std:.2f}) — "
            f"{qualifier}"
        ),
    )

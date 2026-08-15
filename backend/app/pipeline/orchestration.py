"""Detection pipeline orchestration (Phase 5): essay -> evidence.

Wires the deterministic feature extraction (feature registry), the human
baselines artifact (ADR-004), and the LM instrument into one ``analyze`` entry
point. The pipeline produces ONLY evidence-shaped output (feature values vs
human baselines) — never a probability or an authorship verdict.

The LM instrument is loaded lazily on the first analysis and reused across
requests; the health endpoint never triggers a load.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.config import BASE_DIR, Settings
from app.evaluation.baselines import BaselineArtifact, load_baselines
from app.features.base import tokenize
from app.features.lm_signals import LMSignalExtractor
from app.features.registry import FeatureRegistry
from app.models.lm_instrument import LMInstrument, LongDocumentError
from app.pipeline.analysis import score_essay


def find_baselines_path(feature_version: str) -> Path | None:
    """Newest persisted baseline artifact for a feature version (ADR-004)."""
    root = BASE_DIR / "data" / "baselines"
    candidates = sorted(
        root.glob(f"*/baselines_{feature_version}.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


class DetectionPipeline:
    """Owns the extractors, baselines, and instrument used for analysis."""

    def __init__(
        self,
        registry: FeatureRegistry | None = None,
        baselines: BaselineArtifact | None = None,
        baselines_path: Path | None = None,
    ) -> None:
        self.registry = registry or FeatureRegistry()
        self.baselines = baselines
        self.baselines_path = baselines_path

    @property
    def instrument(self) -> LMInstrument:
        return self.registry.document_extractors[0].instrument

    @property
    def ready(self) -> bool:
        return self.baselines is not None

    def analyze(self, text: str, settings: Settings | None = None) -> dict:
        """Analyze one essay; returns the API-shaped evidence response dict."""
        baselines = self.baselines
        if baselines is None:
            raise RuntimeError("analysis pipeline has no baseline artifact")

        clean = text.strip()
        if not clean:
            raise ValueError("text must not be empty")

        word_count = len(tokenize(clean))
        if word_count == 0:
            raise ValueError("text contains no words")

        spans = self.registry.splitter.split_spans(clean)
        sentences = tuple(span.text for span in spans)
        if not sentences:
            raise ValueError("text contains no sentences")

        token_count = self.instrument.count_tokens(clean)
        if token_count > self.instrument.max_context_tokens:
            raise LongDocumentError(
                f"text has {token_count} tokens, exceeding the "
                f"{self.instrument.max_context_tokens}-token window of the "
                "language-model instrument; sliding-window scoring is not "
                "implemented yet"
            )

        feature_matrix = self.registry.extract_essay(clean)

        outcome = score_essay(
            feature_matrix,
            sentences,
            baselines,
            word_count=word_count,
            token_count=token_count,
        )

        model_version = "0.1.0"
        if settings is not None:
            model_version = settings.default_model_version

        return {
            "analysis_id": uuid.uuid4().hex,
            "timestamp": datetime.now(UTC).isoformat(),
            "feature_version": feature_matrix.feature_version,
            "model_version": model_version,
            "baselines_version": baselines.schema_version,
            "dataset_version": baselines.dataset_version,
            "essay_word_count": word_count,
            "essay_token_count": token_count,
            "length_bucket": outcome.length_bucket,
            "baseline_bucket": outcome.baseline_bucket,
            "summary": outcome.summary,
            "sentences": [
                {
                    "index": s.index,
                    "text": s.text,
                    "signals": [_signal_dict(sig) for sig in s.signals],
                    "signal_count": s.signal_count,
                    "evidence_strength": s.evidence_strength,
                    "summary": s.summary,
                }
                for s in outcome.sentence_evidence
            ],
            "passages": [
                {
                    "sentence_indices": list(p.sentence_indices),
                    "signals": [_signal_dict(sig) for sig in p.signals],
                    "signal_count": p.signal_count,
                    "evidence_strength": p.evidence_strength,
                    "summary": p.summary,
                }
                for p in outcome.passage_evidence
            ],
            "limitations": list(outcome.limitations),
        }


def _signal_dict(signal) -> dict:
    return {
        "feature": signal.feature,
        "value": signal.value,
        "baseline_mean": signal.baseline_mean,
        "baseline_std": signal.baseline_std,
        "z_score": signal.z_score,
        "direction": signal.direction,
        "evidence": signal.evidence,
        "summary": signal.summary,
    }


def default_pipeline() -> DetectionPipeline | None:
    """Build the shared pipeline used by the app, or None if no baselines."""
    from app.features.registry import FEATURE_REGISTRY_VERSION

    path = find_baselines_path(FEATURE_REGISTRY_VERSION)
    if path is None:
        return None
    instrument = LMInstrument()
    registry = FeatureRegistry(
        document_extractors=(LMSignalExtractor(instrument),)
    )
    return DetectionPipeline(
        registry=registry,
        baselines=load_baselines(path),
        baselines_path=path,
    )

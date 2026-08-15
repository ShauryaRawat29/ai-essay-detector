"""Integration tests for POST /api/v1/analyze (evidence-shaped response).

The pipeline is stubbed with a fake registry so no language model is loaded.
The production dict-building path in DetectionPipeline.analyze is exercised.
"""

from __future__ import annotations

import pytest

from app.evaluation.baselines import BaselineArtifact, BucketStats
from app.features.base import FeatureMatrix
from app.features.splitter import SentenceSplitter
from app.pipeline.orchestration import DetectionPipeline

ESSAY = (
    "Every summer I return to my grandmother's kitchen. "
    "The smell of cinnamon always takes me back. "
    "It is where I learned patience and tradition. "
    + (
        "I watched her fold dough with the same careful rhythm she used for "
        "everything else in her life. "
    )
    * 15
    + "Those quiet hours taught me more than any classroom ever did."
)


class FakeInstrument:
    max_context_tokens = 1024
    device = "cpu"

    def count_tokens(self, text: str) -> int:
        return len(text.split())


class FakeDocumentExtractor:
    name = "fake_lm"
    instrument = FakeInstrument()


class FakeRegistry:
    def __init__(self, matrix: FeatureMatrix) -> None:
        self.splitter = SentenceSplitter()
        self._matrix = matrix
        self.document_extractors = (FakeDocumentExtractor(),)

    def extract_essay(self, text: str) -> FeatureMatrix:
        spans = self.splitter.split_spans(text)
        n = len(spans)
        sentence_features = tuple(
            {"perplexity": 40.0 if i == 0 else 101.0, "token_entropy_mean": 2.5}
            for i in range(n)
        )
        return FeatureMatrix(
            feature_version="f0.3.0",
            sentence_features=sentence_features,
            passage_features=self._matrix.passage_features,
            passage_sentence_indices=tuple(
                (tuple(range(n)),) if self._matrix.passage_sentence_indices else ()
            ),
        )


def _stats(mean: float = 100.0, std: float = 10.0) -> BucketStats:
    return BucketStats(n=50, mean=mean, std=std, p5=80.0, p25=95.0, p50=100.0, p75=105.0, p95=120.0)


def _baselines() -> BaselineArtifact:
    return BaselineArtifact(
        feature_version="f0.3.0",
        dataset_version="v0.1.0",
        n_essays={"short": 5, "standard": 10, "long": 5, "xlong": 0},
        n_sentences={"short": 25, "standard": 80, "long": 30, "xlong": 0},
        buckets={
            "standard": {
                "perplexity": _stats(),
                "token_entropy_mean": _stats(mean=3.0, std=0.2),
            }
        },
    )


def _matrix() -> FeatureMatrix:
    return FeatureMatrix(
        feature_version="f0.3.0",
        sentence_features=(
            {"perplexity": 40.0, "token_entropy_mean": 2.5},
            {"perplexity": 101.0, "token_entropy_mean": 3.0},
            {"perplexity": 60.0, "token_entropy_mean": 2.8},
        ),
        passage_features=(
            {"perplexity": 67.0, "token_entropy_mean": 2.77},
        ),
        passage_sentence_indices=((0, 1, 2),),
    )


@pytest.fixture
def analyze_client(client):
    pipeline = DetectionPipeline(
        registry=FakeRegistry(_matrix()),
        baselines=_baselines(),
    )
    client.app.state.pipeline = pipeline
    return client


def test_analyze_returns_evidence_shaped_response(analyze_client):
    resp = analyze_client.post("/api/v1/analyze", json={"text": ESSAY})
    assert resp.status_code == 200
    data = resp.json()

    assert data["feature_version"] == "f0.3.0"
    assert data["baselines_version"] == "1.0"
    assert data["dataset_version"] == "v0.1.0"
    assert data["length_bucket"] == "standard"
    assert data["summary"]["sentence_count"] == len(data["sentences"])
    assert data["summary"]["sentence_count"] >= 3
    assert data["summary"]["signal_sentences"] >= 1

    sentences = data["sentences"]
    assert len(sentences) >= 3
    for sent in sentences:
        assert sent["index"] >= 0
        assert sent["text"]
        assert sent["evidence_strength"] in {"low", "medium", "high", "uncertain"}
        assert "signals" in sent

    signals = sentences[0]["signals"]
    assert signals
    assert signals[0]["baseline_mean"] == 100.0
    assert signals[0]["z_score"] is not None
    assert signals[0]["evidence"] in {"low", "medium", "high", "uncertain"}

    passages = data["passages"]
    assert len(passages) == 1
    assert passages[0]["sentence_indices"] == list(
        range(data["summary"]["sentence_count"])
    )

    assert data["limitations"]


def test_analyze_never_emits_verdict_fields(analyze_client):
    data = analyze_client.post("/api/v1/analyze", json={"text": ESSAY}).json()
    blob = str(data).lower()
    assert "probability" not in blob
    assert "confidence" not in blob
    assert "is_ai" not in blob
    assert "ai_generated" not in blob


def test_analyze_whitespace_only_rejected(client):
    resp = client.post("/api/v1/analyze", json={"text": "   \n  "})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_analyze_no_words_rejected(client):
    resp = client.post("/api/v1/analyze", json={"text": "!!!"})
    assert resp.status_code == 422
    assert "Traceback" not in resp.text


def test_analyze_missing_text_rejected(client):
    resp = client.post("/api/v1/analyze", json={})
    assert resp.status_code == 422

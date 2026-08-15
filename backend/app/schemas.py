"""Pydantic request/response schemas (per api-contracts skill).

Phase 1 only defines the health contract. The /api/v1/analyze contract will be
added when the detection pipeline exists.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

ModelStatusValue = Literal["not_loaded", "loading", "ready", "error"]


class DeviceInfo(BaseModel):
    cuda_available: bool
    device_count: int
    gpu_name: str | None = None
    cuda_version: str | None = None
    torch_version: str | None = None
    device: str


class ModelStatusSchema(BaseModel):
    key: str
    name: str
    version: str
    kind: str
    revision: str | None = None
    status: ModelStatusValue
    device: str | None = None
    loaded: bool
    loaded_at: float | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    app_version: str
    python_version: str
    environment: str
    feature_version: str | None = None
    device: DeviceInfo
    models: dict[str, ModelStatusSchema]
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )


class ApiError(BaseModel):
    code: Literal["VALIDATION_ERROR", "RATE_LIMITED", "INTERNAL_ERROR", "MODEL_UNAVAILABLE"]
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ApiError


EvidenceValue = Literal["low", "medium", "high", "uncertain"]


class AnalyzeRequest(BaseModel):
    """Essay text to analyze. No user data is persisted."""

    text: str = Field(..., min_length=1, max_length=10000)


class SignalEvidenceSchema(BaseModel):
    feature: str
    value: float
    baseline_mean: float
    baseline_std: float
    z_score: float | None = None
    direction: Literal["lower", "higher", "typical", "unknown"]
    evidence: EvidenceValue
    summary: str


class SentenceEvidenceSchema(BaseModel):
    index: int
    text: str
    signals: list[SignalEvidenceSchema]
    signal_count: int
    evidence_strength: EvidenceValue
    summary: str


class PassageEvidenceSchema(BaseModel):
    sentence_indices: list[int]
    signals: list[SignalEvidenceSchema]
    signal_count: int
    evidence_strength: EvidenceValue
    summary: str


class AnalysisSummary(BaseModel):
    sentence_count: int
    signal_sentences: int
    high: int
    medium: int
    low: int
    uncertain: int


class AnalyzeResponse(BaseModel):
    """Evidence-shaped analysis. Never a probability or authorship verdict."""

    analysis_id: str
    timestamp: datetime
    feature_version: str
    model_version: str
    baselines_version: str
    dataset_version: str | None = None
    essay_word_count: int
    essay_token_count: int
    length_bucket: str
    baseline_bucket: str
    summary: AnalysisSummary
    sentences: list[SentenceEvidenceSchema]
    passages: list[PassageEvidenceSchema]
    limitations: list[str]

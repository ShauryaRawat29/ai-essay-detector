"""API routes (Phase 1: /api/v1/health)."""

from __future__ import annotations

import platform
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import Settings
from app.models.device import detect_device
from app.models.lm_instrument import LongDocumentError
from app.models.loader import ModelRegistry
from app.pipeline.orchestration import DetectionPipeline
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    DeviceInfo,
    HealthResponse,
    ModelStatusSchema,
)


def get_model_registry(request: Request) -> ModelRegistry:
    return request.app.state.model_registry


def get_runtime_settings(request: Request) -> Settings:
    """Return the settings the app was created with (not process env)."""
    return request.app.state.settings


def build_health_response(
    settings: Settings, registry: ModelRegistry
) -> HealthResponse:
    device = detect_device()
    models: dict[str, ModelStatusSchema] = {}
    for key, state in registry.status().items():
        models[key] = ModelStatusSchema(**state)
    return HealthResponse(
        status="ok",
        app_version=settings.app_version,
        python_version=platform.python_version(),
        environment=settings.environment,
        feature_version=settings.feature_version,
        device=DeviceInfo(**device.to_dict()),
        models=models,
        timestamp=datetime.now(UTC),
    )


router = APIRouter(prefix="/api/v1", tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health(
    settings: Settings = Depends(get_runtime_settings),
    registry: ModelRegistry = Depends(get_model_registry),
) -> HealthResponse:
    """Liveness and environment status. Never triggers a model load."""
    return build_health_response(settings, registry)


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={
        422: {"description": "Validation or context-window rejection"},
        503: {"description": "Analysis pipeline unavailable (no baselines)"},
    },
)
def analyze(
    req: AnalyzeRequest,
    request: Request,
    settings: Settings = Depends(get_runtime_settings),
) -> AnalyzeResponse:
    """Analyze an essay and return evidence-shaped, sentence-level results."""
    pipeline: DetectionPipeline | None = getattr(
        request.app.state, "pipeline", None
    )
    if pipeline is None or not pipeline.ready:
        raise HTTPException(
            status_code=503,
            detail="analysis pipeline is not available (baselines missing)",
        )
    registry: ModelRegistry = request.app.state.model_registry
    try:
        result = pipeline.analyze(req.text, settings)
    except (ValueError, LongDocumentError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        registry.mark_error("lm_instrument", "analysis failed")
        raise
    registry.mark_ready("lm_instrument", device=pipeline.instrument.device)
    return AnalyzeResponse(**result)

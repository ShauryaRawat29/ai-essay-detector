"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from app import __version__
from app.api.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.api.middleware import RateLimitMiddleware
from app.api.rate_limit import InMemorySlidingWindowLimiter
from app.api.routes import router
from app.config import Settings, get_settings
from app.models.lm_instrument import lm_instrument_spec
from app.models.loader import ModelRegistry
from app.pipeline.orchestration import default_pipeline


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(
        title="AI Essay Detector API",
        version=__version__,
        description=(
            "Evidence-based AI-writing analysis for admissions essays. "
            "GPT-2 is an instrument for measurable signals only; no "
            "authorship verdicts are produced."
        ),
    )

    registry = ModelRegistry()
    registry.register(lm_instrument_spec())

    limiter = InMemorySlidingWindowLimiter(settings.rate_limit_per_minute)

    app.state.settings = settings
    app.state.model_registry = registry
    app.state.rate_limiter = limiter
    # Loading baselines is cheap and does not load any model. The LM instrument
    # loads lazily on the first /analyze request.
    app.state.pipeline = default_pipeline()

    app.add_middleware(RateLimitMiddleware, limiter=limiter)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.include_router(router)

    return app


app = create_app()

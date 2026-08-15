"""Environment-driven configuration.

Settings are read from the process environment with sensible defaults, and
optionally from a ``.env`` file in the backend directory (loaded via
``python-dotenv``). No secrets are stored here; see ``.env.example``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from app import __version__

BASE_DIR = Path(__file__).resolve().parent.parent

# Load backend/.env if present. Values already in the process environment win.
load_dotenv(BASE_DIR / ".env")

# Pinned revision of the gpt2-medium instrument on the Hugging Face hub
# (verified 2026-08-15). Used to make the LM instrument reproducible (ADR-001).
LM_MODEL_REVISION_DEFAULT = "6dcaa7a952f72f9298047fd5137cd6e4f05f41da"


@dataclass(frozen=True)
class Settings:
    app_name: str = "ai-essay-detector-backend"
    app_version: str = __version__
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    # Feature orchestration is served by /api/v1/analyze; keep the version in
    # sync with the feature registry (FEATURE_REGISTRY_VERSION).
    feature_version: str | None = "f0.3.0"
    default_model_version: str = "0.1.0"
    rate_limit_per_minute: int = 60
    lm_model_name: str = "gpt2-medium"
    lm_model_revision: str = LM_MODEL_REVISION_DEFAULT
    # Passage windowing (ADR-003): overlapping windows of `passage_window`
    # sentences with `passage_stride` stride; windows never cross \n\n
    # paragraph boundaries when `paragraph_fallback` is enabled.
    passage_window: int = 3
    passage_stride: int = 1
    paragraph_fallback: bool = True
    cors_origins: tuple = ("http://localhost:3000", "http://127.0.0.1:3000")

    @classmethod
    def from_env(cls) -> Settings:
        raw_origins = os.getenv("ALLOWED_ORIGINS", "")
        origins: tuple = tuple(
            o.strip()
            for o in raw_origins.split(",")
            if o.strip()
        ) or ("http://localhost:3000", "http://127.0.0.1:3000")
        return cls(
            environment=os.getenv("ENVIRONMENT", "development"),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", "8000")),
            feature_version=os.getenv("FEATURE_VERSION") or None,
            default_model_version=os.getenv("MODEL_VERSION", "0.1.0"),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            lm_model_name=os.getenv("LM_MODEL_NAME", "gpt2-medium"),
            lm_model_revision=os.getenv("LM_MODEL_REVISION", LM_MODEL_REVISION_DEFAULT),
            passage_window=int(os.getenv("PASSAGE_WINDOW", "3")),
            passage_stride=int(os.getenv("PASSAGE_STRIDE", "1")),
            paragraph_fallback=os.getenv("PARAGRAPH_FALLBACK", "true").lower()
            in ("1", "true", "yes", "on"),
            cors_origins=origins,
        )


def get_settings() -> Settings:
    """Dependency-friendly accessor (also used by tests)."""
    return Settings.from_env()

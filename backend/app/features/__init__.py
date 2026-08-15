"""Deterministic feature extraction pipeline (Phase 2).

Public entry point: :func:`app.features.extract_essay` and the
:class:`app.features.FeatureRegistry`. See ``docs/METHODOLOGY.md`` and the
feature catalog in ``registry.py`` for the full feature inventory.
"""

from app.features.base import FeatureMatrix
from app.features.registry import FEATURE_REGISTRY_VERSION, FeatureRegistry, extract_essay

__all__ = [
    "FEATURE_REGISTRY_VERSION",
    "FeatureMatrix",
    "FeatureRegistry",
    "extract_essay",
]

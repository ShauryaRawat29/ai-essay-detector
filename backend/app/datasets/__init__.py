"""Dataset engineering package: schema, preprocessing, dedup, splits, builder,
generation, ingestion."""

from app.datasets.build import build_dataset_version
from app.datasets.builder import DatasetBuilder
from app.datasets.dedup import content_hash, dedupe
from app.datasets.generator import (
    CONFIG_DEFS,
    GenerationQualityError,
    build_prompt,
    config_for,
    generate_ai_record,
)
from app.datasets.ingest import (
    ingest_all_human,
    ingest_ghostbuster_human,
    ingest_leaf,
    ingest_viorra,
)
from app.datasets.preprocess import preprocess
from app.datasets.schema import EssayRecord, GenerationConfig, PreprocessStep
from app.datasets.splits import assign_splits

__all__ = [
    "CONFIG_DEFS",
    "DatasetBuilder",
    "EssayRecord",
    "GenerationConfig",
    "GenerationQualityError",
    "PreprocessStep",
    "assign_splits",
    "build_dataset_version",
    "build_prompt",
    "config_for",
    "content_hash",
    "dedupe",
    "generate_ai_record",
    "ingest_all_human",
    "ingest_ghostbuster_human",
    "ingest_leaf",
    "ingest_viorra",
    "preprocess",
]

"""Dataset metadata schema (per docs/DATASET.md).

A single versioned :class:`EssayRecord` carries the essay text plus label and
provenance. Provenance is mandatory and label-specific: human records require
source/license/collection date; AI-generated records require model, revision,
prompt template + variables, generation config, and date; AI-polished records
require the original essay id and polish prompt. ``split`` may be empty until
the dataset builder assigns a document-level split.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Any

LABELS = ("human", "ai_generated", "ai_polished")
SPLITS = ("train", "val", "test", "test_cross_model", "test_secondary")
UNASSIGNED_SPLIT = ""


class PreprocessStep(StrEnum):
    NFC_NORMALIZE = "nfc_normalize"
    NEWLINE_NORMALIZE = "newline_normalize"
    COLLAPSE_HSPACE = "collapse_hspace"
    STRIP = "strip"


KNOWN_PREPROCESSING_STEPS = frozenset(step.value for step in PreprocessStep)


@dataclass(frozen=True)
class GenerationConfig:
    """Generation configuration recorded verbatim for AI data provenance."""

    temperature: float
    top_p: float
    top_k: int
    max_tokens: int
    seed: int

    def __post_init__(self) -> None:
        if not (0 < self.temperature <= 2.0):
            raise ValueError(f"temperature out of range: {self.temperature}")
        if not (0 < self.top_p <= 1.0):
            raise ValueError(f"top_p out of range: {self.top_p}")
        if self.top_k < 1:
            raise ValueError(f"top_k must be >= 1: {self.top_k}")
        if not (1 <= self.max_tokens <= 2048):
            raise ValueError(f"max_tokens out of range: {self.max_tokens}")


@dataclass(frozen=True)
class EssayRecord:
    """One essay with label, document-level split, and full provenance."""

    essay_id: str
    text: str
    label: str
    split: str
    length_words: int
    topic: str = ""
    preprocessing: tuple[str, ...] = ()
    source: str | None = None
    license: str | None = None
    collection_date: str | None = None
    writer_demographics: dict[str, Any] | None = None
    model: str | None = None
    model_revision: str | None = None
    prompt_template: str | None = None
    prompt_variables: dict[str, Any] | None = None
    generation_config: GenerationConfig | None = None
    generation_date: str | None = None
    original_essay_id: str | None = None
    polish_prompt: str | None = None

    def __post_init__(self) -> None:
        if self.label not in LABELS:
            raise ValueError(f"invalid label: {self.label!r}")
        if self.split and self.split not in SPLITS:
            raise ValueError(f"invalid split: {self.split!r}")
        if not self.essay_id:
            raise ValueError("essay_id is required")
        if not self.text or not self.text.strip():
            raise ValueError("text must be non-empty")
        if self.length_words < 0:
            raise ValueError("length_words must be >= 0")
        unknown_steps = set(self.preprocessing) - KNOWN_PREPROCESSING_STEPS
        if unknown_steps:
            raise ValueError(f"unknown preprocessing steps: {sorted(unknown_steps)}")
        if self.label == "human":
            if not (self.source and self.license and self.collection_date):
                raise ValueError(
                    "human records require source, license, collection_date"
                )
        elif self.label == "ai_generated":
            if not (
                self.model
                and self.model_revision
                and self.prompt_template
                and self.prompt_variables
                and self.generation_config
                and self.generation_date
            ):
                raise ValueError(
                    "ai_generated records require model, model_revision, "
                    "prompt_template, prompt_variables, generation_config, "
                    "generation_date"
                )
        elif self.label == "ai_polished":
            if not (
                self.original_essay_id
                and self.polish_prompt
                and self.model
                and self.generation_config
                and self.generation_date
            ):
                raise ValueError(
                    "ai_polished records require original_essay_id, polish_prompt, "
                    "model, generation_config, generation_date"
                )

    def to_dict(self) -> dict:
        out = {}
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, GenerationConfig):
                value = {
                    "temperature": value.temperature,
                    "top_p": value.top_p,
                    "top_k": value.top_k,
                    "max_tokens": value.max_tokens,
                    "seed": value.seed,
                }
            out[field.name] = value
        return out

    @classmethod
    def from_dict(cls, data: dict) -> EssayRecord:
        data = dict(data)
        if data.get("generation_config") is not None:
            data["generation_config"] = GenerationConfig(**data["generation_config"])
        return cls(**data)

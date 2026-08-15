"""Human baseline computation machinery (ADR-004, Phase 4).

Evidence strength compares measured feature values against human-reference
distributions. Baselines are computed from the TRAINING human split ONLY
(leakage-free by construction), bucketed by essay length, and versioned with
the feature version: ``baselines_f{feature_version}.json``.

Level of measurement (provisional, pending Architect review): baselines are
distributions of SENTENCE-level feature values, grouped by the length bucket of
the essay each sentence came from — this is what supports sentence-level
evidence strength. ``min_n`` is interpreted as the minimum number of SENTENCE
samples per bucket (fallback: merge adjacent buckets).

STATUS: machinery only. No real baselines are computed or claimed until the
human training split exists (dataset v0.1.0).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from app.features.registry import FEATURE_REGISTRY_VERSION

BUCKET_SPECS: tuple[tuple[str, int, int, str], ...] = (
    ("short", 0, 200, "<200 words"),
    ("standard", 200, 500, "200-500 words"),
    ("long", 500, 800, "500-800 words"),
    ("xlong", 800, 0, ">800 words"),  # upper bound is unbounded
)
BUCKET_NAMES: tuple[str, ...] = tuple(spec[0] for spec in BUCKET_SPECS)
DEFAULT_MIN_N = 30
BASELINE_PERCENTILES = (5.0, 25.0, 50.0, 75.0, 95.0)
BASELINE_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class BucketStats:
    n: int
    mean: float
    std: float
    p5: float
    p25: float
    p50: float
    p75: float
    p95: float

    def to_dict(self) -> dict:
        return {
            "n": self.n,
            "mean": self.mean,
            "std": self.std,
            "p5": self.p5,
            "p25": self.p25,
            "p50": self.p50,
            "p75": self.p75,
            "p95": self.p95,
        }

    @classmethod
    def from_dict(cls, data: dict) -> BucketStats:
        return cls(
            n=int(data["n"]),
            mean=float(data["mean"]),
            std=float(data["std"]),
            p5=float(data["p5"]),
            p25=float(data["p25"]),
            p50=float(data["p50"]),
            p75=float(data["p75"]),
            p95=float(data["p95"]),
        )


@dataclass(frozen=True)
class BaselineEssay:
    """One human essay's length and its sentence-level feature vectors."""

    word_count: int
    sentence_features: tuple[dict[str, float], ...]


@dataclass
class BaselineArtifact:
    """Versioned, persisted human baseline distribution (ADR-004)."""

    schema_version: str = BASELINE_SCHEMA_VERSION
    feature_version: str = FEATURE_REGISTRY_VERSION
    dataset_version: str | None = None
    computed_at: str = ""
    n_essays: dict[str, int] = field(default_factory=dict)
    n_sentences: dict[str, int] = field(default_factory=dict)
    # bucket name -> feature name -> BucketStats
    buckets: dict[str, dict[str, BucketStats]] = field(default_factory=dict)
    merge_log: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "feature_version": self.feature_version,
            "dataset_version": self.dataset_version,
            "computed_at": self.computed_at,
            "n_essays": dict(self.n_essays),
            "n_sentences": dict(self.n_sentences),
            "buckets": {
                bname: {feat: stats.to_dict() for feat, stats in feats.items()}
                for bname, feats in self.buckets.items()
            },
            "merge_log": list(self.merge_log),
        }

    @classmethod
    def from_dict(cls, data: dict) -> BaselineArtifact:
        return cls(
            schema_version=str(data["schema_version"]),
            feature_version=str(data["feature_version"]),
            dataset_version=data.get("dataset_version"),
            computed_at=str(data.get("computed_at", "")),
            n_essays={str(k): int(v) for k, v in data.get("n_essays", {}).items()},
            n_sentences={
                str(k): int(v) for k, v in data.get("n_sentences", {}).items()
            },
            buckets={
                str(bname): {
                    str(feat): BucketStats.from_dict(sd) for feat, sd in feats.items()
                }
                for bname, feats in data.get("buckets", {}).items()
            },
            merge_log=[str(m) for m in data.get("merge_log", [])],
        )


def length_bucket(word_count: int) -> str:
    """Assign an essay word count to its ADR-004 length bucket."""
    for name, lo, hi, _ in BUCKET_SPECS:
        if hi == 0:  # unbounded final bucket
            if word_count >= lo:
                return name
        elif lo <= word_count < hi:
            return name
    return BUCKET_NAMES[-1]


def _bucket_min_n(essays_by_bucket: dict[str, list[BaselineEssay]]) -> dict[str, int]:
    return {
        name: sum(len(e.sentence_features) for e in essays)
        for name, essays in essays_by_bucket.items()
    }


def _merge_small_buckets(
    essays_by_bucket: dict[str, list[BaselineEssay]], min_n: int, merge_log: list[str]
) -> list[str]:
    names = [name for name in BUCKET_NAMES if name in essays_by_bucket]
    i = 0
    while i < len(names):
        name = names[i]
        n = _bucket_min_n({name: essays_by_bucket[name]})[name]
        if n >= min_n:
            i += 1
            continue
        if i + 1 < len(names):
            nxt = names[i + 1]
            essays_by_bucket[nxt].extend(essays_by_bucket[name])
            merge_log.append(f"{name}+{nxt} merged (N={n} < min_n={min_n})")
            names.pop(i)
            continue
        if i > 0:
            prev = names[i - 1]
            essays_by_bucket[prev].extend(essays_by_bucket[name])
            merge_log.append(f"{name}+{prev} merged (N={n} < min_n={min_n})")
            names.pop(i)
            i -= 1
            continue
        merge_log.append(f"{name} kept with N={n} < min_n={min_n} (no neighbors)")
        i += 1
    return names


def _bucket_stats(values: list[float]) -> BucketStats:
    arr = np.asarray(values, dtype=float)
    return BucketStats(
        n=int(arr.size),
        mean=float(arr.mean()),
        std=float(arr.std()),
        p5=float(np.percentile(arr, 5.0)),
        p25=float(np.percentile(arr, 25.0)),
        p50=float(np.percentile(arr, 50.0)),
        p75=float(np.percentile(arr, 75.0)),
        p95=float(np.percentile(arr, 95.0)),
    )


def compute_baselines(
    essays: Iterable[BaselineEssay],
    *,
    min_n: int = DEFAULT_MIN_N,
    feature_version: str = FEATURE_REGISTRY_VERSION,
    dataset_version: str | None = None,
    computed_at: str | None = None,
) -> BaselineArtifact:
    """Compute human baseline distributions from sentence features.

    Only the TRAINING human split may be passed here (ADR-004); this function
    does not enforce provenance — the caller owns that guarantee.
    """
    essays = list(essays)
    if not essays:
        raise ValueError("compute_baselines requires at least one essay")

    essays_by_bucket: dict[str, list[BaselineEssay]] = {}
    for essay in essays:
        essays_by_bucket.setdefault(length_bucket(essay.word_count), []).append(essay)

    merge_log: list[str] = []
    surviving = _merge_small_buckets(essays_by_bucket, min_n, merge_log)

    buckets: dict[str, dict[str, BucketStats]] = {}
    n_essays: dict[str, int] = {}
    n_sentences: dict[str, int] = {}
    for name in BUCKET_NAMES:
        n_essays[name] = 0
        n_sentences[name] = 0
    for name in surviving:
        bucket_essays = essays_by_bucket[name]
        n_essays[name] = len(bucket_essays)
        n_sentences[name] = sum(len(e.sentence_features) for e in bucket_essays)
        feature_values: dict[str, list[float]] = {}
        for essay in bucket_essays:
            for vec in essay.sentence_features:
                for key, value in vec.items():
                    feature_values.setdefault(key, []).append(float(value))
        buckets[name] = {key: _bucket_stats(vals) for key, vals in feature_values.items()}

    if computed_at is None:
        computed_at = datetime.now(UTC).isoformat()

    return BaselineArtifact(
        schema_version=BASELINE_SCHEMA_VERSION,
        feature_version=feature_version,
        dataset_version=dataset_version,
        computed_at=computed_at,
        n_essays=n_essays,
        n_sentences=n_sentences,
        buckets=buckets,
        merge_log=merge_log,
    )


def default_filename(feature_version: str) -> str:
    """ADR-004 artifact filename, pinned to the feature version.

    ADR-004 writes ``baselines_f{feature_version}.json``; because
    ``feature_version`` already carries the ``f`` prefix (e.g. ``f0.3.0``),
    the actual name is ``baselines_{feature_version}.json``.
    """
    return f"baselines_{feature_version}.json"


def save_baselines(artifact: BaselineArtifact, path: Path) -> Path:
    path = Path(path)
    path.write_text(
        json.dumps(artifact.to_dict(), indent=2, sort_keys=True), encoding="utf-8"
    )
    return path


def load_baselines(path: Path) -> BaselineArtifact:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return BaselineArtifact.from_dict(data)

"""Real human baseline computation over a built dataset version (ADR-004).

Loads ``records.jsonl`` from a built dataset, keeps ONLY the training human
split (leakage-free by construction), extracts sentence-level feature vectors,
computes length-bucketed baseline distributions, and persists:

- ``baselines_f{feature_version}.json`` — the versioned ADR-004 artifact
- ``report.json`` — honest build provenance (exclusions, skips, counts)

Long builds resume via a feature-versioned per-essay cache: a full forward
pass of the LM instrument over the training split can take tens of minutes, so
per-essay sentence features are cached under ``cache_dir/baselines_fX.Y.Z/``
and reused on re-runs. Cache validity is scoped to the feature version.

Run for real with ``python -m app.evaluation.run_baselines``.
"""

from __future__ import annotations

import json
import math
import random
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from app.config import BASE_DIR
from app.evaluation.baselines import (
    DEFAULT_MIN_N,
    BaselineArtifact,
    BaselineEssay,
    compute_baselines,
    default_filename,
    length_bucket,
    save_baselines,
)
from app.features import extract_essay
from app.features.registry import FEATURE_REGISTRY_VERSION
from app.models.lm_instrument import LongDocumentError

RECORDS_FILENAME = "records.jsonl"
MANIFEST_FILENAME = "manifest.json"
REPORT_FILENAME = "report.json"

# text -> per-sentence feature vectors
Extractor = Callable[[str], Sequence[Mapping[str, float]]]

DEFAULT_DATASET_DIR = BASE_DIR / "data" / "datasets" / "v0.1.0"
DEFAULT_OUTPUT_DIR = BASE_DIR / "data" / "baselines" / "v0.1.0"
DEFAULT_CACHE_DIR = BASE_DIR / "data" / "cache"


def default_extractor(text: str) -> tuple[dict[str, float], ...]:
    """Real sentence-level extraction through the shared feature registry."""
    return tuple(extract_essay(text).sentence_features)


def load_records(dataset_dir: Path) -> list[dict]:
    dataset_dir = Path(dataset_dir)
    records_path = dataset_dir / RECORDS_FILENAME
    if not records_path.exists():
        raise FileNotFoundError(f"records.jsonl not found: {records_path}")
    raw = records_path.read_text(encoding="utf-8")
    # Split on "\n" only: str.splitlines() also splits on other Unicode line
    # separators (e.g. U+2028) that legitimately appear inside essay text, which
    # would corrupt records. json.dumps escapes real newlines, so "\n" is the
    # only record separator in the file.
    return [
        json.loads(line)
        for line in raw.split("\n")
        if line.strip()
    ]


def load_dataset_version(dataset_dir: Path) -> str:
    manifest_path = Path(dataset_dir) / MANIFEST_FILENAME
    if manifest_path.exists():
        return str(json.loads(manifest_path.read_text(encoding="utf-8"))["version"])
    return Path(dataset_dir).name


def sanitize_vector(vec: Mapping[str, float]) -> dict[str, float]:
    """Drop non-finite / non-numeric values from a sentence feature vector."""
    out: dict[str, float] = {}
    for key, value in vec.items():
        try:
            num = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(num):
            out[key] = num
    return out


def sample_baseline_essays(
    records: list[dict],
    *,
    seed: int,
    max_essays: int,
) -> list[dict]:
    """Deterministic stratified subsample of train-human records.

    Strata mirror the split strategy: ``(source, length_bucket)``. Within each
    stratum a seeded shuffle (on essay_id-sorted members) decides selection;
    quotas are proportional to stratum size with a floor of one per non-empty
    stratum, and rounding drift is corrected toward the largest strata. A fixed
    seed makes the sample reproducible; every run with the same inputs returns
    the same essays (cache-friendly).
    """
    if max_essays < 1:
        raise ValueError(f"max_essays must be >= 1, got {max_essays}")
    total = len(records)
    if total <= max_essays:
        return list(records)

    rng = random.Random(seed)
    strata: dict[tuple[str, str], list[dict]] = {}
    for record in records:
        origin = str(record.get("source") or "unknown")
        bucket = length_bucket(int(record["length_words"]))
        strata.setdefault((origin, bucket), []).append(record)

    keys = sorted(strata)
    shuffled: dict[tuple[str, str], list[dict]] = {}
    for key in keys:
        members = sorted(strata[key], key=lambda r: str(r["essay_id"]))
        rng.shuffle(members)
        shuffled[key] = members

    quota = {
        key: max(1, round(len(members) * max_essays / total))
        for key, members in shuffled.items()
    }
    selected = {key: shuffled[key][: quota[key]] for key in keys}

    excess = sum(len(v) for v in selected.values()) - max_essays
    i = 0
    while excess > 0 and i < len(keys):
        key = keys[i]
        if len(selected[key]) > 0:
            selected[key].pop()
            excess -= 1
        i += 1

    shortfall = max_essays - sum(len(v) for v in selected.values())
    i = 0
    while shortfall > 0 and i < len(keys):
        key = keys[i]
        remainder = shuffled[key][quota[key] :]
        if remainder:
            selected[key].append(remainder.pop(0))
            shortfall -= 1
        i += 1

    return [record for key in keys for record in selected[key]]


def compute_dataset_baselines(
    dataset_dir: Path,
    out_dir: Path,
    *,
    min_n: int = DEFAULT_MIN_N,
    extractor: Extractor | None = None,
    cache_dir: Path | None = None,
    feature_version: str = FEATURE_REGISTRY_VERSION,
    dataset_version: str | None = None,
    computed_at: str | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
    max_essays: int | None = None,
    sample_seed: int = 42,
) -> tuple[BaselineArtifact, dict]:
    """Compute real human baselines from a built dataset's TRAINING split.

    The caller of this function is the dataset owner; provenance (train-only,
    human-only) is enforced here. When ``max_essays`` is given, the training
    human set is first reduced by :func:`sample_baseline_essays` (a
    deterministic stratified subsample) so baselines can be computed quickly;
    the full dataset is never modified. Returns ``(artifact, report)`` and
    persists the artifact plus ``report.json`` into ``out_dir``.
    """
    dataset_dir = Path(dataset_dir)
    if not dataset_dir.is_dir():
        raise FileNotFoundError(f"dataset dir not found: {dataset_dir}")

    extract = extractor if extractor is not None else default_extractor
    if dataset_version is None:
        dataset_version = load_dataset_version(dataset_dir)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cache_root: Path | None = None
    if cache_dir is not None:
        cache_root = Path(cache_dir) / f"baselines_{feature_version}"
        cache_root.mkdir(parents=True, exist_ok=True)

    records = load_records(dataset_dir)
    train_human: list[dict] = []
    excluded_non_human = 0
    excluded_non_train = 0
    for record in records:
        if record.get("label") != "human":
            excluded_non_human += 1
        elif record.get("split") != "train":
            excluded_non_train += 1
        else:
            train_human.append(record)

    sample = train_human
    if max_essays is not None:
        sample = sample_baseline_essays(train_human, seed=sample_seed, max_essays=max_essays)
    total_to_process = len(sample)

    essays: list[BaselineEssay] = []
    excluded_long_documents: list[str] = []
    zero_sentences = 0
    done = 0

    for record in sample:
        essay_id = str(record["essay_id"])
        vectors = _load_cached_vectors(cache_root, essay_id)
        if vectors is None:
            try:
                vectors = [
                    sanitize_vector(vec) for vec in extract(str(record["text"]))
                ]
            except LongDocumentError:
                excluded_long_documents.append(essay_id)
                done += 1
                if progress_callback is not None:
                    progress_callback(done, total_to_process)
                continue
            _save_cached_vectors(cache_root, essay_id, vectors)

        vectors = [vec for vec in vectors if vec]
        if not vectors:
            zero_sentences += 1
        else:
            essays.append(
                BaselineEssay(
                    word_count=int(record["length_words"]),
                    sentence_features=tuple(vectors),
                )
            )
        done += 1
        if progress_callback is not None:
            progress_callback(done, total_to_process)

    artifact = compute_baselines(
        essays,
        min_n=min_n,
        feature_version=feature_version,
        dataset_version=dataset_version,
        computed_at=computed_at,
    )

    report = {
        "dataset_version": dataset_version,
        "feature_version": feature_version,
        "min_n": min_n,
        "records_seen": len(records),
        "train_human_total": len(train_human),
        "train_human_used": len(essays),
        "baseline_max_essays": max_essays,
        "baseline_sample_seed": sample_seed,
        "baseline_sample_size": total_to_process,
        "excluded_non_human": excluded_non_human,
        "excluded_non_train": excluded_non_train,
        "excluded_long_documents": len(excluded_long_documents),
        "excluded_long_document_ids": excluded_long_documents,
        "essays_zero_sentences_skipped": zero_sentences,
        "sentences": sum(artifact.n_sentences.values()),
        "bucket_essay_counts": dict(artifact.n_essays),
        "bucket_sentence_counts": dict(artifact.n_sentences),
        "merge_log": list(artifact.merge_log),
    }
    (out_dir / REPORT_FILENAME).write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    save_baselines(artifact, out_dir / default_filename(feature_version))
    return artifact, report


def _load_cached_vectors(cache_root: Path | None, essay_id: str) -> list[dict] | None:
    if cache_root is None:
        return None
    path = cache_root / f"{essay_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _save_cached_vectors(cache_root: Path | None, essay_id: str, vectors: list[dict]) -> None:
    if cache_root is None:
        return
    path = cache_root / f"{essay_id}.json"
    path.write_text(json.dumps(vectors), encoding="utf-8")


def _print_progress(done: int, total: int) -> None:
    if done == total or done % 100 == 0:
        print(f"progress: {done}/{total} train essays", flush=True)


def main() -> None:
    artifact, report = compute_dataset_baselines(
        DEFAULT_DATASET_DIR,
        DEFAULT_OUTPUT_DIR,
        cache_dir=DEFAULT_CACHE_DIR,
        progress_callback=_print_progress,
        max_essays=500,
        sample_seed=42,
    )
    print(f"{default_filename(artifact.feature_version)} written to {DEFAULT_OUTPUT_DIR}")
    print(
        f"train essays used: {report['train_human_used']} "
        f"(sample {report['baseline_sample_size']} of {report['train_human_total']})"
    )
    print(f"sentence samples: {report['sentences']}")
    print(f"long docs excluded: {report['excluded_long_documents']}")
    print(f"merge_log: {report['merge_log']}")


if __name__ == "__main__":
    main()

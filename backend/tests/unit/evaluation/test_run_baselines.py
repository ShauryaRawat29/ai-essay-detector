"""Unit tests for the real-baseline runner (ADR-004 execution).

Synthetic records + fake extractors only: verifies that the runner reads a
built dataset, keeps ONLY the training human split, sanitizes sentence
features, buckets by the record's ``length_words``, persists the versioned
artifact plus an honest report, and can resume via a feature-versioned cache.
"""

import json

import pytest

from app.evaluation.baselines import default_filename, load_baselines
from app.evaluation.run_baselines import compute_dataset_baselines, sample_baseline_essays

FIXED_AT = "2026-08-15T00:00:00Z"


def make_dataset(tmp_path, records, version="v0.1.0"):
    dataset = tmp_path / version
    dataset.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r, ensure_ascii=False) for r in records]
    (dataset / "records.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (dataset / "manifest.json").write_text(
        json.dumps({"version": version}), encoding="utf-8"
    )
    return dataset


def record(essay_id, text, split, label="human", length_words=None, source=None):
    out = {
        "essay_id": essay_id,
        "text": text,
        "label": label,
        "split": split,
        "length_words": length_words if length_words is not None else len(text.split()),
    }
    if source is not None:
        out["source"] = source
    return out


def counting_extractor(calls):
    def extractor(text):
        calls.append(text)
        return ({"perplexity": float(len(text.split()))},)

    return extractor


def test_filters_train_human_only(tmp_path):
    dataset = make_dataset(
        tmp_path,
        [
            record("h-train", "alpha beta gamma", "train", length_words=300),
            record("h-val", "delta", "val"),
            record("h-test", "epsilon", "test"),
            record("ai-train", "zeta", "train", label="ai_generated"),
        ],
    )
    calls = []
    artifact, report = compute_dataset_baselines(
        dataset, tmp_path / "out", extractor=counting_extractor(calls), computed_at=FIXED_AT
    )
    assert calls == ["alpha beta gamma"]
    assert report["records_seen"] == 4
    assert report["train_human_used"] == 1
    assert report["excluded_non_human"] == 1
    assert report["excluded_non_train"] == 2
    assert artifact.n_essays["standard"] == 1


def test_uses_record_length_words_for_bucket(tmp_path):
    dataset = make_dataset(
        tmp_path, [record("a", "x", "train", length_words=600)]
    )
    artifact, _ = compute_dataset_baselines(
        dataset, tmp_path / "out", extractor=counting_extractor([]), computed_at=FIXED_AT
    )
    assert artifact.n_essays["long"] == 1


def test_non_finite_values_dropped(tmp_path):
    def extractor(text):
        return (
            {"good": 1.0, "nan": float("nan"), "inf": float("inf")},
            {"good": 2.0, "nan": float("nan")},
        )

    artifact, _ = compute_dataset_baselines(
        dataset := make_dataset(tmp_path, [record("a", "x", "train", length_words=300)]),
        tmp_path / "out",
        extractor=extractor,
        computed_at=FIXED_AT,
    )
    feats = artifact.buckets["standard"]
    assert "good" in feats
    assert "nan" not in feats
    assert "inf" not in feats
    assert feats["good"].n == 2


def test_zero_sentence_essay_skipped_and_reported(tmp_path):
    def extractor(text):
        if "zero" in text:
            return []
        return ({"perplexity": 1.0},)

    artifact, report = compute_dataset_baselines(
        dataset := make_dataset(
            tmp_path,
            [
                record("a", "zero words", "train", length_words=300),
                record("b", "real words here", "train", length_words=300),
            ],
        ),
        tmp_path / "out",
        extractor=extractor,
        computed_at=FIXED_AT,
    )
    assert report["essays_zero_sentences_skipped"] == 1
    assert artifact.n_essays["standard"] == 1
    assert artifact.n_sentences["standard"] == 1


def test_long_document_excluded_and_reported(tmp_path):
    from app.models.lm_instrument import LongDocumentError

    def extractor(text):
        if "toolong" in text:
            raise LongDocumentError("text has 2000 tokens, exceeding the 1024-token window")
        return ({"perplexity": 1.0},)

    artifact, report = compute_dataset_baselines(
        dataset := make_dataset(
            tmp_path,
            [
                record("a", "toolong essay", "train", length_words=800),
                record("b", "fits fine", "train", length_words=300),
            ],
        ),
        tmp_path / "out",
        extractor=extractor,
        computed_at=FIXED_AT,
    )
    assert report["excluded_long_documents"] == 1
    assert report["excluded_long_document_ids"] == ["a"]
    assert report["train_human_used"] == 1
    assert artifact.n_essays["standard"] == 1


def test_persistence_writes_artifact_and_report(tmp_path):
    dataset = make_dataset(
        tmp_path, [record("a", "alpha beta gamma", "train", length_words=300)]
    )
    artifact, report = compute_dataset_baselines(
        dataset, tmp_path / "out", extractor=counting_extractor([]), computed_at=FIXED_AT
    )
    artifact_path = tmp_path / "out" / default_filename("f0.3.0")
    assert artifact_path.exists()
    assert (tmp_path / "out" / "report.json").exists()
    loaded = load_baselines(artifact_path)
    assert loaded.to_dict() == artifact.to_dict()
    assert artifact.dataset_version == "v0.1.0"
    assert artifact.feature_version == "f0.3.0"
    assert artifact.computed_at == FIXED_AT
    assert report["sentences"] == 1
    assert report["bucket_essay_counts"]["standard"] == 1
    assert report["bucket_sentence_counts"]["standard"] == 1


def test_empty_train_human_raises(tmp_path):
    dataset = make_dataset(tmp_path, [record("a", "x", "test")])
    with pytest.raises(ValueError):
        compute_dataset_baselines(
            dataset, tmp_path / "out", extractor=counting_extractor([])
        )


def test_missing_dataset_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        compute_dataset_baselines(
            tmp_path / "nope", tmp_path / "out", extractor=counting_extractor([])
        )


def test_unicode_line_separators_in_text_do_not_break_records(tmp_path):
    text = "First sentence.\u2028Second with a line separator.\u0085And a NEL."
    dataset = make_dataset(
        tmp_path, [record("a", text, "train", length_words=10)]
    )
    calls = []
    artifact, report = compute_dataset_baselines(
        dataset, tmp_path / "out", extractor=counting_extractor(calls), computed_at=FIXED_AT
    )
    assert calls == [text]
    assert report["train_human_used"] == 1
    assert artifact.n_essays["short"] == 1


def test_cache_reuse_skips_extraction(tmp_path):
    dataset = make_dataset(
        tmp_path,
        [
            record("a", "alpha beta gamma", "train", length_words=300),
            record("b", "one two three four", "train", length_words=600),
        ],
    )
    cache = tmp_path / "cache"
    calls = []
    extractor = counting_extractor(calls)
    compute_dataset_baselines(
        dataset, tmp_path / "out1", extractor=extractor, cache_dir=cache, computed_at=FIXED_AT
    )
    assert len(calls) == 2
    assert (cache / "baselines_f0.3.0" / "a.json").exists()

    calls.clear()
    compute_dataset_baselines(
        dataset, tmp_path / "out2", extractor=extractor, cache_dir=cache, computed_at=FIXED_AT
    )
    assert calls == []
    a1 = load_baselines(tmp_path / "out1" / default_filename("f0.3.0"))
    a2 = load_baselines(tmp_path / "out2" / default_filename("f0.3.0"))
    assert a1.to_dict() == a2.to_dict()


def test_progress_callback_reports_done_total(tmp_path):
    dataset = make_dataset(
        tmp_path,
        [
            record("a", "alpha beta gamma", "train", length_words=300),
            record("b", "one two three four", "train", length_words=600),
            record("c", "skipped val", "val"),
        ],
    )
    events = []
    compute_dataset_baselines(
        dataset,
        tmp_path / "out",
        extractor=counting_extractor([]),
        progress_callback=lambda done, total: events.append((done, total)),
        computed_at=FIXED_AT,
    )
    assert events
    assert events[-1] == (2, 2)


# --- deterministic stratified subsampling ------------------------------------


def test_sample_baseline_essays_respects_max():
    records = [
        {"essay_id": f"e{i:04d}", "length_words": 300, "source": "S1"}
        for i in range(100)
    ]
    out = sample_baseline_essays(records, seed=1, max_essays=10)
    assert len(out) == 10
    assert len({r["essay_id"] for r in out}) == 10


def test_sample_baseline_essays_keeps_rare_strata():
    records = [
        {"essay_id": f"common-{i:03d}", "length_words": 300, "source": "LEAF"}
        for i in range(50)
    ]
    records.append({"essay_id": "rare-001", "length_words": 700, "source": "VIORRA"})
    out = sample_baseline_essays(records, seed=5, max_essays=10)
    assert "rare-001" in {r["essay_id"] for r in out}


def test_sample_baseline_essays_returns_all_when_under_max():
    records = [{"essay_id": f"e{i}", "length_words": 300, "source": "S"} for i in range(5)]
    out = sample_baseline_essays(records, seed=1, max_essays=100)
    assert len(out) == 5


def test_sample_baseline_essays_rejects_bad_max():
    with pytest.raises(ValueError):
        sample_baseline_essays([], seed=1, max_essays=0)


def test_subsample_limits_extraction_and_reports(tmp_path):
    dataset = make_dataset(
        tmp_path,
        [
            record("s1-001", "alpha beta gamma", "train", length_words=300, source="S1"),
            record("s1-002", "delta epsilon zeta", "train", length_words=300, source="S1"),
            record("s1-003", "eta theta iota", "train", length_words=700, source="S1"),
            record("s2-001", "kappa lambda mu", "train", length_words=300, source="S2"),
            record("s2-002", "nu xi omicron", "train", length_words=700, source="S2"),
        ],
    )
    calls = []
    artifact, report = compute_dataset_baselines(
        dataset,
        tmp_path / "out",
        extractor=counting_extractor(calls),
        max_essays=3,
        sample_seed=7,
        computed_at=FIXED_AT,
    )
    assert len(calls) == 3
    assert report["train_human_total"] == 5
    assert report["baseline_sample_size"] == 3
    assert report["baseline_max_essays"] == 3
    assert report["baseline_sample_seed"] == 7


def test_subsample_deterministic_for_same_seed(tmp_path):
    records = [
        record(f"e{i:04d}", "some words here", "train", length_words=300, source="S1")
        for i in range(50)
    ]
    dataset = make_dataset(tmp_path, records)
    a, _ = compute_dataset_baselines(
        dataset,
        tmp_path / "o1",
        extractor=counting_extractor([]),
        max_essays=10,
        sample_seed=3,
        computed_at=FIXED_AT,
    )
    b, _ = compute_dataset_baselines(
        dataset,
        tmp_path / "o2",
        extractor=counting_extractor([]),
        max_essays=10,
        sample_seed=3,
        computed_at=FIXED_AT,
    )
    assert a.to_dict() == b.to_dict()


def test_no_subsample_by_default(tmp_path):
    dataset = make_dataset(
        tmp_path,
        [record(f"e{i}", "some words here", "train", length_words=300) for i in range(5)],
    )
    calls = []
    artifact, report = compute_dataset_baselines(
        dataset, tmp_path / "out", extractor=counting_extractor(calls), computed_at=FIXED_AT
    )
    assert len(calls) == 5
    assert report["baseline_max_essays"] is None
    assert report["baseline_sample_size"] == 5

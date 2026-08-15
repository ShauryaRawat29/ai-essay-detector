"""Unit tests for the batched AI generation runner.

Fake batch functions only (the real model load is a separate concern): verifies
provenance completeness, per-config quotas, essay-id uniqueness, the retry
queue for quality-guard failures, bounded attempts, and honest stats.
"""

import json
from datetime import date

import pytest

from app.config import LM_MODEL_REVISION_DEFAULT
from app.datasets.generate_batch import generate_batch
from app.datasets.generator import CONFIG_DEFS, PROMPT_VARIANTS

GOOD = (
    "This is a fully formed essay about the topic with enough words to "
    "comfortably pass the length quality guard check. "
) * 3
BAD = "too short"


def good_batch(prompts, cfg):
    return [GOOD for _ in prompts]


def bad_batch(prompts, cfg):
    return [BAD for _ in prompts]


def bad_then_good(prompts, cfg):
    if cfg.seed <= 3:
        return [BAD for _ in prompts]
    return [GOOD for _ in prompts]


def test_generate_batch_provenance():
    records, stats = generate_batch(
        "gpt2-medium", LM_MODEL_REVISION_DEFAULT, records_target=8, batch_fn=good_batch
    )
    assert len(records) == 8
    for r in records:
        assert r.label == "ai_generated"
        assert r.split == ""
        assert r.model == "gpt2-medium"
        assert r.model_revision == LM_MODEL_REVISION_DEFAULT
        assert r.generation_date == date.today().isoformat()
        assert "Write a college admissions essay" in r.prompt_template
        assert r.prompt_variables["word_count"] == 600
        assert "topic" in r.prompt_variables
        assert r.generation_config.max_tokens == 800
        assert 0 < r.generation_config.temperature <= 2.0


def test_generate_batch_essay_ids_unique_per_config():
    records, _ = generate_batch(
        "gpt2-medium", LM_MODEL_REVISION_DEFAULT, records_target=8, batch_fn=good_batch
    )
    ids = [r.essay_id for r in records]
    assert len(ids) == len(set(ids))
    assert all(i.startswith("ai-gpt2-") for i in ids)


def test_generate_batch_quota_per_config():
    records, _ = generate_batch(
        "gpt2-medium", LM_MODEL_REVISION_DEFAULT, records_target=8, batch_fn=good_batch
    )
    per = {}
    for r in records:
        key = r.essay_id.split("-")[2]
        per[key] = per.get(key, 0) + 1
    assert per == {"standard": 2, "creative": 2, "focused": 2, "adversarial": 2}


def test_adversarial_uses_human_style_template():
    records, _ = generate_batch(
        "gpt2-medium",
        LM_MODEL_REVISION_DEFAULT,
        records_target=4,
        config_names=["adversarial"],
        batch_fn=good_batch,
    )
    assert all("natural, human style" in r.prompt_template for r in records)


def test_retries_failed_samples_with_next_seed():
    records, stats = generate_batch(
        "gpt2-medium",
        LM_MODEL_REVISION_DEFAULT,
        records_target=4,
        config_names=["standard"],
        batch_fn=bad_then_good,
    )
    assert len(records) == 4
    assert all(r.generation_config.seed > 3 for r in records)
    assert stats["failed_samples"] > 0
    assert stats["configs"]["standard"]["attempts_used"] > 1


def test_gives_up_after_max_attempts_without_infinite_loop():
    records, stats = generate_batch(
        "gpt2-medium",
        LM_MODEL_REVISION_DEFAULT,
        records_target=4,
        config_names=["standard"],
        max_attempts=3,
        batch_fn=bad_batch,
    )
    assert records == []
    assert stats["accepted_total"] == 0
    assert stats["configs"]["standard"]["attempts_used"] == 3


def test_stats_summary_honest():
    records, stats = generate_batch(
        "gpt2-medium",
        LM_MODEL_REVISION_DEFAULT,
        records_target=4,
        config_names=["focused"],
        batch_fn=good_batch,
    )
    assert len(records) == 4
    assert stats["records_target"] == 4
    assert stats["accepted_total"] == 4
    assert stats["configs"]["focused"]["accepted"] == 4


def test_rejects_empty_topics():
    with pytest.raises(ValueError):
        generate_batch(
            "gpt2-medium",
            LM_MODEL_REVISION_DEFAULT,
            records_target=4,
            topics=[],
            batch_fn=good_batch,
        )


def test_configs_are_documented():
    assert set(CONFIG_DEFS) == {"standard", "creative", "focused", "adversarial"}
    assert PROMPT_VARIANTS == ("standard", "adversarial")


def _make_checkpoint(tmp_path, done_configs=None, persisted_records=None):
    ckpt = tmp_path / "ckpt"
    ckpt.mkdir(parents=True, exist_ok=True)
    if done_configs is not None:
        (ckpt / "checkpoint.json").write_text(
            json.dumps({"configs_done": done_configs, "accepted_total": 0}),
            encoding="utf-8",
        )
    if persisted_records:
        lines = [json.dumps(r, ensure_ascii=False) for r in persisted_records]
        (ckpt / "records.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ckpt


def _persisted_record(essay_id):
    return {
        "essay_id": essay_id,
        "text": GOOD,
        "label": "ai_generated",
        "split": "",
        "length_words": 60,
        "topic": "a topic",
        "model": "gpt2-medium",
        "model_revision": LM_MODEL_REVISION_DEFAULT,
        "prompt_template": "Write a college admissions essay on the topic: {topic}",
        "prompt_variables": {"topic": "a topic", "word_count": 600},
        "generation_config": {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 50,
            "max_tokens": 800,
            "seed": 1,
        },
        "generation_date": "2026-08-15",
    }


def test_checkpoint_skips_completed_configs(tmp_path):
    ckpt = _make_checkpoint(
        tmp_path,
        done_configs=["standard", "creative"],
        persisted_records=[
            _persisted_record("ai-gpt2-standard-0001"),
            _persisted_record("ai-gpt2-standard-0002"),
            _persisted_record("ai-gpt2-creative-0001"),
            _persisted_record("ai-gpt2-creative-0002"),
            _persisted_record("ai-gpt2-creative-0003"),
        ],
    )
    calls = []
    records, stats = generate_batch(
        "gpt2-medium",
        LM_MODEL_REVISION_DEFAULT,
        records_target=8,
        config_names=["standard", "creative", "focused"],
        checkpoint_dir=ckpt,
        batch_fn=lambda prompts, cfg: (calls.append(1) or [GOOD for _ in prompts]),
    )
    assert calls  # only the not-yet-done config was generated
    focused = [r for r in records if "focused" in r.essay_id]
    assert all(r.essay_id.startswith("ai-gpt2-focused-") for r in focused)
    assert (ckpt / "checkpoint.json").exists()
    assert (ckpt / "records.jsonl").exists()
    assert len(records) == 8
    ids = [r.essay_id for r in records]
    assert len(ids) == len(set(ids))


def test_checkpoint_resume_adds_only_missing(tmp_path):
    ckpt = _make_checkpoint(tmp_path)
    first, _ = generate_batch(
        "gpt2-medium",
        LM_MODEL_REVISION_DEFAULT,
        records_target=4,
        config_names=["standard"],
        checkpoint_dir=ckpt,
        batch_fn=good_batch,
    )
    assert len(first) == 4
    calls = []
    second, _ = generate_batch(
        "gpt2-medium",
        LM_MODEL_REVISION_DEFAULT,
        records_target=4,
        config_names=["standard"],
        checkpoint_dir=ckpt,
        batch_fn=lambda prompts, cfg: (calls.append(cfg.name) or [GOOD for _ in prompts]),
    )
    assert calls == []
    assert len(second) == 4
    ids = [r.essay_id for r in second]
    assert len(ids) == len(set(ids))

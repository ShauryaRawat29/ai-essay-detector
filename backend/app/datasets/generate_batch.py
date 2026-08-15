"""Batched self-generation of AI admissions essays (gpt2-medium and later).

Wraps :func:`app.datasets.generator.generate_ai_record`'s single-essay path
with a batched runner so the causal LM is loaded ONCE and prompts are generated
in batches (default 8; batch 16 OOMs on this GPU). Provenance stays complete
per record (model, revision, prompt template + variables, config + seed, date).

Reproducibility note (documented, honest): sampling seeds are recorded PER
BATCH (all samples in a call share ``cfg.seed`` — transformers applies one RNG
seed per ``generate`` call). Exact reproduction of a single record therefore
requires re-running the identical batch (same prompts in the same order, same
seed, same batch size, same model revision), which the batch manifest records.

Quality: drafts failing the 50-700-word guard are retried with the next seed;
retries are bounded by ``max_attempts`` and any shortfall is reported honestly
in the returned stats (never fabricated).
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from app.config import BASE_DIR, LM_MODEL_REVISION_DEFAULT
from app.datasets.generator import (
    CONFIG_DEFS,
    PROMPT_VARIANTS,
    build_prompt,
    config_for,
    is_acceptable,
    template_for,
)
from app.datasets.schema import EssayRecord

# text -> per-sample sampling config
BatchFn = Callable[[Sequence[str], Any], list[str]]

DEFAULT_BATCH_SIZE = 8
DEFAULT_MAX_ATTEMPTS = 40
DEFAULT_WORD_COUNT = 600

TOPICS = (
    "a moment that changed how you see yourself",
    "the place you call home",
    "a failure that taught you something",
    "an intellectual curiosity you can't shake",
    "a community you belong to",
    "a challenge you overcame",
    "the book that shaped your thinking",
    "an ordinary habit with extraordinary meaning",
    "a person who influenced you",
    "a time you changed someone's mind",
    "a tradition that matters to you",
    "what you would change about your school",
)

DEFAULT_GENERATED_ROOT = BASE_DIR / "data" / "generated" / "gpt2-medium"


def _load_model(model_name: str, revision: str):
    """Load the causal LM + tokenizer once (lazy torch/transformers import)."""
    import torch  # noqa: F401
    from transformers import AutoModelForCausalLM, AutoTokenizer

    from app.models.device import detect_device

    tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_name, revision=revision, use_safetensors=True
    )
    model.eval()
    model.to(detect_device().device)  # type: ignore[arg-type]
    return model, tokenizer


def _generate_batch_texts(model, tokenizer, prompts: Sequence[str], cfg) -> list[str]:
    """Generate one prompt batch; returns the continuation text per prompt.

    Prompts are encoded individually and padded manually (the fast-tokenizer
    batch encode path has hit transient IndexErrors on this model) — encoding
    per prompt is equivalent and robust. All samples in the batch share
    ``cfg.seed`` (see module docstring for the reproducibility note).
    """
    import torch

    from app.datasets.generator import _make_hf_generation_config

    encoded = [tokenizer(p, return_tensors="pt")["input_ids"][0] for p in prompts]
    prompt_lens = torch.tensor([len(e) for e in encoded], device=model.device)
    max_len = max(len(e) for e in encoded)
    padded = torch.full(
        (len(prompts), max_len), tokenizer.pad_token_id, dtype=torch.long
    ).to(model.device)
    for i, enc in enumerate(encoded):
        padded[i, : len(enc)] = enc

    gc = _make_hf_generation_config(model.config, cfg)
    with torch.no_grad():
        output = model.generate(
            input_ids=padded, attention_mask=padded.ne(tokenizer.pad_token_id),  # type: ignore[arg-type]
            generation_config=gc,
        )
    texts = []
    for i in range(len(prompts)):
        new_tokens = output[i][prompt_lens[i] :]
        texts.append(tokenizer.decode(new_tokens, skip_special_tokens=True).strip())
    return texts


def _generate_for_config(
    cfg_name: str,
    quota: int,
    topics: list[str],
    word_count: int,
    seed: int,
    batch_size: int,
    max_attempts: int,
    model_name: str,
    revision: str,
    fn: BatchFn,
) -> tuple[list[EssayRecord], dict]:
    variant = cfg_name if cfg_name in PROMPT_VARIANTS else "standard"
    template = template_for(variant)
    queue = list(topics)
    records: list[EssayRecord] = []
    idx = 0
    failed = 0
    attempt = 0
    while len(records) < quota and attempt < max_attempts:
        if not queue:
            queue = list(topics)
        batch_topics = queue[:batch_size]
        queue = queue[batch_size:]
        cfg = config_for(cfg_name, seed + attempt)
        prompts = [build_prompt(t, word_count, variant=variant) for t in batch_topics]
        texts = fn(prompts, cfg)
        for topic, text in zip(batch_topics, texts, strict=True):
            if len(records) >= quota:
                break
            if is_acceptable(text):
                records.append(
                    EssayRecord(
                        essay_id=f"ai-gpt2-{cfg_name}-{idx + 1:04d}",
                        text=text,
                        label="ai_generated",
                        split="",
                        length_words=len(text.split()),
                        topic=topic,
                        model=model_name,
                        model_revision=revision,
                        prompt_template=template,
                        prompt_variables={"topic": topic, "word_count": word_count},
                        generation_config=cfg,
                        generation_date=date.today().isoformat(),
                    )
                )
                idx += 1
            else:
                failed += 1
                queue.append(topic)
        attempt += 1
    return records, {
        "quota": quota,
        "accepted": len(records),
        "failed_samples": failed,
        "batches_run": attempt,
        "attempts_used": attempt,
    }


def generate_batch(
    model_name: str = "gpt2-medium",
    revision: str = LM_MODEL_REVISION_DEFAULT,
    *,
    records_target: int = 240,
    config_names: Sequence[str] | None = None,
    topics: Sequence[str] | None = None,
    word_count: int = DEFAULT_WORD_COUNT,
    seed: int = 1,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    batch_fn: BatchFn | None = None,
    progress_callback: Callable[[str, int, int], None] | None = None,
    checkpoint_dir: Path | None = None,
) -> tuple[list[EssayRecord], dict]:
    """Generate ``records_target`` AI essays split across the sampling configs.

    Returns ``(records, stats)``; stats record accepted totals, failed samples,
    per-config detail, and the batch seed — honest provenance for the run.

    When ``checkpoint_dir`` is given, each config's records are appended to
    ``records.jsonl`` ATOMICALLY (only after the whole config quota completes),
    and ``checkpoint.json`` tracks completed configs. A resume re-runs only
    uncompleted configs, so an interrupted/timeout run never loses or
    duplicates finished configs.
    """
    config_list = list(config_names) if config_names is not None else list(CONFIG_DEFS)
    topics_list = list(topics) if topics is not None else list(TOPICS)
    if not config_list:
        raise ValueError("config_names must not be empty")
    if not topics_list:
        raise ValueError("topics must not be empty")

    if batch_fn is None:
        model, tokenizer = _load_model(model_name, revision)

        def fn(prompts, cfg):
            return _generate_batch_texts(model, tokenizer, prompts, cfg)

    else:
        fn = batch_fn

    quota = math.ceil(records_target / len(config_list))
    records: list[EssayRecord] = []
    stats: dict = {
        "records_target": records_target,
        "accepted_total": 0,
        "failed_samples": 0,
        "batches_run": 0,
        "batch_seed": seed,
        "batch_size": batch_size,
        "model": model_name,
        "model_revision": revision,
        "configs": {},
    }

    checkpoint_path: Path | None = None
    records_path: Path | None = None
    if checkpoint_dir is not None:
        checkpoint_dir = Path(checkpoint_dir)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path = checkpoint_dir / CHECKPOINT_FILENAME
        records_path = checkpoint_dir / RECORDS_FILENAME
        done, persisted_total = _load_checkpoint(checkpoint_path)
        records = _load_records_from(records_path)
        stats["accepted_total"] = persisted_total
    else:
        done, persisted_total = set(), 0

    for cfg_name in config_list:
        if cfg_name in done:
            continue
        cfg_records, cfg_stats = _generate_for_config(
            cfg_name,
            quota,
            topics_list,
            word_count,
            seed,
            batch_size,
            max_attempts,
            model_name,
            revision,
            fn,
        )
        records.extend(cfg_records)
        stats["accepted_total"] += len(cfg_records)
        stats["failed_samples"] += cfg_stats["failed_samples"]
        stats["batches_run"] += cfg_stats["batches_run"]
        stats["configs"][cfg_name] = cfg_stats
        if checkpoint_path is not None and records_path is not None:
            done.add(cfg_name)
            _append_records(records_path, cfg_records)
            _save_checkpoint(checkpoint_path, done, stats["accepted_total"])
        if progress_callback is not None:
            progress_callback(cfg_name, len(cfg_records), quota)
    return records, stats


CHECKPOINT_FILENAME = "checkpoint.json"
RECORDS_FILENAME = "records.jsonl"


def _load_checkpoint(path: Path) -> tuple[set[str], int]:
    if not path.exists():
        return set(), 0
    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data.get("configs_done", [])), int(data.get("accepted_total", 0))


def _save_checkpoint(path: Path, done: set[str], accepted_total: int) -> None:
    path.write_text(
        json.dumps(
            {"configs_done": sorted(done), "accepted_total": accepted_total},
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _append_records(path: Path, records: Sequence[EssayRecord]) -> None:
    lines = [json.dumps(r.to_dict(), ensure_ascii=False) for r in records]
    with path.open("a", encoding="utf-8") as fh:
        if path.stat().st_size and lines:
            fh.write("\n")
        fh.write("\n".join(lines))
        if lines:
            fh.write("\n")


def _load_records_from(path: Path) -> list[EssayRecord]:
    if not path.exists():
        return []
    return load_generated_batch(path)


def save_generated_batch(
    records: Sequence[EssayRecord],
    stats: dict,
    out_dir: Path,
) -> Path:
    """Persist the generated records + batch manifest for provenance."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r.to_dict(), ensure_ascii=False) for r in records]
    (out_dir / "records.jsonl").write_text(
        "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8"
    )
    manifest = dict(stats)
    manifest["generated_at"] = datetime.now(UTC).isoformat()
    manifest["total_records"] = len(records)
    (out_dir / "batch_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return out_dir


def load_generated_batch(records_path: Path) -> list[EssayRecord]:
    records_path = Path(records_path)
    out = []
    for line in records_path.read_text(encoding="utf-8").split("\n"):
        if line.strip():
            out.append(EssayRecord.from_dict(json.loads(line)))
    return out


def main() -> None:
    records, stats = generate_batch(
        records_target=160,
        batch_size=4,
        checkpoint_dir=DEFAULT_GENERATED_ROOT,
        progress_callback=lambda cfg, got, quota: print(
            f"config {cfg}: {got}/{quota}", flush=True
        ),
    )
    save_generated_batch(records, stats, DEFAULT_GENERATED_ROOT)
    print(f"generated {stats['accepted_total']} records -> {DEFAULT_GENERATED_ROOT}")
    print(f"failed samples: {stats['failed_samples']}, batches: {stats['batches_run']}")


if __name__ == "__main__":
    main()

"""Self-generated AI essay data (DATASET.md generation provenance rules).

Generates AI-authored admissions essays with a local causal LM so that every
record carries exact provenance (model, revision, prompt template + variables,
generation config including seed, date) per AGENTS.md rule #5. This is a DATA
PRODUCTION tool only — never used at inference time and never a judge.
"""

from __future__ import annotations

from datetime import date

from app.config import LM_MODEL_REVISION_DEFAULT
from app.datasets.schema import EssayRecord, GenerationConfig

MIN_GENERATED_WORDS = 50
MAX_GENERATED_WORDS = 700

ADMISSIONS_PROMPT_V1 = """Write a college admissions essay on the topic: {topic}
Word count: {word_count} words
Style: Personal, reflective, authentic voice
"""

ADVERSARIAL_INSTRUCTION = "\nWrite in a natural, human style."

PROMPT_VARIANTS = ("standard", "adversarial")

CONFIG_DEFS: dict[str, tuple[float, float, int, int]] = {
    "standard": (0.7, 0.9, 50, 800),
    "creative": (0.9, 0.95, 100, 800),
    "focused": (0.3, 0.8, 20, 800),
    "adversarial": (0.7, 0.9, 50, 800),
}


class GenerationQualityError(ValueError):
    """Raised when a generated draft fails quality guards (length bounds)."""


def config_for(name: str, seed: int) -> GenerationConfig:
    """Return the full :class:`GenerationConfig` (params + seed) for a config name."""
    if name not in CONFIG_DEFS:
        raise ValueError(f"unknown generation config: {name!r}")
    temperature, top_p, top_k, max_tokens = CONFIG_DEFS[name]
    return GenerationConfig(
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        max_tokens=max_tokens,
        seed=seed,
    )


def template_for(variant: str = "standard") -> str:
    """Exact prompt template (with placeholders) used for a prompt variant."""
    if variant not in PROMPT_VARIANTS:
        raise ValueError(f"unknown prompt variant: {variant!r}")
    if variant == "adversarial":
        return ADMISSIONS_PROMPT_V1 + ADVERSARIAL_INSTRUCTION
    return ADMISSIONS_PROMPT_V1


def build_prompt(topic: str, word_count: int, variant: str = "standard") -> str:
    """Fill the prompt template with concrete variables."""
    return template_for(variant).format(topic=topic, word_count=word_count)


def is_acceptable(
    text: str,
    min_words: int = MIN_GENERATED_WORDS,
    max_words: int = MAX_GENERATED_WORDS,
) -> bool:
    """Length-quality guard for a generated draft.

    The upper bound keeps drafts scorable by the 1024-token LM instrument
    (prompt + generation must fit in one forward pass). Runs that fail this
    guard are rejected; the batch runner retries with a different seed.
    """
    words = len(text.split())
    return min_words <= words <= max_words


def _make_hf_generation_config(model_config, cfg: GenerationConfig):
    """Map our :class:`GenerationConfig` onto a transformers GenerationConfig.

    ``do_sample`` is required for temperature/seed sampling. The ``seed``
    attribute makes sampling deterministic for a fixed config (provenance rule
    #9 — reproducibility).
    """
    from transformers import GenerationConfig as HFGenerationConfig

    pad_token_id = getattr(model_config, "eos_token_id", None) or getattr(
        model_config, "pad_token_id", None
    )
    gc = HFGenerationConfig.from_model_config(model_config)
    gc.max_new_tokens = cfg.max_tokens
    gc.do_sample = True
    gc.temperature = cfg.temperature
    gc.top_p = cfg.top_p
    gc.top_k = cfg.top_k
    gc.seed = cfg.seed  # type: ignore[attr-defined]  # runtime-supported in transformers 5.x
    gc.pad_token_id = pad_token_id
    return gc


def _generate_text(model_name: str, revision: str, prompt: str, cfg: GenerationConfig) -> str:
    """Generate a draft with the causal LM and return the continuation text.

    Imported lazily so dataset tests (and the app) never require torch/
    transformers at import time. This function is the monkeypatch seam for
    unit tests; the real deterministic-sampling guarantee is exercised in
    ml_pipeline tests against a pinned model revision.
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    from app.models.device import detect_device

    tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, revision=revision, use_safetensors=True
    )
    model.eval()
    model.to(detect_device().device)  # type: ignore[arg-type]

    gc = _make_hf_generation_config(model.config, cfg)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output = model.generate(**inputs, generation_config=gc)  # type: ignore[misc]
    new_tokens = output[0][inputs["input_ids"].shape[1] :]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()  # type: ignore[union-attr]


def generate_ai_record(
    essay_id: str,
    topic: str,
    config_name: str,
    seed: int,
    word_count: int = 600,
    model_name: str = "gpt2-medium",
    revision: str = LM_MODEL_REVISION_DEFAULT,
) -> EssayRecord:
    """Generate one AI-authored essay as a provenance-complete EssayRecord.

    ``config_name`` selects the sampling config; the ``adversarial`` config
    also switches the prompt variant to the "write like human" template.
    """
    cfg = config_for(config_name, seed)
    variant = config_name if config_name in PROMPT_VARIANTS else "standard"
    prompt = build_prompt(topic, word_count, variant=variant)
    text = _generate_text(model_name, revision, prompt, cfg)

    if not is_acceptable(text):
        raise GenerationQualityError(
            f"generated text for {essay_id!r} has {len(text.split())} words, "
            f"outside [{MIN_GENERATED_WORDS}, {MAX_GENERATED_WORDS}]; "
            "retry with a different seed"
        )

    return EssayRecord(
        essay_id=essay_id,
        text=text,
        label="ai_generated",
        split="",
        length_words=len(text.split()),
        topic=topic,
        model=model_name,
        model_revision=revision,
        prompt_template=template_for(variant),
        prompt_variables={"topic": topic, "word_count": word_count},
        generation_config=cfg,
        generation_date=date.today().isoformat(),
    )

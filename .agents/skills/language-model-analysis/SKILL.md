# Skill: language-model-analysis

## Purpose
Using a local causal language model as an INSTRUMENT to extract measurable signals: token log-probabilities, perplexity, entropy, rank distributions, and probability curvature.

## When to Use
- Implementing language model signal extraction
- Choosing/updating the instrument model
- Defining signal computation methods
- Validating signal determinism

## Core Rules
1. **Model is an instrument, not a judge**: The LM provides measurable quantities only
2. **Local model only**: No external API calls for signals
3. **Signals are computable from logits**: perplexity, token entropy, log-prob stats, rank stats, probability curvature
4. **Deterministic inference**: Same model + same input + same config = same signals
5. **Model version pinned**: Record model name, revision, quantization in every experiment
6. **Context window handling**: Document how long essays are handled (truncation, sliding window, chunking)

## Prohibited Behavior
- ❌ Sending essay to LLM with "Is this AI-generated?" prompt
- ❌ Using LLM generated explanations as features
- ❌ Using external APIs (OpenAI, Anthropic) for signals
- ❌ Non-deterministic sampling for signal computation
- ❌ Changing model without version bump and re-evaluation

## Signal Definitions
**Per-sentence signals:**
- `perplexity`: exp(-mean(log_prob)) over sentence tokens
- `token_entropy_mean`: mean of -Σ p log p per token position
- `token_entropy_std`: std of per-position entropy
- `log_prob_mean`: mean token log-probability
- `log_prob_std`: std of token log-probability
- `rank_mean`: mean rank of true token in model distribution
- `rank_std`: std of rank
- `prob_curvature`: measure of probability distribution sharpness

**Passage-level aggregations:**
- Mean, std, min, max, percentiles (25, 50, 75) of each per-sentence signal

## Implementation Requirements
- Use Hugging Face Transformers with `torch.no_grad()`
- Batch sentences for efficiency
- Handle tokenization alignment (model tokenizer ↔ sentence splitter)
- Config: model_id, revision, device, batch_size, max_length, stride
- Output: structured arrays with feature names and versions

## Relevant Project Files
- `backend/app/features/lm_signals.py` - signal extraction
- `backend/app/models/lm_instrument.py` - model loading/wrapper
- `docs/METHODOLOGY.md` - signal definitions and justification
- `docs/EXPERIMENTS.md` - model version tracking
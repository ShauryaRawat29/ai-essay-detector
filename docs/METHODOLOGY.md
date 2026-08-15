# METHODOLOGY.md

## Proposed Detection Methodology

### Overview
Essay → Sentence Split → Feature Extraction (Stylometric + LM Signals) → Classifier → Label Resolution → Evidence Generation

### Feature Families

#### 1. Language Model Signals (Instrument Model: GPT-2 Medium — PROVISIONAL, experimental)
| Feature | Description | Sentence | Passage | Status |
|---------|-------------|----------|---------|--------|
| perplexity | exp(-mean log prob) | ✓ | ✓ (agg) | implemented (f0.3.0) |
| token_entropy_mean | Mean per-position entropy | ✓ | ✓ | implemented (f0.3.0) |
| token_entropy_std | Std of per-position entropy | ✓ | ✓ | implemented (f0.3.0) |
| log_prob_mean | Mean token log-probability | ✓ | ✓ | implemented (f0.3.0) |
| log_prob_std | Std of token log-probability | ✓ | ✓ | implemented (f0.3.0) |
| rank_mean | Mean rank of true token | ✓ | ✓ | implemented (f0.3.0) |
| rank_std | Std of rank | ✓ | ✓ | implemented (f0.3.0) |
| prob_curvature | Distribution sharpness (top-1 prob mean) | ✓ | ✓ | implemented (f0.3.0) |

Scoring: one causal forward pass over the whole essay, so each token is conditioned on all preceding tokens (full context). The first essay token has no prediction and is unscored. Std uses population std (consistent with passage aggregation). Context cap: 1024 tokens (GPT-2 window); longer texts raise `LongDocumentError` — sliding-window context scoring is a documented TODO.

#### 2. Lexical Diversity
| Feature | Description | Sentence | Passage | Status |
|---------|-------------|----------|---------|--------|
| ttr | Type-token ratio | ✓ | ✓ | implemented (f0.2.0) |
| mattr | Moving-average TTR (window=50) | ✗ | ✓ | implemented (f0.2.0) |
| mtld | Mean segmental TTR | ✗ | ✓ | implemented (f0.2.0) |
| hdd | Hypergeometric diversity | ✗ | ✓ | experimental |
| rare_word_rate | Words freq < 1000 in reference corpus | ✓ | ✓ | planned |
| word_length_mean | Mean characters per word | ✓ | ✓ | implemented (f0.2.0) |

#### 3. Syntactic / POS
| Feature | Description | Sentence | Passage | Status |
|---------|-------------|----------|---------|--------|
| pos_dist | Universal POS tag distribution (17 dims) | ✓ | ✓ | implemented (f0.2.0) |
| pos_entropy | Entropy of POS distribution | ✓ | ✓ | implemented (f0.2.0) |
| dep_depth_mean | Mean dependency tree depth | ✓ | ✓ | implemented (f0.2.0) |
| clause_density | Clauses per sentence | ✓ | ✓ | implemented (f0.2.0) |

#### 4. Readability
| Feature | Description | Sentence | Passage | Status |
|---------|-------------|----------|---------|--------|
| flesch_kincaid_grade | Standard formula | ✓ | ✓ | implemented (f0.2.0) |
| flesch_reading_ease | Standard formula | ✓ | ✓ | implemented (f0.2.0) |
| ari | Automated Readability Index | ✓ | ✓ | implemented (f0.2.0) |
| coleman_liau | Coleman-Liau Index | ✓ | ✓ | implemented (f0.2.0) |
| gunning_fog | Gunning Fog Index | ✓ | ✓ | implemented (f0.2.0) |

#### 5. Repetition
| Feature | Description | Sentence | Passage | Status |
|---------|-------------|----------|---------|--------|
| ngram_rep_char_3 | Char 3-gram repetition rate | ✓ | ✓ | implemented (f0.2.0) |
| ngram_rep_word_2 | Word 2-gram repetition rate | ✓ | ✓ | implemented (f0.2.0) |
| self_similarity | Sentence embedding cosine (adjacent) | ✓ | ✓ | experimental |
| lexical_recurrence | Word recurrence rate | ✓ | ✓ | implemented (f0.2.0) |

#### 6. Sentence Rhythm
| Feature | Description | Sentence | Passage | Status |
|---------|-------------|----------|---------|--------|
| sent_len_mean | Mean sentence length (words) | ✓ | ✓ | implemented (f0.2.0) |
| sent_len_std | Std sentence length | ✓ | ✓ | implemented (f0.2.0) |
| sent_len_cv | Coefficient of variation | ✓ | ✓ | implemented (f0.2.0) |
| punct_density | Punctuation chars / total chars | ✓ | ✓ | implemented (f0.2.0) |
| clause_per_sent | Clauses per sentence | ✓ | ✓ | implemented (f0.2.0) as `clause_density` / `clause_density_mean` |

#### 7. Contextual
| Feature | Description | Sentence | Passage | Status |
|---------|-------------|----------|---------|--------|
| coherence_prev | Embedding cosine with previous sentence | ✓ | ✓ | experimental |
| coherence_next | Embedding cosine with next sentence | ✓ | ✓ | experimental |
| topic_consistency | Topic model probability variance | ✗ | ✓ | experimental |

### Label Scheme (per ADR-008)
- **Primary classifier**: Binary — `human` vs `ai_generated`
- **Training labels**: Document-level only; all sentences of a human essay = `human`; all sentences of an AI essay = `ai_generated`
- **Sentence-level supervision**: **Weak supervision (derived from document labels)** — explicitly flagged as such; no independently labeled sentence data exists (recorded as `None`)
- **AI-polished essays**: Label `ai_polished` — secondary evaluation set only (not a training class in MVP)
- **Essay-level result**: Aggregation of evidence counts (sentences with low/medium/high/uncertain strength), NOT a hard verdict

### Classifier Approach
- **Algorithm**: XGBoost (primary), Logistic Regression (mandatory baseline)
- **Input**: Combined feature matrix (standardized)
- **Output**: Per-sentence calibrated probability scores
- **Passage scores**: Aggregated from sentence scores (mean/max of calibrated probabilities)
- **Calibration**: Platt scaling primary; Isotonic regression only if calibration set ≥1000 AND reliability diagram shows non-sigmoid shape (per ADR-005)

### Evidence Generation Pipeline (per ADR-009)
1. **Per-signal scoring**: z-score vs human-training baselines → evidence strength (low/med/high/uncertain)
2. **Classifier prediction**: Calibrated probability per sentence
3. **Feature contribution**: Logistic Regression coefficients OR SHAP values for XGBoost (ranked)
4. **Evidence categories**: perplexity, entropy, lexical_diversity, repetition, rhythm, syntax, readability, contextual
5. **Template descriptions**: Parameterized natural language per category (e.g., "Unusually low perplexity (42.3 vs human baseline 120.5±35.2) suggests predictable token choices")
6. **Uncertainty flags**: Conflicting signal directions, short text (<150 words), OOD feature values
7. **Aggregation**: Sentence → passage (window aggregates) → essay summary (counts per strength; flagged passages)

### Baselines
- Computed from **training human set ONLY** (no validation/test leakage)
- Length-bucketed: <200, 200–500, 500–800, >800 words (min-N=30, fallback merges adjacent buckets)
- Stored as: mean, std, percentiles (5, 25, 50, 75, 95) per feature
- Versioned: `baselines_{feature_version}.json` (ADR-004 writes `baselines_f{feature_version}`; the `f` is already in `feature_version`)
- Updated only with dataset version bump or feature version bump
- **Status**: pipeline machinery implemented (Phase 4) and unit-tested on synthetic data. **No real baselines computed yet** — blocked on the human training split (dataset v0.1.0). Level of measurement (sentence-level feature values, min-N counted in sentences) is provisional pending Architect review.

## Configuration Parameters
- `passage_window`: 3 sentences (configurable 1-10)
- `passage_stride`: 1 sentence
- `paragraph_fallback`: true (respect `\n\n` as hard boundary)
- `lm_model`: gpt2-medium (PROVISIONAL — experimental instrument, per ADR-001)
- `lm_revision`: `6dcaa7a952f72f9298047fd5137cd6e4f05f41da` (HF commit pinned 2026-08-15)
- `lm_max_length`: 1024 (with stride for long essays)
- `lm_batch_size`: 8
- `lm_device`: cpu | cuda
- `classifier_threshold`: Calibrated per class (not a fixed 0.5)
- `evidence_strength_thresholds`: {low: |z|<1, medium: 1≤|z|<2, high: |z|≥2}
- `min_words_for_evidence`: 150 (below → uncertainty flag)

## Pending Validation
- [ ] Signal correlation analysis (multicollinearity)
- [ ] Feature importance stability across CV folds
- [ ] Minimum essay length for reliable signals
- [ ] Cross-model generalization test design
- [ ] EXP-001: GPT-2 Medium vs stronger causal LM on same pipeline
- [ ] EXP-003: Combined feature set vs stylometric-only vs LM-only
- [ ] EXP-004: LogReg vs calibrated XGBoost comparison
- [ ] EXP-005: Platt vs Isotonic calibration comparison
- [ ] EXP-006: Passage aggregation comparison
- [ ] EXP-007: Bias/ESL false-positive audit on all evaluation sets
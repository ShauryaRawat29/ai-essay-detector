# EVALUATION.md

## Evaluation Results

Per `ml-evaluation` skill requirements.

---

## Human Baselines — Real Artifact (dataset v0.1.0, features f0.3.0)

**Status**: Computed 2026-08-15. Artifacts in `backend/data/baselines/v0.1.0/`
(`baselines_f0.3.0.json` + `report.json`). These are the human-reference
distributions used for evidence strength (ADR-004) — NOT a classifier, so no
detection metrics are claimed here.

**Method** (per ADR-004): baselines come from the **training human split only**
(4,230 eligible essays). To bound compute time (the LM feature pass over all
train essays is ~2h), the training set was first reduced by a **deterministic
stratified subsample** (`sample_baseline_essays`, seed 42, strata = source ×
length bucket, proportional quotas, hard cap 500). The full dataset is
unchanged; this composition choice is recorded in the report and as an ADR-004
implementation note. Per-essay sentence features are cached under
`backend/data/cache/` (gitignored) so the full set can be scored later without
rework.

**Sample composition (500)**: LEAF 407, Ghostbuster-human 82, VIORRA sources 11
(JHU 5, Emory 2, Shemmassian 2, CollegeVine 1, IvyCollegeEssay 1);
buckets: standard 428, long 33, short 19, xlong 20.

**Results**: 480 of 500 essays scored (20 excluded — see below), **8,817
sentence samples** across 40 sentence-level features per bucket (stylometric +
syntax + 8 LM signals).

| Length Bucket | Essays | Sentences | Notes |
|---------------|--------|-----------|-------|
| short (<200w) | 19 | 188 | above min_n=30, kept unmerged |
| standard (200–500w) | 428 | 7,624 | dominated by LEAF/IELTS (see limitation) |
| long (500–800w) | 33 | 1,005 | kept unmerged |
| xlong (>800w) | **0** | **0** | **absent** — see limitation |

**Example (standard bucket, perplexity)**: p5=3.4, p25=14.0, p50=24.7,
p75=44.0, p95=149.1, mean=558.2, std=3395.4. Heavy right skew: a few
extreme-perplexity sentences inflate mean/std — evidence strength must use
percentiles (z vs. distribution), never the mean, as the reference point.

**Limitations (baseline-specific)**:
- **xlong (>800 words) bucket is empty.** All 20 sampled xlong essays exceed
  the 1024-token LM context window (`LongDocumentError`); essays >800 words
  cannot be scored with the current instrument. Sliding-window scoring
  (documented TODO in `lm_instrument.py`) is the fix; until then there is no
  human baseline for long admissions essays.
- **Composition skew**: LEAF (IELTS/essayforum, ESL-heavy) is 81% of the
  sample, so the "standard" human reference reflects academic learner writing
  more than polished admissions essays. Bias audits must treat this as a
  coverage limitation, not a representative admissions baseline.
- **Subsample vs full**: baselines use a 500-essay deterministic sample, not
  all 4,230 train essays; distributional stability is assumed but not yet
  verified against the full set.

---

## Current Best Model: [TODO]

**Model Version**: TODO
**Feature Version**: TODO
**Dataset Version**: TODO
**Evaluation Date**: TODO

### Label Scheme (per ADR-008)
- **Primary classes**: `human` | `ai_generated` (binary)
- **Secondary evaluation set**: `ai_polished` (test-only, reported separately)
- **Sentence-level**: Weak supervision derived from document labels (explicitly flagged); no independent sentence labels exist

### Test Set Composition

| Test Set | Description | Size | Source | Label |
|----------|-------------|------|--------|-------|
| test_in_dist | In-distribution (same sources as train) | TODO | Train sources | human / ai_generated |
| test_ood_human | Out-of-distribution human essays | TODO | New human sources | human |
| test_cross_model | AI from unseen model families | TODO | Held-out AI families | ai_generated |
| test_bias_esl | ESL writer essays | TODO | ESL sources | human |
| test_bias_formal | Formal human writing | TODO | Academic/formal sources | human |
| test_bias_edited | Heavily edited essays | TODO | Edited sources | human |
| test_bias_short | Short essays (<200 words) | TODO | Short human + AI | human / ai_generated |
| test_bias_unusual | Unusual topics | TODO | Niche prompts | human / ai_generated |
| test_adversarial | Red Team generated | TODO | Red Team | human / ai_generated |
| test_polished_secondary | AI-polished human essays | TODO | Polished pairs | ai_polished |

### Primary Metrics (Per Test Set)

#### test_in_dist
| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| Human | TODO | TODO | TODO | TODO |
| AI | TODO | TODO | TODO | TODO |
| **Macro Avg** | **TODO** | **TODO** | **TODO** | **TODO** |

**Accuracy**: TODO
**Confusion Matrix**:
```
[[TN, FP],
 [FN, TP]]
```

#### test_ood_human
| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| Human | TODO | TODO | TODO | TODO |
| AI | TODO | TODO | TODO | TODO |
| **Macro Avg** | **TODO** | **TODO** | **TODO** | **TODO** |

#### test_cross_model
| Model Family | Precision | Recall | F1 | Macro F1 |
|--------------|-----------|--------|-----|----------|
| TODO | TODO | TODO | TODO | TODO |

#### test_polished_secondary
| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| Human | TODO | TODO | TODO | TODO |
| AI | TODO | TODO | TODO | TODO |
| **Macro Avg** | **TODO** | **TODO** | **TODO** | **TODO |

*Note: Polished set evaluated separately; primary classifier not trained on polished label. Results reported with uncertainty caveat.*

#### Bias Audit
| Subgroup | FPR | FNR | Macro F1 | vs Overall FPR | Significance |
|----------|-----|-----|----------|----------------|--------------|
| ESL | TODO | TODO | TODO | TODO | TODO |
| Formal | TODO | TODO | TODO | TODO | TODO |
| Edited | TODO | TODO | TODO | TODO | TODO |
| Short (<200) | TODO | TODO | TODO | TODO | TODO |
| Unusual Topic | TODO | TODO | TODO | TODO | TODO |

### Calibration
- **Brier Score**: TODO
- **Reliability Diagram**: [path]
- **ECE (Expected Calibration Error)**: TODO
- **Method**: Platt (primary) / Isotonic (conditional)

### Failure Analysis (3+ Confident Failures)

#### Failure 1
- **Input**: [Excerpt or description]
- **Ground Truth**: Human / AI
- **Prediction**: Human / AI (calibrated score: X.X)
- **Key Features**: [Feature values that drove prediction]
- **Hypothesized Reason**: [Why model failed]
- **Mitigation**: [Potential fix]

#### Failure 2
[Same format]

#### Failure 3
[Same format]

### Limitations Documented
- [ ] Limitation 1: [Description]
- [ ] Limitation 2: [Description]
- [ ] Limitation 3: [Description]

## Historical Evaluations
| Model Version | Date | Macro F1 (in-dist) | Macro F1 (OOD) | Cross-Model Avg | Bias Audit Pass |
|---------------|------|--------------------|----------------|-----------------|-----------------|
| TODO | TODO | TODO | TODO | TODO | TODO |
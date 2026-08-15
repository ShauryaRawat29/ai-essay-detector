# EXPERIMENTS.md

## Experiment Log

Format per `ml-experimentation` skill.

---

## EXP-001: Language Model Instrument Comparison

**Date**: TBD
**Author**: Research / NLP Engineer
**Hypothesis**: A stronger causal LM (e.g., Llama-3-8B) provides measurably better detection signals than GPT-2 Medium on the same downstream pipeline, justifying the instrument upgrade cost.

**Configuration**:
- Models: GPT-2 Medium (`gpt2-medium`) vs Llama-3-8B-Instruct (4-bit quantized) vs DistilGPT-2 (speed baseline)
- Features: LM signals only (perplexity, entropy, log-prob, rank, curvature) + stylometric baseline
- Dataset: Dataset v0.1.0, split v0.1.0_split_42, train/val/test sizes recorded
- Seeds: {numpy: 42, torch: 42, python: 42, sklearn: 42}
- Compute: CPU (GPT-2 Medium, DistilGPT-2); GPU 16GB (Llama-3-8B); time recorded

**Results**: (TBD — to be filled after execution)
- Train: {precision, recall, f1, macro_f1, acc}
- Val: {same}
- Test (in-dist): {same}
- Test (cross-model): {per model family}
- Test (bias): {per subgroup}
- Calibration: {brier, reliability_diagram_path}
- Confusion matrices: [paths]

**Failure Analysis**: 3+ confidently incorrect predictions per model

**Conclusion**: Supported/Refuted, why, next steps

**Artifacts**: [model_path, config_hash, log_path]

**Invalidation Criterion**: If stronger LM does NOT achieve >5% macro-F1 improvement on cross-model test set over GPT-2 Medium, retain GPT-2 Medium as instrument.

---

## EXP-002: Real Human Baselines Computation (v0.1.0 / f0.3.0)

**Date**: 2026-08-15
**Author**: Dataset Engineer / ML Engineer
**Hypothesis**: Computing real human baseline distributions (ADR-004) from the v0.1.0 training human split is feasible within bounded compute via a deterministic stratified subsample, and the resulting reference distributions are usable for evidence strength.

**Configuration**:
- Dataset: v0.1.0 (6,039 records; 4,230 train human eligible)
- Features: f0.3.0 (40 sentence-level features: stylometric + syntax + 8 LM signals, gpt2-medium `6dcaa7a`)
- Baseline sample: `sample_baseline_essays` (seed 42, strata = source × length bucket, proportional quotas, hard cap 500)
- Buckets: ADR-004 (<200 / 200–500 / 500–800 / >800), min_n=30
- Cache: per-essay sentence features under `data/cache/baselines_f0.3.0/`

**Results**:
- 500 sampled → 480 scored, 20 excluded (`LongDocumentError`, >1024 tokens)
- 8,817 sentence samples; merge_log empty (no bucket merges)
- Bucket sentence counts: short 188 / standard 7,624 / long 1,005 / **xlong 0**
- Artifacts: `data/baselines/v0.1.0/baselines_f0.3.0.json`, `data/baselines/v0.1.0/report.json`

**Conclusion**: Supported with documented limitations. The reference distributions
are usable for evidence strength, but the **xlong (>800 words) bucket is empty**
(1024-token LM window excludes all sampled long essays) and the standard bucket is
skewed toward LEAF/IELTS learner writing (81% of sample). Percentiles (not mean/std)
are the stable evidence reference given heavy right skew in LM features (e.g.,
standard-bucket perplexity p50=24.7 vs mean=558.2).

**Follow-up**: sliding-window LM scoring (unblocks xlong); full-set baseline
recomputation reusing the feature cache; verify distributional stability of the
500-essay sample vs full 4,230.

---

## EXP-002: Stylometric Baseline

**Date**: TBD
**Author**: NLP Engineer / ML Engineer
**Hypothesis**: Stylometric features alone (lexical diversity, syntax, readability, repetition, rhythm, contextual) achieve above-chance macro-F1 on in-distribution test set, establishing a non-LM baseline.

**Configuration**:
- Model: Logistic Regression (baseline) + XGBoost
- Features: All stylometric families (NO LM signals)
- Dataset: Dataset v0.1.0, split v0.1.0_split_42
- Seeds: {numpy: 42, torch: 42, python: 42, sklearn: 42}
- Compute: CPU; time recorded

**Results**: (TBD)

**Failure Analysis**: 3+ cases

**Conclusion**: Supported/Refuted

**Artifacts**: [model_path, config_hash, log_path]

**Invalidation Criterion**: If stylometric-only macro-F1 ≤ 0.55 (near chance for binary), LM signals are essential; if >0.65, stylometric has standalone value.

---

## EXP-003: Stylometric + LM Features (Combined)

**Date**: TBD
**Author**: ML Engineer
**Hypothesis**: Combining stylometric features with GPT-2 Medium LM signals improves macro-F1 over either family alone by ≥5% absolute.

**Configuration**:
- Model: XGBoost (primary), Logistic Regression (baseline)
- Features: All stylometric + all LM signals (GPT-2 Medium)
- Dataset: Dataset v0.1.0, split v0.1.0_split_42
- Seeds: {numpy: 42, torch: 42, python: 42, sklearn: 42}
- Compute: CPU; time recorded

**Results**: (TBD)

**Failure Analysis**: 3+ cases

**Conclusion**: Supported/Refuted

**Artifacts**: [model_path, config_hash, log_path]

**Invalidation Criterion**: If combined features do NOT improve macro-F1 by ≥5% over best single family, re-evaluate feature families (ablation in EXP-008+).

---

## EXP-004: Logistic Regression vs Calibrated XGBoost

**Date**: TBD
**Author**: ML Engineer
**Hypothesis**: Calibrated XGBoost achieves ≥3% macro-F1 gain over Logistic Regression on the combined feature set, justifying XGBoost as primary model.

**Configuration**:
- Models: Logistic Regression (Platt calibrated) vs XGBoost (Platt calibrated)
- Features: Combined (stylometric + GPT-2 Medium LM)
- Dataset: Dataset v0.1.0, split v0.1.0_split_42
- Seeds: {numpy: 42, torch: 42, python: 42, sklearn: 42}
- Compute: CPU; time recorded

**Results**: (TBD)

**Failure Analysis**: 3+ cases

**Conclusion**: Supported/Refuted

**Artifacts**: [model_path, config_hash, log_path]

**Invalidation Criterion**: If XGBoost gain <3% macro-F1 → default to Logistic Regression as primary (per ADR-002).

---

## EXP-005: Calibration Comparison (Platt vs Isotonic)

**Date**: TBD
**Author**: ML Engineer / QA Engineer
**Hypothesis**: Platt scaling provides well-calibrated probabilities (Brier score < 0.15, ECE < 0.05) on validation set; Isotonic only improves calibration when N≥1000 and reliability curve is non-sigmoid.

**Configuration**:
- Model: XGBoost (primary) + Logistic Regression
- Calibration methods: Platt vs Isotonic (on held-out validation set)
- Dataset: Dataset v0.1.0, split v0.1.0_split_42
- Seeds: {numpy: 42, torch: 42, python: 42, sklearn: 42}
- Compute: CPU; time recorded

**Results**: (TBD)

**Failure Analysis**: Calibration-specific (reliability diagrams, Brier, ECE per test set)

**Conclusion**: Supported/Refuted

**Artifacts**: [reliability_diagram_paths, calibration_model_paths]

**Invalidation Criterion**: If Isotonic significantly outperforms Platt (ΔBrier > 0.02) AND N_val ≥ 1000 AND non-sigmoid curve, adopt Isotonic for that model; else Platt remains primary (per ADR-005).

---

## EXP-006: Passage Aggregation Comparison

**Date**: TBD
**Author**: NLP Engineer / ML Engineer
**Hypothesis**: Fixed window (k=3, stride=1) with paragraph fallback achieves ≥5% passage-level macro-F1 improvement over paragraph-only and semantic chunking.

**Configuration**:
- Models: XGBoost (calibrated)
- Features: Combined
- Passage strategies: (a) fixed k=3 stride=1, (b) paragraph-only, (c) semantic (SBERT, threshold=0.7)
- Dataset: Dataset v0.1.0, split v0.1.0_split_42
- Seeds: {numpy: 42, torch: 42, python: 42, sklearn: 42}
- Compute: CPU + GPU for semantic embeddings; time recorded

**Results**: (TBD)

**Failure Analysis**: Passage-level false positives/negatives per strategy

**Conclusion**: Supported/Refuted

**Artifacts**: [model_paths, config_hash, log_path]

**Invalidation Criterion**: If semantic chunking >5% passage-F1 gain over fixed window, adopt semantic (per ADR-003).

---

## EXP-007: Bias / ESL False-Positive Audit

**Date**: TBD
**Author**: ML Engineer / Red Team Reviewer
**Hypothesis**: The detector's false positive rate (FPR) on ESL, formal, edited, short, and unusual-topic subgroups does not exceed overall FPR by >10% absolute (i.e., no discriminatory bias).

**Configuration**:
- Model: Best from EXP-003/004 (XGBoost calibrated)
- Features: Combined
- Test sets: 
  - ESL: ≥50 essays from verified ESL writers
  - Formal: ≥50 highly formal human essays
  - Edited: ≥50 professionally edited essays
  - Short: ≥50 essays <200 words
  - Unusual topic: ≥50 essays on niche/technical/creative prompts
  - Cross-model: AI from unseen families
  - Adversarial: Red Team generated
- Dataset: Dataset v0.1.0 + bias audit augmentation
- Seeds: {numpy: 42, torch: 42, python: 42, sklearn: 42}
- Compute: CPU; time recorded

**Results**: (TBD)
- Per-subgroup: FPR, FNR, macro-F1, vs overall FPR (with statistical significance test)
- Calibration: Brier, ECE per subgroup

**Failure Analysis**: 3+ confident failures per subgroup

**Conclusion**: Supported/Refuted

**Artifacts**: [bias_report_path, model_path]

**Invalidation Criterion**: If ANY subgroup FPR exceeds overall FPR by >10% absolute → bias mitigation required before release (per ADR-008/009 and LIMITATIONS.md L-009/L-010).

---

## Experiment Index

| ID | Title | Hypothesis | Status | Best Macro F1 | Date |
|----|-------|------------|--------|---------------|------|
| EXP-001 | LM Instrument Comparison | Stronger LM >5% cross-model gain | Planned | - | TBD |
| EXP-002 | Stylometric Baseline | Stylometric alone > chance | Planned | - | TBD |
| EXP-003 | Stylometric + LM Combined | Combined ≥5% over single family | Planned | - | TBD |
| EXP-004 | LogReg vs Calibrated XGBoost | XGBoost ≥3% gain over LogReg | Planned | - | TBD |
| EXP-005 | Calibration Comparison | Platt sufficient; Isotonic conditional | Planned | - | TBD |
| EXP-006 | Passage Aggregation | Fixed window ≥5% over alternatives | Planned | - | TBD |
| EXP-007 | Bias/ESL False-Positive Audit | No subgroup FPR > overall+10% | Planned | - | TBD |

---

## Future Experiment Pool (EXP-008+)

These are preserved from prior planning and renumbered for future execution:

### Feature Ablation
- [ ] EXP-008: Remove lexical diversity family
- [ ] EXP-009: Remove syntactic features
- [ ] EXP-010: Remove readability
- [ ] EXP-011: Remove repetition
- [ ] EXP-012: Remove rhythm
- [ ] EXP-013: Remove contextual
- [ ] EXP-014: Remove LM signals

### Model Comparison
- [ ] EXP-015: Random Forest
- [ ] EXP-016: MLP (small)
- [ ] EXP-017: SVM (RBF)

### Cross-Model Validation
- [ ] EXP-018: Train on GPT-2, test on Llama-3
- [ ] EXP-019: Train on Llama-3, test on GPT-2
- [ ] EXP-020: Train on both, test on Mistral

### Bias Mitigation
- [ ] EXP-021: Subgroup-specific thresholds
- [ ] EXP-022: Feature reweighting for ESL
- [ ] EXP-023: Additional ESL training data

### Data Ablation
- [ ] EXP-024: Train on 50% data
- [ ] EXP-025: Train without AI-polished data
- [ ] EXP-026: Train without short essays
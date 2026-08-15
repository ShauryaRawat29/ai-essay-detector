# DECISIONS.md

## Architecture Decision Records (ADRs)

Use this format for all architectural decisions.

---

## ADR-001: Local Language Model Instrument Selection

**Date**: 2026-08-15
**Status**: Accepted (Provisional)
**Author**: Architect
**Reviewers**: Research, NLP Engineer, ML Engineer

### Context
The detection pipeline requires a local causal language model to serve as an INSTRUMENT for extracting measurable signals (token log-probabilities, perplexity, entropy, rank distributions, probability curvature). The LM must NOT make the final classification decision (Non-Negotiable Principle #2). We need a model that is: locally runnable on CPU/GPU, deterministic, provides full logits access, has a permissive license, and is well-understood for baseline experiments.

### Options Considered
1. **GPT-2 Medium (355M parameters)**: MIT license, runs on CPU, deterministic with `torch.no_grad()`, full logits access via Hugging Face Transformers, well-studied in detection literature (GPTZero, DetectGPT).
2. **Llama-3-8B-Instruct**: Stronger model, but requires quantization for CPU, larger memory footprint, more complex licensing (Meta Llama 3 Community License), less established as detection instrument.
3. **DistilGPT-2 (82M)**: Faster, smaller, but significantly weaker signal quality; useful for speed comparison only.
4. **External API (GPT-4, Claude)**: Prohibited by Principle #2 (No Opaque LLM Judgement) and security rules.

### Decision
GPT-2 Medium (`gpt2-medium` from Hugging Face) is the CURRENT PROVISIONAL language-model instrument.

**Qualification**: GPT-2 Medium is an EXPERIMENTAL instrument from which we derive measurable signals. It is NOT itself a validated admissions-essay detector. Existing tools (GPTZero, DetectGPT) do NOT prove GPT-2 Medium will work for this project. Perplexity alone is NOT sufficient for detection. Its usefulness must be experimentally evaluated via EXP-001.

### Trade-offs
- **Accepted**: Proven baseline, CPU-runnable, deterministic, MIT license, full logits access.
- **Accepted**: Weaker than modern LLMs; cross-model generalization unproven.
- **Mitigations**: EXP-001 compares GPT-2 Medium vs. at least one stronger causal LM candidate on the SAME documents and SAME downstream feature/classification pipeline.

### Consequences
- **Architecture**: `lm_model: gpt2-medium` in METHODOLOGY.md; ADR-001 recorded.
- **API**: No contract changes.
- **Data**: No schema changes.
- **Testing**: EXP-001 defines the invalidation experiment.

### Related ADRs
- ADR-003: Passage definition (uses LM signals per passage)
- EXP-001: LM instrument comparison experiment

---

## ADR-002: Classifier Algorithm Selection

**Date**: 2026-08-15
**Status**: Accepted
**Author**: Architect
**Reviewers**: ML Engineer, Research

### Context
We need a primary production classifier and a mandatory baseline. The classifier consumes combined stylometric + LM signal features and produces per-sentence scores. Requirements: calibrated probabilities, interpretability, strong baseline performance, compatibility with scikit-learn/XGBoost ecosystem, deterministic inference.

### Options Considered
1. **Logistic Regression (mandatory baseline)**: Linear, highly interpretable, fast, deterministic, coefficients directly usable for feature contribution analysis.
2. **XGBoost (primary production)**: Gradient boosting, typically higher accuracy on tabular features, supports SHAP for contribution analysis, mature calibration integration.
3. **MLP (small neural net)**: More capacity but less interpretable, harder to calibrate, overkill for initial feature set.
4. **Random Forest**: Interpretable feature importance but less calibrated, larger artifacts.
5. **SVM (RBF)**: Strong on small data but poor calibration, no native probability without Platt.

### Decision
**Logistic Regression is the mandatory baseline**. **XGBoost is the primary production model** with post-hoc calibration (per ADR-005). Logistic Regression coefficients provide direct feature contribution evidence; XGBoost uses SHAP for the same purpose.

### Trade-offs
- **Accepted**: Two-model maintenance (baseline + primary).
- **Accepted**: XGBoost adds dependency but is standard in ML stack.
- **Mitigations**: Invalidation criterion — if XGBoost provides <3% macro-F1 gain over Logistic Regression on the same features/data, default to Logistic Regression as primary.

### Consequences
- **Architecture**: Classifier approach updated in METHODOLOGY.md.
- **API**: Response includes `model_version` distinguishing baseline vs primary.
- **Data**: No schema changes.
- **Testing**: EXP-004 compares both with calibrated probabilities.

### Related ADRs
- ADR-005: Calibration method
- EXP-004: Logistic Regression vs calibrated XGBoost

---

## ADR-003: Passage Definition and Aggregation

**Date**: 2026-08-15
**Status**: Accepted
**Author**: Architect
**Reviewers**: NLP Engineer, ML Engineer

### Context
Sentence-level evidence is mandatory (Principle #3), but passages provide more stable aggregate signals and reduce variance. We need a configurable passage definition that works for admissions essays (200–1,500 words, structured paragraphs).

### Options Considered
1. **Fixed overlapping window (k sentences, stride s)**: Deterministic, simple, configurable, sliding context. Default k=3, stride=1 gives 3-sentence context with 1-sentence overlap.
2. **Semantic chunking (embeddings-based boundaries)**: More linguistically natural but non-deterministic, adds embedding dependency, requires threshold tuning.
3. **Paragraph-only (`\n\n` split)**: Natural for essays but variable length; some essays lack clear paragraph breaks.
4. **Hybrid**: Fixed window with paragraph fallback — use fixed k/stride, but respect explicit paragraph boundaries when present.

### Decision
**Configurable overlapping fixed window with paragraph fallback**: default `passage_window=3` sentences, `passage_stride=1`, with paragraph (`\n\n`) boundaries respected as hard breaks. Semantic chunking deferred — requires >5% passage-F1 gain on EXP-006 to adopt.

### Trade-offs
- **Accepted**: Simple, deterministic, configurable, works without paragraph structure.
- **Accepted**: Fixed window may split semantic units; paragraph fallback mitigates.
- **Mitigations**: EXP-006 compares fixed-window vs paragraph vs semantic; gate at >5% macro-F1 improvement.

### Consequences
- **Architecture**: Passage stage in pipeline uses fixed window + paragraph fallback; config in METHODOLOGY.md.
- **API**: Response includes `passages` array with `sentence_indices`.
- **Data**: No schema changes.
- **Testing**: EXP-006 passage aggregation comparison.

### Related ADRs
- ADR-008: Passage-level evidence aggregation

---

## ADR-004: Human Baseline Computation Strategy

**Date**: 2026-08-15
**Status**: Accepted
**Author**: Architect
**Reviewers**: Dataset Engineer, ML Engineer

### Context
Evidence strength (low/medium/high/uncertain) is derived by comparing feature values to human baselines (Principle #4). Baselines must be leakage-free, representative, and versioned.

### Options Considered
1. **Training-human-set baselines**: Compute mean/std/percentiles from the human essays in the training split only. Leakage-free by construction.
2. **External reference corpus (e.g., COCA, student essays)**: Independent but may not match admissions genre; versioning harder.
3. **Combined training + validation human**: Larger sample but introduces validation data into baselines (circular).
4. **Full dataset human**: Maximum sample but leaks test distribution.
### Decision
  **Baselines computed from training human split ONLY**, length-bucketed (<200, 200–500, 500–800, >800 words), 
  with minimum-N=30 per bucket (fallback: merge adjacent buckets). Stored as `baselines_f{feature_version}.json` with 
  mean, std, and percentiles (5, 25, 50, 75, 95) per feature. Updated only when dataset version or feature version bumps.
  
  ### Implementation Note (2026-08-15, real artifact v0.1.0 / f0.3.0)
  Execution may cap the baseline sample with a **deterministic stratified subsample**
  (`sample_baseline_essays`, seed 42, strata = source × length bucket, proportional quotas,
  hard cap default 500) to bound LM compute time. This does not change the architecture
  (still train-human-only, bucketed, versioned); the choice is recorded in `report.json`
  (`baseline_max_essays`, `baseline_sample_seed`, `baseline_sample_size`) and EVALUATION.md.
  Per-essay features are cached under `data/cache/` (gitignored) so a later full-set
  recomputation reuses them.
### Trade-offs
- **Accepted**: Leakage-free, genre-matched, versioned with features.
- **Accepted**: Smaller sample than full dataset; length bucketing reduces N per bucket.
- **Mitigations**: Minimum-N=30 with bucket merging; monitor baseline stability across CV folds.

### Consequences
- **Architecture**: Baseline version pinned to feature version; loaded at pipeline start.
- **API**: Evidence responses reference baseline values per feature.
- **Data**: Baseline artifact stored with feature version.
- **Testing**: Baseline stability checked in ML pipeline tests.

### Related ADRs
- ADR-008: Evidence generation uses these baselines
- ADR-009: Evidence strength thresholds

---

## ADR-005: Calibration Method

**Date**: 2026-08-15
**Status**: Accepted (Provisional)
**Author**: Architect
**Reviewers**: ML Engineer, QA Engineer

### Context
Classifier outputs (Logistic Regression probabilities, XGBoost raw scores) must be calibrated to produce reliable evidence strength categories and calibrated probabilities for downstream use.

### Options Considered
1. **Platt Scaling (sigmoid calibration)**: Parametric, works well for Logistic Regression and XGBoost, low sample requirement (N~100+), stable.
2. **Isotonic Regression**: Non-parametric, more flexible but requires N≥1000 for stability, can overfit on small calibration sets.
3. **Beta Calibration**: More flexible than Platt but less mature in scikit-learn.
4. **Temperature Scaling**: For neural nets; not applicable here.

### Decision
**Platt Scaling is the primary calibration method**. **Isotonic Regression is used ONLY when the calibration set size ≥1000 AND the reliability diagram shows a clearly non-sigmoid shape** (provisional — depends on dataset size). Calibration performed on held-out validation set (not training, not test).

### Trade-offs
- **Accepted**: Platt is stable with modest data; Isotonic available when justified.
- **Accepted**: Provisional status — final choice depends on actual validation set size.
- **Mitigations**: EXP-005 compares both; reliability diagrams recorded in EVALUATION.md.

### Consequences
- **Architecture**: Calibration step in pipeline; `model_version` includes calibration method.
- **API**: Calibrated probabilities in response (rounded to 1 decimal; no false precision).
- **Data**: Calibration set split documented in DATASET.md.
- **Testing**: Calibration tests in ML pipeline (Brier score, ECE).

### Related ADRs
- ADR-002: Classifier choice (both need calibration)
- EXP-005: Calibration comparison

---

## ADR-006: API Rate Limiting Strategy

**Date**: 2026-08-15
**Status**: Accepted (Provisional / Dev-Only)
**Author**: Architect
**Reviewers**: Backend Engineer, Security

### Context
The `/api/v1/analyze` endpoint needs rate limiting to prevent abuse. Production will use Redis-backed distributed limiting; development needs a simple solution.

### Options Considered
1. **In-memory sliding window (fastapi-throttle)**: Simple, zero external deps, works for single-instance dev.
2. **Redis-backed sliding window**: Production-ready, distributed, adds infrastructure.
3. **Token bucket (custom)**: More control but more code.
4. **No rate limiting (dev)**: Risky even in development.

### Decision
**In-memory sliding window via `fastapi-throttle` at 60 requests/minute per IP** for development. Returns 429 with `Retry-After` header and standard rate-limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`). **Redis-backed implementation is required for staging/production**; this ADR is explicitly provisional and dev-only.

### Trade-offs
- **Accepted**: Zero external infrastructure for dev.
- **Accepted**: Not suitable for multi-instance or production; will be replaced.
- **Mitigations**: Configuration-driven; backend AGENTS.md documents env var override.

### Consequences
- **Architecture**: Rate limiter as FastAPI dependency; config in `.env`.
- **API**: Rate-limit headers on all responses.
- **Data**: No schema changes.
- **Testing**: Integration test for 429 behavior.

### Related ADRs
- ADR-007: Frontend state during rate-limited requests

---

## ADR-007: Frontend State Management

**Date**: 2026-08-15
**Status**: Accepted
**Author**: Architect
**Reviewers**: Frontend Engineer, UI/UX Engineer

### Context
The frontend needs client-side state for: essay text, analysis result, loading/error states, selected sentence for detail view. Must be lightweight, TypeScript-friendly, and avoid prop drilling.

### Options Considered
1. **Zustand (~1KB)**: Minimal, React-friendly, TypeScript-first, no Context boilerplate, easy testing.
2. **React Context API**: Built-in, but requires providers, re-renders on any change unless split, verbose for global state.
3. **Redux Toolkit**: Powerful but overkill for this state surface (~10KB+).
4. **Recoil**: Atoms/selectors but larger bundle, less maintained.

### Decision
**Zustand for all client state**; React Context ONLY for static globals (theme, feature flags). Store structure: `essayText`, `result` (AnalysisResult), `status` ('idle' | 'analyzing' | 'complete' | 'error'), `selectedSentenceIndex`, actions. Persist only `theme` to localStorage.

### Trade-offs
- **Accepted**: Tiny bundle, excellent TS support, simple mental model.
- **Accepted**: Less ecosystem tooling than Redux; acceptable for app scope.
- **Mitigations**: If state complexity grows, migration path to Redux Toolkit exists.

### Consequences
- **Architecture**: `useAnalysis` hook wraps Zustand store; components subscribe to slices.
- **API**: No contract changes.
- **Data**: No schema changes.
- **Testing**: Unit tests for store actions; component tests with mocked store.

### Related ADRs
- Frontend AGENTS.md component contracts align with this store.

---

## ADR-008: Detection Label Definition

**Date**: 2026-08-15
**Status**: Accepted
**Author**: Architect
**Reviewers**: Research, Dataset Engineer, ML Engineer, Red Team Reviewer

### Context
The system must distinguish conceptually between at least: (A) HUMAN — writing produced without known generative-AI assistance; (B) AI-GENERATED — writing substantially generated by a generative language model; (C) AI-POLISHED / HUMAN-AUTHORED + AI-ASSISTED — writing originally produced by a human but subsequently modified, rewritten, or polished using an AI system. The architecture must explicitly decide: what labels are used for training, what labels for evaluation, whether AI-polished is a separate class/secondary set/both, whether the primary classifier is binary or multiclass, how sentence-level labels relate to document-level labels, how essay-level results aggregate from sentence/passage scores, and what "AI-like evidence" means when authorship cannot be proven.

### Options Considered
1. **Binary primary (HUMAN / AI-GENERATED), AI-polished as secondary evaluation set**: Clean binary training; polished essays held out for evaluation only with explicit uncertainty expectation.
2. **3-way multiclass (HUMAN / AI-GENERATED / AI-POLISHED)**: Treats all three as first-class training classes.
3. **Binary with AI-polished merged into AI-GENERATED**: Simplest but conflates distinct phenomena; loses ability to study polished behavior.
4. **Abstention/rejection class for uncertain cases**: Adds complexity; defers the core label decision.

### Decision
**Binary primary classifier (HUMAN vs AI-GENERATED) trained on clean human + fully AI-generated essays. AI-polished essays form a secondary evaluation set (test-only), reported separately, with high uncertainty expectation.** Not a training class in MVP.

**Label semantics**:
- Document labels (HUMAN / AI-GENERATED) are authoritative **only at document level**.
- Sentence/passage scores are **evidence signals**, never ground-truth authorship labels.
- Any sentence/passage supervision derived from document labels must be explicitly labeled **"weak supervision (derived from document labels)"** — to be used only if the architecture later needs it, and only flagged as such unless independently labeled sentence/passage data exists (currently none; recorded as `None`).
- Essay-level result = aggregation of evidence counts (sentences with low/medium/high/uncertain strength), NOT a hard verdict.
- "AI-like evidence" means: patterns statistically associated with known generative model outputs in our training data; explicitly NOT proof of authorship.

### Trade-offs
- **Accepted**: Clean binary performance preserved; polished behavior measured honestly on held-out set.
- **Accepted**: AI-polished detection capability unproven at MVP; explicitly documented as limitation.
- **Mitigations**: Invalidation experiment — if polished-set separation is near chance AND/OR bias audit (ESL/formal/short) fails at MVP gate, reconsider multiclass or abstention policy for hybrids.

### Consequences
- **Architecture**: Label scheme documented in METHODOLOGY.md, DATASET.md, EVALUATION.md.
- **API**: Response includes `labels_used: ["human", "ai_generated"]` and `evaluation_sets: ["in_dist", "cross_model", "polished_secondary"]`.
- **Data**: AI-polished essays stored with `label: "ai_polished"` and `split: "test_secondary"` (or `test` if used in primary test); original human essay and its polished derivative are a **leak group** — both must go to the SAME split (or polished held to test).
- **Testing**: EXP-007 includes polished-set evaluation; bias audit on all sets.

### Related ADRs
- ADR-004: Baselines (human only)
- ADR-009: Evidence generation (uses label scheme)
- EXP-007: Bias/ESL audit includes polished secondary set

---

## ADR-009: Evidence Generation Pipeline

**Date**: 2026-08-15
**Status**: Accepted
**Author**: Architect
**Reviewers**: NLP Engineer, ML Engineer, UI/UX Engineer, Explainable AI skill

### Context
The system must convert predictions into human-readable evidence WITHOUT: (a) asking an LLM "Why is this sentence AI?" (forbidden), (b) inventing explanations not backed by measured features, (c) displaying false precision (e.g., "92.3817% AI"). Every evidence claim must trace to measurable feature values and model contributions.

### Options Considered
1. **LLM-generated explanations**: Prohibited by Principle #2 and explainable-ai skill.
2. **Template-based evidence from measured features + model contributions**: Deterministic, traceable, auditable.
3. **Raw feature dump only**: Not human-readable enough for admissions officers.
4. **SHAP/LIME explanations only**: Powerful but can produce unstable natural language; requires templating layer anyway.

### Decision
**Template-based evidence generator**. Pipeline:
```
Raw sentence
  ↓
Feature extraction (stylometric + LM signals)
  ↓
Feature values (per sentence + passage aggregates)
  ↓
Per-signal scoring: z-score vs human-training baselines → evidence strength {low | medium | high | uncertain}
  ↓
Classifier prediction (calibrated probability)
  ↓
Feature contribution analysis: Logistic Regression coefficients OR SHAP values for XGBoost (ranked)
  ↓
Evidence categories: {perplexity, entropy, lexical_diversity, repetition, rhythm, syntax, readability, contextual}
  ↓
Template-based natural language descriptions (one template per evidence category, parameterized by values/baselines)
  ↓
Uncertainty flags: conflicting signals, short text (<150 words), OOD feature values
  ↓
Human-readable evidence output
```

**Evidence schema (per sentence)**:
```json
{
  "index": 0,
  "text": "Sentence text...",
  "signals": {
    "perplexity": {"value": 42.3, "baseline_mean": 120.5, "baseline_std": 35.2, "z_score": -2.22, "evidence_strength": "high", "direction": "lower_than_human"},
    "token_entropy_mean": {"value": 2.1, "baseline_mean": 3.8, "baseline_std": 0.9, "z_score": -1.89, "evidence_strength": "medium", "direction": "lower_than_human"}
  },
  "contributions": [
    {"feature": "perplexity", "contribution": 0.42, "direction": "toward_ai"},
    {"feature": "token_entropy_mean", "contribution": 0.18, "direction": "toward_ai"}
  ],
  "evidence_strength": "high",
  "evidence_summary": "Unusually low perplexity and low token entropy suggest predictable, low-surprise word choices.",
  "uncertainty_flags": []
}
```

**Feature registry statuses**: every feature tagged `implemented | planned | experimental | rejected` (all `planned/experimental` until built).

**Evidence strength thresholds**: `low: |z| < 1`, `medium: 1 ≤ |z| < 2`, `high: |z| ≥ 2`, `uncertain: conflicting directions or short text (<150 words) or OOD`.

**UI MUST NOT display**:
- "X% AI" or any probability-as-authorship (calibrated probability shown only if calibration validated, rounded to 1 decimal, labeled "calibrated score — not authorship probability")
- Binary "AI-Generated: Yes/No" or "Human: Yes/No" labels
- Red/Green color coding for AI/Human
- "Confidence" language without calibration backing
- Invented explanations for features not in the pipeline
- Single overall score without sentence-level breakdown

### Trade-offs
- **Accepted**: Template approach requires maintaining templates per feature category; but ensures traceability.
- **Accepted**: SHAP for XGBoost adds compute; fallback to mean |SHAP| per feature is acceptable.
- **Mitigations**: Explanation fidelity audit (feature removal changes evidence predictably) in testing.

### Consequences
- **Architecture**: Evidence generation as explicit pipeline stage; `feature_version` and `model_version` in every response.
- **API**: Response schema includes `sentences[]`, `passages[]`, `limitations[]`, `feature_version`, `model_version`.
- **Data**: No schema changes.
- **Testing**: Unit tests for evidence templates with golden outputs; explanation fidelity test.

### Related ADRs
- ADR-001: LM signals feed evidence
- ADR-004: Baselines for z-scores
- ADR-008: Label scheme informs evidence language
- Frontend AGENTS.md: Evidence UI contracts

---

## ADR Template (Copy for New Decisions)

```markdown
## ADR-XXX: [Title]

**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Rejected | Deferred | Superseded
**Author**: [Agent]
**Reviewers**: [List]

### Context
[What problem are we solving? What constraints exist?]

### Options Considered
1. **Option A**: [Description, pros, cons]
2. **Option B**: [Description, pros, cons]
3. **Option C**: [Description, pros, cons]

### Decision
[Chosen option and rationale]

### Trade-offs
- **Accepted**: [What we gain]
- **Accepted**: [What we lose/accept]
- **Mitigations**: [How we address downsides]

### Consequences
- **Architecture**: [Changes to docs/ARCHITECTURE.md]
- **API**: [Contract changes]
- **Data**: [Schema/migration changes]
- **Testing**: [New test requirements]

### Related ADRs
- ADR-XXX: [Related decision]
```
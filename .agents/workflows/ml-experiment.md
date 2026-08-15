# Workflow: ML Experiment

## Trigger
- New hypothesis from Research
- Feature ablation needed
- Model comparison required
- Hyperparameter search
- Bias mitigation test

## Process

### Quality Gate Chain (mandatory, no skips)
Quality Skill → Implementation → Tests → Static checks → Review → Documentation

### 0. Mandatory Skills
- Load `software-engineering-quality` and `test-driven-development`
- All experiment/analysis code must satisfy the quality gate and be test-first

### 1. Define Hypothesis
- Write in `docs/EXPERIMENTS.md` using template
- One sentence, testable, falsifiable
- Link to research question or architectural need

### 2. Baseline First
- Always run baseline before variants
- Baseline: simplest reasonable config
- Record baseline metrics fully

### 3. Configure Experiment
- Model: algorithm, hyperparameters
- Features: feature version, list of families
- Dataset: dataset version, split version
- Seeds: numpy, torch, python, sklearn
- Compute: hardware, estimated time

### 4. Run Experiment
- Execute training with full logging
- Validate on validation set
- Test on ALL test sets (in-distribution, OOD, cross-model, bias)
- Capture: metrics, logs, artifacts, confusion matrices, calibration curves

### 5. Record Results
- Complete `docs/EXPERIMENTS.md` entry
- Include negative/failed results
- Link to model artifacts

### 6. Analyze & Conclude
- Hypothesis supported/refuted?
- Why? (feature importance, error analysis)
- Next steps (new hypothesis, production candidate, discard)

### 7. Production Candidate Gate
If results warrant production:
- Run full Evaluation workflow
- Red Team Review workflow
- Architecture Review for serving changes

## Experiment Template (in `docs/EXPERIMENTS.md`)
```markdown
## EXP-XXX: [Title]

**Date**: YYYY-MM-DD
**Author**: [Agent]
**Hypothesis**: [One sentence]

**Configuration**:
- Model: [algorithm, hyperparams dict]
- Features: [feature_version, families]
- Dataset: [dataset_version, split_version, sizes]
- Seeds: {numpy: X, torch: Y, python: Z, sklearn: W}
- Compute: [GPU/CPU, time]

**Results**:
- Train: {precision, recall, f1, macro_f1, acc}
- Val: {same}
- Test (in-dist): {same}
- Test (OOD): {same}
- Test (cross-model): {per model family}
- Test (bias): {per subgroup}
- Calibration: {brier, reliability_diagram_path}
- Confusion matrices: [paths]

**Failure Analysis**: [3+ cases or N/A]

**Conclusion**: [Supported/Refuted, why, next steps]

**Artifacts**: [model_path, config_hash, log_path]
```

## Agents Involved
- **ML Engineer** (lead): Executes workflow
- **Dataset Engineer**: Provides validated splits
- **NLP Engineer**: Provides feature matrices
- **Architect**: Reviews for production gating
- **Red Team Reviewer**: Receives models for testing

## Gates
- **No experiment without written hypothesis**
- **No experiment code without passing the quality gate: TDD, lint, type check, reproducibility checks**
- **No results without full test suite evaluation**
- **No production without Red Team Review**
- **All results recorded** (including failures)

## Prohibited
- ❌ Running experiments without hypothesis
- ❌ Changing config mid-run without new entry
- ❌ Evaluating only on best test set
- ❌ Skipping bias audit
- ❌ Fabricating or cherry-picking results
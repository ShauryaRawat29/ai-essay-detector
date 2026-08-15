# Skill: ml-experimentation

## Purpose
Structured ML experimentation: hypothesis-driven experiments, configuration tracking, reproducibility, and result recording.

## When to Use
- Running any ML experiment (feature ablation, model comparison, hyperparameter search)
- Recording experiment results
- Comparing experimental variants
- Ensuring reproducibility

## Core Rules
1. **Hypothesis first**: Every experiment has a written hypothesis before running
2. **Configuration fully recorded**: Model, features, data, hyperparameters, seeds
3. **Dataset version pinned**: Exact dataset version and split used
4. **Feature version pinned**: Exact feature extractor versions
5. **Model version output**: Trained model artifact versioned
6. **Results recorded in `docs/EXPERIMENTS.md`**: No exceptions

## Prohibited Behavior
- ❌ Running experiments without written hypothesis
- ❌ Changing config mid-experiment without new entry
- ❌ Using unversioned data/features/models
- ❌ Not recording failed/negative results
- ❌ Cherry-picking results for documentation

## Experiment Record Format (`docs/EXPERIMENTS.md`)
```markdown
## Experiment EXP-XXX: [Short Title]

**Date**: YYYY-MM-DD
**Author**: [Agent]
**Hypothesis**: [One sentence, testable]
**Configuration**:
  - Model: [algorithm, hyperparameters]
  - Features: [feature version, list of feature families]
  - Dataset: [dataset version, split version, train/val/test sizes]
  - Random seed: [integer]
  - Compute: [hardware, time]
**Result**:
  - Train metrics: [precision, recall, F1, etc.]
  - Val metrics: [same]
  - Test metrics: [same, on all test sets]
  - Calibration: [Brier, reliability]
  - Cross-model: [metrics on unseen models]
  - Bias audit: [subgroup metrics]
**Conclusion**: [Supported/refuted, why, next steps]
**Artifacts**: [model path, config hash, log path]
```

## Experiment Types
1. **Baseline establishment**: First model of a type
2. **Feature ablation**: Add/remove feature families
3. **Model comparison**: Different algorithms
4. **Hyperparameter search**: Systematic or random
5. **Data ablation**: Subset of training data
6. **Cross-model validation**: Train on Model A, test on Model B
7. **Bias intervention**: Mitigation technique test

## Reproducibility Checklist
- [ ] Random seeds set (numpy, torch, python, sklearn)
- [ ] Dataset version and split hash recorded
- [ ] Feature extractor versions recorded
- [ ] Model config fully serialized
- [ ] Environment (Python, package versions) recorded or containerized
- [ ] Artifacts saved with versioned names
- [ ] Results recorded in `docs/EXPERIMENTS.md`

## Relevant Project Files
- `backend/app/experiments/` - experiment scripts
- `docs/EXPERIMENTS.md` - experiment log
- `docs/EVALUATION.md` - evaluation results referenced by experiment
- `backend/requirements.txt` / `pyproject.toml` - environment
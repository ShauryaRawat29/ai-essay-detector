# Skill: ml-evaluation

## Purpose
Rigorous model evaluation: precision, recall, F1, confusion matrix, calibration, cross-model evaluation, failure analysis, and bias auditing.

## When to Use
- Evaluating trained models
- Comparing model variants
- Running bias audits
- Documenting evaluation results
- Preparing evaluation reports

## Core Rules
1. **Primary metrics**: Precision, Recall, F1 per class; macro-averaged
2. **Confusion matrix required**: For every evaluation
3. **Calibration reported**: Reliability diagrams, Brier score
4. **Cross-model evaluation**: Test on model families not in training
5. **Failure analysis**: 3+ confidently incorrect predictions with analysis
6. **Bias audit mandatory**: Explicit test sets for ESL, formal, edited, short, unusual topics
7. **No cherry-picking**: Report all test sets, not just best-performing

## Prohibited Behavior
- ❌ Reporting only accuracy
- ❌ Evaluating only on training-distribution test sets
- ❌ Skipping calibration
- ❌ Skipping cross-model evaluation
- ❌ Skipping bias audit
- ❌ Hiding poor-performing test sets
- ❌ Fabricating metrics

## Required Evaluation Protocol

### Test Set Composition (documented in `docs/EVALUATION.md`)
- In-distribution test set (same sources as training)
- Out-of-distribution: different human sources
- Cross-model: AI from models not in training
- Bias audit sets: ESL, formal, edited, short, unusual topics
- Adversarial: Red Team generated cases

### Metrics Per Test Set
| Metric | Required |
|--------|----------|
| Precision (per class) | Yes |
| Recall (per class) | Yes |
| F1 (per class) | Yes |
| Macro F1 | Yes |
| Accuracy | Yes |
| Confusion Matrix | Yes |
| Brier Score | Yes |
| Reliability Diagram | Yes |
| AUC-ROC | If probabilistic |

### Failure Analysis (3+ cases)
For each confidently incorrect prediction:
- Input essay (or excerpt)
- Ground truth
- Prediction with scores
- Feature values that drove prediction
- Hypothesized reason for error
- Mitigation idea

### Bias Audit Report
For each bias dimension:
- Test set description and size
- False positive rate
- False negative rate
- Comparison to overall rates
- Statistical significance test

## Output Format
All results recorded in `docs/EVALUATION.md` with:
- Model version
- Feature version
- Dataset version and split
- Test set descriptions
- All metrics above
- Failure analyses
- Bias audit results
- Conclusions and limitations

## Relevant Project Files
- `backend/app/evaluation/` - evaluation scripts
- `docs/EVALUATION.md` - evaluation records
- `docs/EXPERIMENTS.md` - experiment references
- `docs/FAILURE-CASES.md` - failure analyses
- `docs/LIMITATIONS.md` - documented limitations
# Skill: bias-analysis

## Purpose
Systematic investigation of detector bias: false positive rates across demographic and stylistic groups, fairness metrics, and mitigation strategies.

## When to Use
- Designing bias audit test sets
- Running bias evaluations
- Analyzing bias results
- Documenting bias findings and limitations
- Proposing mitigations

## Core Rules
1. **Explicit test sets required**: ESL, formal, edited, short, unusual topics — each documented
2. **False positive focus**: Primary concern is flagging human writing as AI
3. **Intersectional awareness**: Bias may compound (e.g., ESL + short + unusual topic)
4. **Statistical rigor**: Confidence intervals, significance tests, not just point estimates
5. **Documentation mandatory**: Findings in `docs/LIMITATIONS.md` and `docs/EVALUATION.md`

## Prohibited Behavior
- ❌ Testing only on "average" essays
- ❌ Reporting only overall metrics without subgroup breakdown
- ❌ Ignoring bias findings because "overall F1 is good"
- ❌ Deploying without bias audit
- ❌ Claiming "no bias" without evidence

## Required Bias Dimensions

### 1. Second-Language English Writers
- Test set: Essays from known ESL writers (with consent)
- Metrics: FPR, FNR vs. native English baseline
- Analysis: Which features drive false positives?

### 2. Unusually Formal Human Writers
- Test set: Academic, legal, technical human writing
- Metrics: FPR vs. general human baseline
- Analysis: Formality features vs. AI signals

### 3. Heavily Edited Essays
- Test set: Professionally edited, multi-draft essays
- Metrics: FPR vs. single-draft baseline
- Analysis: Edit-induced regularity vs. AI regularity

### 4. Short Essays
- Test set: < 200 words, < 100 words, < 50 words
- Metrics: FPR, FNR by length bucket
- Analysis: Signal reliability at low token counts

### 5. Unusual Topics
- Test set: Creative, highly technical, personal/niche topics
- Metrics: FPR, FNR vs. common topic baseline
- Analysis: Topic-specific vocabulary effects

### 6. Intersectional
- Combinations above (e.g., ESL + short + formal)
- Minimum 50 samples per intersectional cell if possible

## Analysis Methods
- False Positive Rate comparison (subgroup vs. overall)
- Feature attribution: which features drive subgroup FPs?
- Calibration by subgroup: reliability diagrams per group
- Statistical tests: proportion z-test, chi-square for confusion matrices

## Mitigation Strategies (document even if not implemented)
- Subgroup-specific thresholds
- Feature reweighting
- Additional training data
- Uncertainty flagging for high-bias subgroups
- Human-in-the-loop for flagged subgroups

## Relevant Project Files
- `backend/app/evaluation/bias_audit.py`
- `docs/EVALUATION.md` - bias audit results
- `docs/LIMITATIONS.md` - documented bias limitations
- `docs/FAILURE-CASES.md` - bias-related failures
# Workflow: Red Team Review

## Trigger
- Pre-release (mandatory)
- Post-model-update
- Post-dataset-update
- Architect request
- Quarterly scheduled audit

## Process

### Quality Gate Chain (mandatory, no skips)
Quality Skill → Implementation → Tests → Static checks → Review → Documentation

### 0. Mandatory Skills
- Load `software-engineering-quality` and `test-driven-development`
- Any attack/evaluation code produced by this workflow must satisfy the quality
  gate (tests first for new scripts, lint clean, results documented)

### 1. Inspect Claims
- Read `docs/EVALUATION.md` — verify reported metrics
- Read `docs/ARCHITECTURE.md` — verify implementation matches
- Read UI — verify evidence-first, no verdict language
- Read `docs/LIMITATIONS.md` — verify honesty

### 2. Attack Assumptions
**Data Leakage:**
- Re-run leakage checks on current splits
- Check for new near-duplicates
- Verify AI prompt isolation across splits

**False Positives (Human → AI):**
- Run on ESL challenge set
- Run on formal human writing
- Run on heavily edited essays
- Run on short essays (< 200, < 100 words)
- Run on unusual topics

**False Negatives (AI → Human):**
- Run on models not in training
- Run on adversarial prompts ("write like human")
- Run on AI-human hybrids
- Run on paraphrased/translated AI

**Overfitting:**
- Train/test gap analysis
- Feature importance stability across CV folds
- Cross-model degradation measurement

**Bias:**
- Subgroup FPR/FNR comparison
- Intersectional analysis
- Calibration by subgroup

**Model-Family Dependence:**
- Test on 3+ model families not in training
- Measure performance drop

**Unsupported Claims:**
- Trace every UI evidence claim to feature value
- Verify no invented explanations
- Check uncertainty communication

**Explanation Consistency:**
- Same feature value → same explanation
- Ablation: remove feature → evidence changes appropriately
- Counterfactual: modify sentence → evidence changes

**Adversarial Patterns:**
- Prompt injection in essay
- Unicode homoglyphs, zero-width chars
- Repetition attacks
- Length manipulation
- Structure mimicry

### 3. Document Findings
- Update `docs/FAILURE-CASES.md` (3+ confident failures)
- Update `docs/LIMITATIONS.md`
- Create GitHub issues for each finding
- Notify Architect for architectural vulnerabilities

### 4. Verify Fixes
- Re-test after fixes applied
- Close issues only when verified
- Update regression test suite

## Agents Involved
- **Red Team Reviewer** (lead): Executes attacks
- **All Engineers**: Receive findings, implement fixes
- **Architect**: Receives architectural vulnerability reports
- **QA Engineer**: Adds adversarial cases to regression suite

## Gates
- **No release without Red Team Review pass**
- **No new evaluation/attack code without passing the quality gate (TDD, lint, docs)**
- **Critical findings block release**
- **All findings documented** (no silent drops)

## Prohibited
- ❌ Passing system with known critical flaws
- ❌ Testing only training-distribution data
- ❌ Ignoring bias audit requirements
- ❌ Accepting claims without feature evidence
- ❌ Silent approval
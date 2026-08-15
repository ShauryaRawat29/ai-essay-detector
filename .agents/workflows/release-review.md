# Workflow: Release Review

## Trigger
- Pre-deployment to any environment
- Scheduled release cadence
- Hotfix preparation

## Process

### Quality Gate Chain (mandatory, no skips)
Quality Skill → Implementation → Tests → Static checks → Review → Documentation

### 1. Run Tests
- Execute Testing workflow (full suite)
- All tests must pass
- No flaky tests unaddressed

### 2. Inspect Documentation
- `docs/ARCHITECTURE.md` — matches implementation?
- `docs/DECISIONS.md` — all ADRs current?
- `docs/DATASET.md` — provenance complete?
- `docs/EVALUATION.md` — current metrics recorded?
- `docs/LIMITATIONS.md` — honest and current?
- `docs/FAILURE-CASES.md` — 3+ failures documented?
- `docs/QUALITY-STANDARDS.md` — quality gate applied and green?
- `README.md` — setup instructions work?

### 3. Inspect Dataset Provenance
- All sources documented with licenses
- AI data: model, prompt, config, date for every sample
- Human data: consent verified
- Splits: document-level, leakage checks passed
- Version tagged

### 4. Inspect Evaluation
- Primary metrics: Precision, Recall, F1 (macro)
- Confusion matrix present
- Calibration reported
- Cross-model evaluation done
- Bias audit done (5+ dimensions)
- Failure analysis: 3+ cases
- No cherry-picking (all test sets reported)

### 5. Inspect Git Diff
- `git diff main..release-branch`
- No secrets, keys, .env files
- No model weights, large generated data
- No node_modules, .next, .venv
- Conventional commit messages
- Only intended files changed

### 6. Final Checklist
- [ ] All tests pass
- [ ] Quality gate green (TDD verified, lint, type checks, self/security review)
- [ ] Documentation current and honest
- [ ] Dataset provenance complete
- [ ] Evaluation rigorous and complete
- [ ] Git diff clean
- [ ] Red Team Review passed
- [ ] Architect sign-off
- [ ] Version bumped (semver)
- [ ] Changelog updated

### 7. Release
- Tag: `vX.Y.Z`
- Build artifacts
- Deploy to staging → production
- Monitor error rates, latency

## Agents Involved
- **Architect** (lead): Final sign-off
- **QA Engineer**: Test execution verification
- **Red Team Reviewer**: Review pass verification
- **All Engineers**: Documentation ownership
- **Dataset Engineer**: Provenance verification

## Gates
- **No release without ALL checklist items**
- **No release unless the software-engineering-quality gate passed**
- **No release with undocumented dataset changes**
- **No release without current evaluation**
- **No release with Red Team critical findings open**

## Prohibited
- ❌ Releasing without test pass
- ❌ Releasing with fabricated metrics
- ❌ Releasing with incomplete provenance
- ❌ Releasing with secrets in repo
- ❌ Silent releases (no tag, no changelog)
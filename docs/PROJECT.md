# PROJECT.md

## Project Objective
Build a real AI-writing analysis application for college admissions essays that provides evidence-based, sentence-level detection with honest evaluation and documented limitations.

## Hackathon Requirements
- Project 2 of the 2026 i12 HR Drive Hackathon by Callus
- "AI detector for admissions essays"
- Must NOT simply send essay to LLM and ask "Is this AI-generated?"
- Language model must only provide measurable signals (token probabilities, perplexity, entropy)
- Detection pipeline/classifier must be our own software

## Success Criteria (Architecture-First, Not Accuracy-Target)
1. **Working real interface**: Next.js frontend + FastAPI backend that accepts an essay and returns sentence/passage-level evidence
2. **Sentence-level and passage-level evidence**: Every flag traces to measurable feature values with human baselines
3. **Measurable detection methodology**: Feature extraction → classifier → evidence pipeline fully implemented and versioned
4. **Documented dataset provenance**: Every source recorded with license, collection date, preprocessing; AI data with model, prompt, config, date
5. **Leakage-free evaluation**: Document-level splits only; verified no duplicate/near-duplicate/prompt/writer overlap across splits; AI-polished leak groups handled
6. **Honest metrics**: Precision, Recall, F1 per class + macro; confusion matrix; calibration (Brier, reliability diagram); cross-model evaluation; bias audit (5+ subgroups)
7. **Three confident failure cases**: Documented with feature values, hypothesized reasons, mitigations
8. **Bias investigation**: Explicit audit on ESL, formal, edited, short, unusual topics; statistical significance tested
9. **Reproducible experiments**: Dataset version, feature version, model version, seeds, config recorded for every experiment
10. **Defensible architecture**: All decisions via ADR process; no silent changes; no LLM verdicts; evidence-first UI

## Non-Goals
- ❌ Perfect detection (impossible)
- ❌ "AI probability percentage" verdicts
- ❌ Real-time detection of all current/future models
- ❌ Replacing human review in admissions
- ❌ Detecting AI-assisted vs. fully AI-written (distinction not reliable)
- ❌ Multi-language support (English only for v1)

## Milestones (No Week-Based Timeline)
- **M1 — Architecture & Research**: ADRs recorded; literature review; EXP-001 designed
- **M2 — Dataset & Feature Engineering**: MVP dataset collected (provisional minimums); feature extractors implemented with golden tests; baselines computed
- **M3 — Model Training & Evaluation**: EXP-001 through EXP-007 executed; best model selected; calibration validated; bias audit passed
- **M4 — Backend & Frontend Implementation**: `/api/v1/analyze` contract fulfilled; evidence UI (highlighting, tooltips, panels, limitations notice); accessibility (WCAG AA)
- **M5 — Red Team Review & Release**: Adversarial testing; failure cases documented; limitations finalized; reproducible artifacts packaged

## Team Roles
See `.agents/agents/` for role definitions.
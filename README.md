# AI Essay Detector

Evidence-based AI-writing analysis for college admissions essays: sentence/passage-level
evidence, honest evaluation, documented limitations. Built for Project 2 of the 2026 i12
HR Drive Hackathon (Callus).

GPT-2 Medium is used **only as an instrument** to produce measurable signals (perplexity,
entropy, token probabilities). It never renders an authorship verdict. Detection comes from
our own feature extraction + classifier + evidence pipeline. See `AGENTS.md` for the
non-negotiable detector principles and `docs/` for architecture, ADRs, and methodology.

## Status

Foundation phase (Phase 1) is implemented: backend health endpoint, model registry,
config, rate limiting, and frontend↔backend connectivity.

Phase 2 (sentence splitting + feature extraction) is implemented: a deterministic
spaCy sentence splitter, stylometric and syntactic feature extractors, passage
windowing (ADR-003) with paragraph fallback, and a versioned feature registry.

Phase 3 (LM signals) is implemented: the gpt2-medium instrument
(`backend/app/models/lm_instrument.py`, pinned revision, full-context causal
scoring) provides 8 measurable sentence-level signals (perplexity, token
entropy, log-prob, rank, probability curvature) consumed by the feature
registry (`f0.3.0`). The LM is an instrument only — it never produces an
authorship verdict.

Phase 4 (baseline machinery) is implemented: the ADR-004 human-baseline
pipeline (length buckets, min-N=30 merge fallback, per-feature statistics,
versioned `baselines_{feature_version}.json` artifacts) is built and unit-tested
on synthetic data. Real baselines await the human training split.

Phase 5 (dataset machinery + source research) is implemented: the versioned
dataset builder (`backend/app/datasets/` — schema/provenance validation,
preprocessing, SHA-256 dedup, document-level stratified splits with
`test_cross_model` and `test_secondary` leak groups, records.jsonl +
manifest.json) is unit-tested (44 tests), and licensed human/AI source
candidates are documented in `docs/DATASET.md`. The AI essay generation
pipeline (`app/datasets/generator.py`, 15 tests) produces provenance-complete
AI-authored records via the pinned gpt2-medium instrument (config table:
standard/creative/focused/adversarial, seeded & deterministic, length quality
guards). The quality gate now includes ruff + mypy (both green). No data has
been collected/generated yet (dataset v0.1.0 pending). Classifier and evidence
generation are later phases.

## Prerequisites

- Python 3.11+ (dev machine: 3.14.3)
- Node.js (dev machine: Next.js 16.3.1)
- CUDA GPU optional; CPU fallback supported

## Backend

```powershell
cd backend
# create venv if needed
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# optional: copy .env.example to .env and adjust
uvicorn app.main:app --reload
```

- Health check: `GET http://127.0.0.1:8000/api/v1/health`
- Tests: `.\.venv\Scripts\python.exe -m pytest` (153 tests: Phase 1 + Phase 2 features + Phase 3 LM signals + Phase 4 baselines + Phase 5 dataset machinery + generation; model weights load on first LM test)
- Lint: `.\.venv\Scripts\ruff.exe check app tests`; Types: `.\.venv\Scripts\mypy.exe app`

The health endpoint reports API/app/python versions, CUDA availability + GPU name, and
model status. It never loads GPT-2.

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend proxies `/api/*` to the backend (see `next.config.ts`). To call the backend
directly instead, set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` (see `.env.example`).

- Verify connectivity: open `http://127.0.0.1:3000` — it fetches `/api/v1/health` and shows
  backend status.

## Docs

- `docs/ARCHITECTURE.md` — system design + implementation status
- `docs/DECISIONS.md` — ADR-001…009
- `docs/METHODOLOGY.md`, `docs/DATASET.md`, `docs/EXPERIMENTS.md`, `docs/EVALUATION.md`,
  `docs/LIMITATIONS.md`, `docs/FAILURE-CASES.md`

## Git Rules

Never commit: `.env`, model weights, datasets, `node_modules/`, `.next/`, `.venv/`.
Commits use Conventional Commits format.
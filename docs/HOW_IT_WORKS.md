# HOW IT WORKS

A complete walkthrough of the AI Essay Detector: what was built, why, how it
works, what data was used, how it was evaluated, and where it fails. This is
the "everything" document — read `AGENTS.md` for the non-negotiable principles,
`ARCHITECTURE.md` for the system diagram, and this file for the story.

---

## 1. What This Project Is

A web application that analyzes college admissions essays and reports
**machine-like writing signals** with **sentence-level evidence** and **honest
limitations**. It does NOT say "this is AI" — it says which measurable features
deviate from a human baseline and how strongly.

### Why it's different from a naive "AI detector"
Most detectors send an essay to an LLM and ask "is this AI?" — that is an
opaque black box. This project instead:

1. **Measures** dozens of objective features (perplexity, entropy, sentence-length
   regularity, lexical diversity, POS distributions, readability, repetition).
2. **Compares** each feature to a real distribution of human admissions essays.
3. **Reports** the deviation (z-score) per sentence and per passage.
4. **Admits** uncertainty — short, edited, or second-language essays can look
   unusual for reasons unrelated to AI.

The language model (GPT-2 Medium) is used **only as an instrument** that emits
measurable token signals (log-probability, entropy, rank). It never makes the
final judgement.

---

## 2. What Was Built (What I Did)

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 1 | FastAPI backend + health endpoint + rate limiting + CORS | ✅ Done |
| 2 | Feature extraction (stylometric + syntax), sentence splitter, passage windows | ✅ Done |
| 3 | GPT-2 Medium instrument + 8 LM signal features | ✅ Done |
| 4 | Human baseline machinery (length buckets, statistics) | ✅ Done |
| 5 | Dataset builder + AI essay generation pipeline (checkpointed, resumable) | ✅ Done |
| 6 | Real human dataset v0.1.0 (6,039 essays) + real baselines f0.3.0 (480 essays) | ✅ Done |
| 7 | Evidence scoring pipeline (z-scores → sentence/passage signals) | ✅ Done |
| 8 | `/api/v1/analyze` endpoint returning `AnalysisResult` | ✅ Done |
| 9 | Next.js evidence-first frontend | ✅ Done |
| 10 | 200+ tests, ruff + mypy green | ✅ Done |

**Quality gate:** every component was written test-first (TDD), linted (ruff),
and type-checked (mypy) before being called complete.

---

## 3. The Detection Pipeline (How It Works)

```
Essay text
   │
   ▼
[Sentence Splitter]  spaCy, deterministic
   │
   ▼
[Feature Extraction]  per sentence + passage windows (k=3, stride=1)
   │  ├─ Stylometric : TTR, word length, sentence length, MATTR/MTLD,
   │  │               n-gram repetition, lexical recurrence, 5 readability scores,
   │  │               rhythm (punct density, sent-length stats, clause density)
   │  ├─ Syntax      : POS entropy, dependency depth, clause density,
   │  │               17 universal POS tag frequencies
   │  └─ LM signals  : perplexity, token entropy mean/std, log-prob mean/std,
   │                  rank mean/std, probability curvature (GPT-2 Medium, one
   │                  full-context causal pass over the whole essay)
   │
   ▼
[Baseline Lookup]  essay word count → length bucket
   │                (short <200 / standard 200-500 / long 500-800 / xlong >800)
   │                → per-feature human stats (mean, std, p5–p95) from train split
   │
   ▼
[Evidence Scoring]  per sentence & passage:
   │    z = (measured - baseline_mean) / baseline_std
   │    |z| ≥ 2 → high     |z| ≥ 1 → medium     else → low     no baseline → uncertain
   │
   ▼
[AnalysisResult]   JSON: sentences, passages, summary counts, limitations
   │
   ▼
[Frontend]         evidence-first UI: highlights, signal tables, limitations notice
```

### Evidence strength
- **high** — one or more features ≥ 2 standard deviations from the human baseline
- **medium** — one or more features ≥ 1σ (none ≥ 2σ)
- **low** — all scored features within 1σ
- **uncertain** — no comparable baseline for that feature/bucket

---

## 4. The Data

### Human essays (dataset v0.1.0) — 6,039 essays
| Source | Count | Notes |
|--------|-------|-------|
| VIORRA | 128 | Admissions essays |
| LEAF (Essays) | 4,917 | Human-written essays |
| Ghostbuster-human | 994 | Human subset of Ghostbuster corpus |

**Splits** (document-level, stratified by source + length, seed 42 — never
sentence-level, so no leakage):

| Split | Count |
|-------|-------|
| Train | 4,230 |
| Val | 905 |
| Test | 904 |

**Dedup:** SHA-256 exact hashing — 0 duplicates removed.

### Human baselines (f0.3.0) — computed from the TRAIN split ONLY
- 480 human essays scored
- 40 features per length bucket (incl. 8 LM signals)
- 8,817 sentence samples
- Length buckets: short 188 / standard 7,624 / long 1,005 / xlong 0 sentences

> **Important honest note:** baselines come from the training split only, so
> comparing any new essay against them is leakage-free by construction. The
> standard bucket has heavy right-skew on perplexity (p50=24.7 vs mean=558),
> so evidence strength uses the deviation (z) not raw magnitude.

---

## 5. How It Was Evaluated

The full classifier with precision/recall/F1/calibration is a **later phase**
(needs the AI-generated dataset). The v0.1.0 deliverable is the **evidence
pipeline**, which was validated by:

- **200+ automated tests** (unit + integration + pipeline), all green
- **ruff lint** clean (38 files)
- **mypy typecheck** clean (38 files)
- **Frontend build** (Next.js 16) clean
- **Live end-to-end run**: a real essay produced real per-sentence evidence
  (7 high / 3 medium signals out of 10 sentences; top features pos_PART,
  perplexity, token_entropy_mean, pos_DET)

### Documented limitations (surfaced in every response)
1. Measures signals, not authorship — evidence, not proof.
2. LM is an instrument only; never judges.
3. Baselines from 480 human essays (train split, v0.1.0); other populations unknown.
4. Only features with a baseline are scored.
5. Short / heavily-edited / second-language essays can look unusual for reasons
   unrelated to AI.
6. Essays > 1024 tokens are rejected (LM context window; no sliding window yet).
7. xlong bucket (>800 words) has no baseline — falls back to nearest bucket.

---

## 6. Where It Fails (Honest Gaps)

- **No classifier yet** — the evidence pipeline does not output a combined
  prediction or probability. It is a "feature deviation report".
- **AI-generated dataset not complete** — the batch generation was started but
  not finished; so no trained classifier and no cross-model evaluation yet.
- **1024-token cap** — longer essays can't be fully LM-scored.
- **Bias audit pending** — ESL / formal / heavily-edited / unusual-topic
  subgroups not yet statistically tested (documented in `docs/LIMITATIONS.md`).
- **Baseline sample small** — 480 human essays; the short bucket (188 sentences)
  is the least populated.

These are recorded as `TODO:` items in `docs/` — nothing is claimed that wasn't
built.

---

## 7. Reproducibility

Every artifact records its version and provenance:
- **Dataset v0.1.0** — manifest.json (sources, counts, splits, dedup, seed)
- **Baselines f0.3.0** — baselines_f0.3.0.json (schema 1.0, dataset v0.1.0, buckets)
- **Features f0.3.0** — registry version, deterministic extractors
- **LM instrument** — gpt2-medium @ pinned revision `6dcaa7a952f72f9298047fd5137cd6e4f05f41da`
- **AI generation** — generator records model, prompt, config (incl. seed), date
- **API** — every response includes feature_version + model_version + baselines_version

---

## 8. Quick Reference

| Task | Command |
|------|---------|
| Run backend | `cd backend && .venv\Scripts\uvicorn.exe app.main:app --port 8000` |
| Run frontend | `cd frontend && npm run dev` |
| Backend tests | `cd backend && .\.venv\Scripts\python.exe -m pytest` |
| Backend lint | `cd backend && .\.venv\Scripts\ruff.exe check app tests` |
| Backend types | `cd backend && .\.venv\Scripts\mypy.exe app` |
| Frontend lint | `cd frontend && npm run lint` |
| Frontend build | `cd frontend && npm run build` |

---

## 9. The Non-Negotiable Principles (why it's built this way)

1. **Evidence over verdicts** — never claim authorship as fact.
2. **No opaque LLM judgement** — the LM only provides signals we consume.
3. **Sentence & passage level** — never just an overall score.
4. **Every flag has evidence** — never invent explanations.
5. **Dataset provenance** — every source documented.
6. **No data leakage** — document-level splits only.
7. **Honest evaluation** — precision/recall/F1, confusion matrix, calibration.
8. **Bias investigation** — explicit audits.
9. **Reproducibility** — versions, seeds, configs recorded.
10. **Documentation is part of the product** — a reviewer can understand it all.

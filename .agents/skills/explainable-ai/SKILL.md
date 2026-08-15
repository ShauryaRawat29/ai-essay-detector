# Skill: explainable-ai

## Purpose
Generating human-understandable evidence from feature values: mapping raw features to evidence descriptions, ensuring every claim traces to measurable data, and preventing invented explanations.

## When to Use
- Implementing evidence generation from feature vectors
- Designing evidence tooltips and panels
- Validating explanation fidelity
- Auditing UI claims against feature data

## Core Rules
1. **Every claim traces to a feature value**: No "AI-like" without measurable support
2. **No invented explanations**: If feature X doesn't exist, don't explain with X
3. **Uncertainty is explicit**: "Uncertain" when features conflict or are weak
4. **Comparative framing**: Feature values shown relative to human/AI baselines
5. **Feature ablation consistency**: Removing a feature should change evidence predictably

## Prohibited Behavior
- ❌ "This looks AI-generated because..." without feature citation
- ❌ Explanations for features not in the pipeline
- ❌ Hiding uncertainty when features are ambiguous
- ❌ Using LLM to generate explanations
- ❌ Binary "AI/Human" labels in explanations

## Evidence Generation Pipeline
```
Raw Feature Values
    ↓
Per-signal scoring (z-score vs. human baseline, or calibrated probability)
    ↓
Evidence strength classification (low/medium/high/uncertain)
    ↓
Natural language evidence description (template-based, not LLM)
    ↓
UI rendering (tooltip, panel, highlight)
```

## Evidence Description Templates
**Per-signal (example):**
- "Perplexity: 42.3 (human baseline: 120.5 ± 35.2) — unusually low, suggesting predictable token choices"
- "Token entropy: 2.1 (human baseline: 3.8 ± 0.9) — low entropy indicates less surprising word choices"
- "Sentence length CV: 0.15 (human baseline: 0.35 ± 0.12) — unusually regular sentence lengths"

**Aggregation:**
- "3 of 8 sentences show machine-like signals (low perplexity, low entropy)"
- "Passages 2-4 exhibit consistent low-entropy pattern across 5 sentences"

**Uncertainty:**
- "Conflicting signals: low perplexity but high lexical diversity — uncertain"
- "Short essay (120 words) — limited evidence, interpret with caution"

## Baseline References
- Human baselines computed from training human set
- Stored as: mean, std, percentiles per feature
- Versioned with feature version
- Updated only with dataset version bump

## Relevant Project Files
- `backend/app/explainability/` - evidence generation
- `backend/app/schemas.py` - evidence output schemas
- `frontend/src/components/EvidenceTooltip.tsx`
- `frontend/src/components/EvidencePanel.tsx`
- `docs/METHODOLOGY.md` - evidence generation approach
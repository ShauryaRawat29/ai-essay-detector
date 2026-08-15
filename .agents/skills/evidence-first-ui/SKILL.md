# Skill: evidence-first-ui

## Purpose
Building UI that presents evidence over verdicts: sentence highlighting, evidence tooltips, explainability panels, uncertainty visualization, and accessibility.

## When to Use
- Designing or implementing any user-facing detection results
- Creating evidence visualization components
- Writing evidence display logic
- Auditing UI for misleading presentations

## Core Rules
1. **No verdict language**: Never "AI-generated: Yes", "Probability: 87%", "Human: 95%"
2. **Evidence-first**: Lead with "Machine-like signals detected in X sentences"
3. **Sentence-level primary**: Overall summary is secondary to sentence evidence
4. **Feature transparency**: Every highlight links to actual feature values
5. **Uncertainty visible**: "Uncertain" is a first-class state
6. **Calibrated color**: No red=AI, green=Human; use neutral evidence scale
7. **Accessibility mandatory**: WCAG AA, keyboard navigation, screen readers

## Prohibited Behavior
- ❌ Binary AI/Human labels or colors
- ❌ Percentage certainty displays
- ❌ Hiding uncertainty in tooltips
- ❌ "Confidence" without calibration
- ❌ Invented explanations not in feature data
- ❌ Inaccessible color-only signaling

## Component Specifications

### Essay Input
- Textarea with word/character count
- Paste handling (preserve paragraphs)
- Clear button
- Analyze button (disabled while processing)

### Results: Evidence Summary (Top)
- "Analysis complete. Found machine-like signals in 3 of 8 sentences."
- "Uncertain: 2 sentences have conflicting signals"
- Limitations notice prominent: "This detector has known limitations..."

### Results: Sentence View (Main)
- Each sentence rendered with highlight overlay
- Highlight intensity = evidence strength (subtle, not alarming)
- Hover/focus → Evidence Tooltip
- Click → Evidence Panel detail
- Keyboard navigable (Tab/Enter between sentences)

### Evidence Tooltip
- Sentence text (truncated, expandable)
- Top 3 signals with values and baselines
- Evidence strength badge
- "View details" link to panel

### Evidence Panel (Side/Bottom)
- Per-sentence feature table (searchable, sortable)
- Passage-level aggregates
- Baseline comparison charts (optional)
- Limitations/uncertainty section

### Color System (Semantic, Not Binary)
- `evidence-none`: Neutral gray
- `evidence-low`: Cool blue (subtle)
- `evidence-medium`: Warm amber
- `evidence-high`: Deep orange
- `evidence-uncertain`: Purple pattern/hatch
- All colors meet 4.5:1 contrast on light/dark backgrounds

## Accessibility Requirements
- Focus visible on all interactive elements
- Screen reader: "Sentence 3, medium evidence, low perplexity, view details"
- Keyboard: Tab between sentences, Enter for panel, Escape to close
- Reduced motion: Disable highlight animations
- High contrast mode support

## Relevant Project Files
- `frontend/src/components/EvidenceSummary.tsx`
- `frontend/src/components/SentenceView.tsx`
- `frontend/src/components/EvidenceTooltip.tsx`
- `frontend/src/components/EvidencePanel.tsx`
- `frontend/src/styles/evidence.css` (or Tailwind config)
- `docs/ARCHITECTURE.md` - UI data flow
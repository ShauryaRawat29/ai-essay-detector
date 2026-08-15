<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# Frontend-Specific Rules

## Software Engineering Quality (Mandatory)

All frontend work MUST follow the `software-engineering-quality` skill and the
quality gate in `docs/QUALITY-STANDARDS.md`, and MUST follow
`test-driven-development` (tests written and observed to fail first). See
`../AGENTS.md`. Run the actual lint/build/test commands before claiming a check
passed.

## Technology Stack
- Next.js 15+ (App Router)
- TypeScript (strict mode)
- Tailwind CSS v4
- React 19

## Project Structure
```
frontend/
├── src/
│   ├── app/                    # App Router pages
│   │   ├── page.tsx           # Home: essay input
│   │   ├── analyze/           # Analysis results (dynamic route)
│   │   └── layout.tsx         # Root layout
│   ├── components/            # React components
│   │   ├── EssayInput.tsx
│   │   ├── EvidenceSummary.tsx
│   │   ├── SentenceView.tsx
│   │   ├── EvidenceTooltip.tsx
│   │   ├── EvidencePanel.tsx
│   │   └── LimitationsNotice.tsx
│   ├── lib/
│   │   ├── api.ts             # Backend API client
│   │   ├── types.ts           # TypeScript types matching API
│   │   └── utils.ts
│   ├── styles/
│   │   └── globals.css        # Tailwind + custom evidence styles
│   └── hooks/
│       └── useAnalysis.ts     # Analysis state management
├── public/
├── package.json
├── tsconfig.json
├── next.config.ts
├── eslint.config.mjs
└── postcss.config.mjs
```

## Evidence-First UI Rules (Non-Negotiable)

### Prohibited
- ❌ "AI Probability: XX%" or any percentage certainty display
- ❌ Binary "AI-Generated: Yes/No" or "Human: Yes/No" labels
- ❌ Red/Green color coding for AI/Human
- ❌ "Confidence" language without calibration backing
- ❌ Hiding uncertainty in tooltips or panels
- ❌ Invented explanations not backed by feature values
- ❌ Single overall score without sentence-level evidence

### Required
- ✅ Lead with: "Machine-like signals detected in X of Y sentences"
- ✅ Sentence-level highlighting with evidence tooltips
- ✅ Tooltips show actual feature values vs. human baselines
- ✅ Evidence strength: "low" | "medium" | "high" | "uncertain"
- ✅ Limitations notice prominent on every result
- ✅ Neutral color scale (no red=AI, green=Human)
- ✅ "Uncertain" as first-class state

## Component Contracts

### EssayInput
- Props: `onAnalyze: (text: string) => void`, `disabled: boolean`
- Textarea: min-height 300px, word/char count, paste handling
- Validation: client-side length check (max 10000 chars)

### EvidenceSummary
- Props: `sentenceCount: number`, `signalCount: number`, `uncertainCount: number`, `limitations: string[]`
- Shows: Summary stats + prominent limitations

### SentenceView
- Props: `sentences: SentenceEvidence[]`, `onSelect: (index: number) => void`, `selectedIndex: number`
- Renders each sentence with highlight overlay
- Keyboard navigable (Tab/Enter)
- Highlight intensity by `evidence_strength`

### EvidenceTooltip
- Props: `sentence: SentenceEvidence`, `position: {x, y}`
- Shows: sentence text, top 3 signals with values/baselines, evidence strength
- "View details" → opens EvidencePanel

### EvidencePanel
- Props: `sentences: SentenceEvidence[]`, `passages: PassageEvidence[]`, `limitations: string[]`
- Per-sentence feature table (sortable, searchable)
- Passage aggregates
- Limitations section

## TypeScript Types (Mirror API Contract)
```typescript
interface SignalValue {
  value: number;
  baseline_mean: number;
  baseline_std: number;
  evidence: 'low' | 'medium' | 'high' | 'uncertain';
}

interface SentenceEvidence {
  index: number;
  text: string;
  signals: Record<string, SignalValue>;
  evidence_strength: 'low' | 'medium' | 'high' | 'uncertain';
  evidence_summary: string;
}

interface PassageEvidence {
  sentence_indices: number[];
  aggregated_signals: Record<string, SignalValue>;
  evidence_summary: string;
}

interface AnalysisResult {
  analysis_id: string;
  timestamp: string;
  feature_version: string;
  model_version: string;
  sentences: SentenceEvidence[];
  passages: PassageEvidence[];
  limitations: string[];
}
```

## API Client
- Base URL from `NEXT_PUBLIC_API_URL` env var
- Request timeout: 30s
- Retry: 2x with exponential backoff
- Error handling: map to user-friendly messages

## Styling
- Tailwind v4 (CSS-first config)
- Custom evidence colors in `globals.css`:
  ```css
  :root {
    --evidence-none: #6b7280;
    --evidence-low: #3b82f6;
    --evidence-medium: #f59e0b;
    --evidence-high: #ea580c;
    --evidence-uncertain: #8b5cf6;
  }
  ```
- Dark mode support via `@media (prefers-color-scheme: dark)`

## Accessibility (WCAG AA Minimum)
- Semantic HTML structure
- Focus visible on all interactive elements
- Keyboard navigation for sentence highlighting
- Screen reader announcements for evidence
- Color contrast ≥ 4.5:1 (all evidence colors)
- Reduced motion: disable highlight animations
- High contrast mode support

## Testing
- Unit: Jest + React Testing Library
- Integration: Playwright for analysis flow
- Accessibility: axe-core in CI
- Visual regression: sentence highlight accuracy

## Environment Variables
- `NEXT_PUBLIC_API_URL` - Backend API base URL
- No other client-side secrets

## Git Ignore (Frontend)
- `node_modules/`
- `.next/`
- `*.log`
- `.env.local` (if exists)
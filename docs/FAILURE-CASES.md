# FAILURE-CASES.md

## Confident Failure Cases

Per evaluation requirements: 3+ confidently incorrect predictions with analysis.

---

### FC-001: [Placeholder]

**Input**: [Essay excerpt or full text if short]
**Ground Truth**: Human / AI
**Prediction**: Human / AI (score: X.XX)
**Evidence Shown**: [What the UI would display]

**Feature Values**:
| Feature | Value | Human Baseline (mean±std) | Z-Score |
|---------|-------|---------------------------|---------|
| TODO | TODO | TODO | TODO |

**Hypothesized Reason**: [Why the detector failed]
- e.g., "Formal human writing mimics low perplexity pattern"
- e.g., "Short essay length → unreliable entropy estimate"
- e.g., "AI-polished human: hybrid signals confuse classifier"

**Mitigation Ideas**:
- [ ] Feature adjustment
- [ ] Additional training data
- [ ] Uncertainty flagging for this pattern
- [ ] Subgroup-specific threshold

**Status**: Open / Investigating / Mitigated / Won't Fix

---

### FC-002: [Placeholder]
[Same format]

---

### FC-003: [Placeholder]
[Same format]

---

## Failure Categories (For Tagging)

| Category | Description | Count |
|----------|-------------|-------|
| ESL_FP | ESL writer flagged as AI | 0 |
| FORMAL_FP | Formal human flagged as AI | 0 |
| EDITED_FP | Heavily edited human flagged as AI | 0 |
| SHORT_FP | Short human essay flagged as AI | 0 |
| TOPIC_FP | Unusual topic human flagged as AI | 0 |
| CROSS_MODEL_FN | Unseen AI model not detected | 0 |
| ADVERSARIAL_FN | Adversarial prompt not detected | 0 |
| HYBRID_FN | AI-human hybrid not detected | 0 |
| CALIBRATION | Confident but wrong | 0 |
| EXPLANATION_MISMATCH | Evidence doesn't match features | 0 |

## Resolution Tracking
| Failure ID | Category | Resolution | Date | Verified |
|------------|----------|------------|------|----------|
| FC-001 | TODO | TODO | TODO | No |
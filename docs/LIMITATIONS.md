# LIMITATIONS.md

## Documented Limitations

Honest accounting of what the detector cannot do, where it fails, and what remains uncertain.

---

## Technical Limitations

### L-001: Minimum Essay Length
- **Issue**: Statistical signals (perplexity, entropy, diversity) unreliable below ~150 words
- **Impact**: Short essays (< 150 words) have high uncertainty
- **Mitigation**: Flag uncertainty prominently; don't show sentence highlights for very short text; `min_words_for_evidence: 150` in config
- **Status**: Documented, not resolved

### L-002: Local LM Instrument Coverage
- **Issue**: LM signals only meaningful relative to the specific instrument model (GPT-2 Medium provisional)
- **Impact**: Cross-model generalization unproven; new model families may evade detection
- **Mitigation**: Train on multiple model families; explicit cross-model evaluation (EXP-001, EXP-018+)
- **Status**: Under investigation

### L-003: Classifier Calibration Drift
- **Issue**: Calibration on validation set may not hold on truly OOD data
- **Impact**: Evidence strength labels (low/med/high) may be miscalibrated
- **Mitigation**: Regular recalibration; uncertainty flag for OOD feature values
- **Status**: Monitoring

### L-004: Sentence Segmentation Errors
- **Issue**: spaCy may mis-segment admissions essays (bullet points, fragments, dialogue)
- **Impact**: Feature misalignment; wrong sentence highlighted
- **Mitigation**: Custom segmentation rules for admissions format; test on edge cases
- **Status**: Known, needs validation

---

## Dataset Limitations

### L-005: Limited ESL Representation
- **Issue**: Training data has few verified ESL admissions essays
- **Impact**: Higher false positive rate for ESL writers (preliminary)
- **Mitigation**: Actively source ESL essays with consent; bias audit required (EXP-007)
- **Status**: Active gap

### L-006: Limited Topic Diversity
- **Issue**: Topics clustered around common prompts; unusual topics underrepresented
- **Impact**: Unusual topics may trigger false signals (rare vocabulary → low diversity)
- **Mitigation**: Augment with diverse topic generation; document coverage
- **Status**: Documented

### L-007: AI Model Coverage
- **Issue**: Training covers only {TODO} model families
- **Impact**: Unknown performance on Claude, Gemini, future models
- **Mitigation**: Regular cross-model evaluation; document as limitation
- **Status**: By design (explicitly documented)

### L-008: AI-Polished Human Essays (per ADR-008)
- **Issue**: Detector trained on binary primary (human vs fully AI); hybrids (`ai_polished` label) not a training class in MVP
- **Impact**: AI-polished human essays evaluated only on secondary test set; may be misclassified either way with high uncertainty
- **Mitigation**: Generate more hybrid data; uncertainty flag for conflicting signals; revisit multiclass if bias audit fails
- **Status**: Under investigation

---

## Bias Concerns

### L-009: ESL False Positives
- **Preliminary finding**: ESL writers show lower perplexity, more regular structure
- **Risk**: Discriminatory impact on non-native applicants
- **Required**: Explicit bias audit before any deployment (EXP-007)
- **Status**: Must fix before release

### L-010: Formal Writing False Positives
- **Preliminary finding**: Highly formal human writing mimics AI regularity
- **Risk**: Penalizes strong academic writers
- **Required**: Bias audit on formal writing corpus (EXP-007)
- **Status**: Must fix before release

### L-011: Short Essay Reliability
- **Issue**: All signals degrade with length; short essays (< 200 words) near-random
- **Risk**: Admissions essays vary in length; some prompts require short responses
- **Required**: Minimum length warning; possibly decline to score
- **Status**: Documented

---

## False Positive / False Negative Analysis

### False Positives (Human → AI)
Most likely for:
1. ESL writers (formal, regular, low diversity)
2. Highly edited/professional essays
3. Template/formulaic human writing
4. Very short essays
5. Unusual technical/creative topics

### False Negatives (AI → Human)
Most likely for:
1. Models not in training set
2. Adversarial prompting ("add errors", "write casually")
3. AI-human hybrids (AI outline + human write)
4. Post-processed AI (paraphrase, translation loop)
5. High-temperature generation

---

## Authorship Uncertainty

### Fundamental Limitation
**AI authorship cannot be proven from text alone.** This detector identifies *statistical patterns associated with known AI generators in our training data*. It does not and cannot:
- Prove a specific essay was written by AI
- Detect all possible AI generators (current or future)
- Distinguish AI-assisted from fully AI-written
- Account for human editing of AI drafts (or vice versa)

### Communication Requirement (per ADR-008, ADR-009)
All outputs must use language:
- "Machine-like writing signals detected"
- "Higher evidence of AI-like patterns"
- "Lower evidence"
- "Uncertain — limited statistical power"

**Never**: "AI-generated", "X% AI", "Written by AI", "Human-written", "Confidence: X%"

---

## Unresolved Questions
- [ ] UQ-001: Can we reliably detect AI-polished human essays?
- [ ] UQ-002: What is the true cross-model generalization gap?
- [ ] UQ-003: How does detector perform on handwritten→OCR essays?
- [ ] UQ-004: Can adversarial prompts be systematically defended against?
- [ ] UQ-005: What's the optimal uncertainty communication for admissions officers?

---

## Review Schedule
- Limitations reviewed at each Release Review (M5)
- Bias audit repeated with each model/dataset update
- Failure cases updated with each evaluation
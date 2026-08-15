# RESEARCH.md

## Research Questions

### RQ-001: What measurable signals distinguish AI from human admissions essays?
- Sub-questions:
  - Perplexity/entropy patterns in short, structured essays?
  - Stylometric markers specific to admissions essay genre?
  - Sentence-level vs. passage-level signal strength?

### RQ-002: What are known failure modes of current AI detectors?
- False positives on: ESL, formal, edited, short, template writing
- False negatives on: New models, adversarial prompts, hybrids
- Calibration failures on out-of-distribution text

### RQ-003: Which local language models provide useful instrument signals?
- **GPT-2 Medium (355M)**: Baseline, well-understood, CPU-runnable, MIT license — **CURRENT PROVISIONAL INSTRUMENT (per ADR-001)**; usefulness must be experimentally validated via EXP-001
- **Llama-3-8B-Instruct**: Stronger, more recent; candidate for EXP-001 comparison
- **Smaller models (DistilGPT-2, TinyLlama)**: For speed/ablation only

### RQ-004: What stylometric features are validated for short texts?
- Lexical diversity measures (MTLD, HD-D for < 500 words)
- Readability formulas reliability at short lengths
- Syntactic complexity measures

### RQ-005: How to prevent data leakage in essay-level splits?
- Document-level splitting strategies
- Near-duplicate detection thresholds
- Writer overlap detection
- AI-polished leak group handling (original + polished = same split)

## Sources

| Source | Type | Key Findings | Confidence | Link |
|--------|------|--------------|------------|------|
| TODO: Add papers | | | | |

## Findings

### Signal: Perplexity
- **Finding**: AI text tends to have lower perplexity under the generating model
- **Caveat**: Depends on model match; human can have low perplexity if formal
- **Applicability**: Strong for same-model detection; weaker cross-model
- **Confidence**: High

### Signal: Token Entropy
- **Finding**: AI distributions often sharper (lower entropy)
- **Caveat**: Temperature affects; human editing reduces entropy
- **Confidence**: Medium

### Signal: Sentence Length Regularity
- **Finding**: AI often produces more uniform sentence lengths
- **Caveat**: Admissions essays naturally structured; edited human also regular
- **Confidence**: Medium

### Signal: Lexical Diversity (MTLD/HD-D)
- **Finding**: AI can show lower diversity; but prompted diversity varies
- **Caveat**: Short texts make TTR unreliable; MTLD/HD-D better
- **Confidence**: Medium

## Unresolved Questions

- [ ] UQ-001: Optimal passage window size for admissions essays (typically 500-1000 words)?
- [ ] UQ-002: How much does prompt engineering affect signal reliability?
- [ ] UQ-003: Can we detect AI-polished human essays reliably? (per ADR-008 limitation)
- [ ] UQ-004: What's the minimum essay length for reliable signals?
- [ ] UQ-005: Cross-model generalization: how many model families needed in training?
- [ ] UQ-006: EXP-001: Does stronger LM (Llama-3-8B) provide >5% cross-model gain over GPT-2 Medium?
- [ ] UQ-007: What feature ablation profile maximizes robustness vs. bias?

## Next Steps
- [ ] Conduct literature review (assign to Research agent)
- [ ] Design EXP-001 matrix (ML Experimentation workflow)
- [ ] Identify dataset sources (Dataset Engineering workflow)
- [ ] Validate provisional MVD floors with Dataset Engineer
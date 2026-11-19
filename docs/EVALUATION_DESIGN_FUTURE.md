# Evaluation Design (Future — Phase 2+)

This document is a placeholder for the Phase 2 evaluation system. **Do not treat any of this as implemented in Phase 1.**

## Intended capabilities

- Batch datasets of synthetic banking dialogues and edge cases
- Independent LLM judges for personality adherence vs banking policy compliance
- Banking quality checks (hallucination, omission of critical caveats, tool grounding)
- Measured score overlays on the radar (never fabricate these in Phase 1)
- A/B comparison runs across presets and models
- Upload / export of evaluation manifests

## Separation from Phase 1

Phase 1 ships live chat + Requested (TARGET) profile visualization only. The nav item **Batch Evaluation — Phase 2** is intentionally disabled. No judge prompts, scoring UIs, or Measured series should appear until Phase 2 work begins.

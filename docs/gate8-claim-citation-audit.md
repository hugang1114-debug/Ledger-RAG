# Gate 8 Claim-to-Citation Audit

Source audit: `configs/gate8/main_v1_corrected_50x6x3_claim_citation_audit.yaml`

This audit uses existing run artifacts only. It made no API calls and does not track raw model answers.

## Diagnostic Status

This audit is historical diagnostic evidence. It should be used to motivate the new attribution protocol, not as paper-grade semantic attribution evidence.

## What Was Checked

| Check | Meaning | New status |
|---|---|---|
| Claim citation coverage | Whether each generated atomic claim has at least one citation | Core metric, but must count only structurally valid citations in future runs. |
| Invalid citation rate | Whether cited evidence IDs exist in retrieved evidence | Core metric, now generalized to pointer validation categories. |
| Lexical support rate | Whether claim keywords overlap with cited evidence text | Debugging diagnostic only. |

The lexical support check is a heuristic. It can flag suspicious citations but cannot establish entailment.

## Diagnostic Result

| Metric | Value |
|---|---:|
| Run records | 900 |
| Claims | 2024 |
| Citations | 2004 |
| Claim citation coverage | 0.958992 |
| Invalid citation rate | 0.309381 |
| Lexical support rate | 0.628542 |
| Weak support rate | 0.371458 |
| Mean claim support score | 0.568992 |

## Lessons for the New Protocol

1. High citation coverage does not imply valid attribution.
2. Citation-only prompting can increase citation count while still producing invalid or weak citations.
3. Ledger IDs alone are insufficient if the model can invent or transform them.
4. Deterministic validation must reject, sanitize, or count invalid IDs.
5. Semantic support must be evaluated separately from structural citation validity.

## Decision

The next implementation step is deterministic citation pointer validation plus a semantic claim-to-span evaluation layer. Lexical support rate may remain in diagnostics for triage, but it must not be used as a core metric.

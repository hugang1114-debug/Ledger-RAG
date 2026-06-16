# Gate 8 Corrected 6-Baseline Diagnosis

Source summary: `configs/gate8/main_v1_corrected_50x6x3_result_summary.yaml`

This diagnosis uses existing artifacts only. It made no new provider calls and does not inspect or track raw provider responses.

## Status

The corrected Gate 8 mini-main run is diagnostic evidence only. It should not be presented as paper-grade main comparison evidence and should not be scaled by sample size alone.

## Diagnostic Result Shape

| Item | Value |
|---|---:|
| Datasets | 3 |
| Baselines | 6 legacy diagnostic slots |
| Questions per dataset | 50 |
| Run records | 900 |
| Failure count | 0 |
| Estimated provider cost | $1.061699 |
| Overall support hit rate | 0.96 |
| Overall refusal rate | 0.154444 |
| Overall claim-to-citation rate | 0.990119 |

## Interpretation Under New Direction

1. The run is useful because it exposed citation attribution failure modes.
2. The run does not prove final answer accuracy improvement.
3. The run does not prove semantic faithfulness because its verifier fields are not paper-grade entailment judgments.
4. The `hybrid_rag` label is a legacy prompt-policy slot over lexical retrieval, not a true dense-plus-reranker baseline.
5. `claim_to_citation_rate` measures citation density, not citation validity or support.

## Methodology Risks

- Current validator fields are contract-shape metadata, not independent semantic verification.
- Current attribution checks mix citation shape, retrieval overlap, and lexical heuristics.
- `support_hit_rate` means any gold support document was retrieved. It is too weak for multi-hop sufficiency.
- Rates above 1 citation per claim do not imply better attribution.

## Decision

Do not treat this as final paper evidence. The next phase should implement deterministic pointer validation, semantic claim-to-span checking, and ledger-specific stress tests before any larger main comparison.

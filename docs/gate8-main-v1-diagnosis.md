# Gate 8 Corrected 6-Baseline Diagnosis

Source summary: `configs/gate8/main_v1_corrected_50x6x3_result_summary.yaml`

This diagnosis uses existing artifacts only. It made no new provider calls and does not inspect or track raw provider responses.

## Current Result Shape

| Item | Value |
|---|---:|
| Datasets | 3 |
| Baselines | 6 |
| Questions per dataset | 50 |
| Run records | 900 |
| Failure count | 0 |
| Estimated provider cost | $1.061699 |
| Overall support hit rate | 0.96 |
| Overall refusal rate | 0.154444 |
| Overall claim-to-citation rate | 0.990119 |

## Baseline View

| Baseline | Support hit rate | Refusal rate | Claim-to-citation rate | Cost |
|---|---:|---:|---:|---:|
| `vanilla_rag` | 0.96 | 0.146667 | 0.909091 | $0.176403 |
| `hybrid_rag` | 0.96 | 0.1 | 0.964602 | $0.176963 |
| `citation_only` | 0.96 | 0.146667 | 1.0 | $0.177423 |
| `validator_only` | 0.96 | 0.16 | 0.97929 | $0.175723 |
| `ledger_only` | 0.96 | 0.22 | 1.012085 | $0.177428 |
| `ledger_validator` | 0.96 | 0.153333 | 1.076923 | $0.177759 |

## Dataset View

| Dataset | top_k | Support hit rate | Refusal rate | Claim-to-citation rate | Cost |
|---|---:|---:|---:|---:|---:|
| `hotpotqa` | 8 | 0.9 | 0.116667 | 1.013997 | $0.30965 |
| `2wikimultihopqa` | 8 | 1.0 | 0.13 | 0.984456 | $0.303964 |
| `musique` | 16 | 0.98 | 0.216667 | 0.972085 | $0.448085 |

## Findings

1. Retrieval support hit rate is not a baseline differentiator yet. All six baselines use the same dataset-specific retrieval outputs, so the identical 0.96 support hit rate across baselines reflects shared retrieval, not model behavior.
2. `hybrid_rag` has the lowest refusal rate at 0.10, but this is only a prompt-policy slot over the current lexical index. It is not yet a true dense-plus-reranker Hybrid RAG baseline.
3. `ledger_only` has the highest refusal rate at 0.22. Ledger formatting alone appears to make the model more conservative in this run.
4. `ledger_validator` has the highest claim-to-citation rate at 1.076923. That is useful for citation density, but it does not prove faithfulness because multiple citations can point to weak or irrelevant evidence.
5. MuSiQue remains the hardest dataset after the `top_k=16` correction. It has the highest refusal rate at 0.216667 and the largest cost share.

## Methodology Risks

- The current validator fields are contract-shape metadata, not a paper-grade independent semantic verifier.
- The current attribution metric checks citation shape and retrieval overlap. It does not prove every cited span supports every atomic claim.
- `support_hit_rate` means any gold support document was retrieved. That is too weak for multi-hop sufficiency.
- `hybrid_rag` should not be reported as a true Hybrid RAG baseline until dense retrieval or reranking is implemented.

## Decision

Do not scale to a full run yet. The current run is useful as an engineering and diagnostic mini-main result, but the next step should be a no-API claim-to-citation faithfulness audit over existing artifacts.

Recommended next step: `gate8_claim_to_citation_audit`.

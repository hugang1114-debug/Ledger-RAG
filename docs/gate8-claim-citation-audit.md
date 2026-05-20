# Gate 8 Claim-to-Citation Audit

Source audit: `configs/gate8/main_v1_corrected_50x6x3_claim_citation_audit.yaml`

This audit uses existing run artifacts only. It made no API calls and does not track raw model answers.

## What Was Checked

The audit checks three attribution properties across the corrected 3 dataset x 6 baseline x 50 question run:

| Check | Meaning |
|---|---|
| Claim citation coverage | Whether each generated atomic claim has at least one citation |
| Invalid citation rate | Whether cited evidence ids actually exist in the retrieved evidence list |
| Lexical support rate | Whether claim keywords overlap enough with the cited evidence text |

The lexical support check is a conservative heuristic, not a semantic entailment verifier. It is useful for flagging weak citations, not for proving final attribution correctness.

## Overall Result

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

The important result is that citation coverage is high, but citation faithfulness is not locked. Roughly 96% of claims have citations, yet about 31% of citation references are invalid and about 37% of cited claims have weak lexical support.

## Baseline Diagnosis

| Baseline | Coverage | Invalid citation rate | Lexical support rate | Refusal rate |
|---|---:|---:|---:|---:|
| `vanilla_rag` | 0.885630 | 0.193548 | 0.751656 | 0.146667 |
| `hybrid_rag` | 0.943953 | 0.238532 | 0.709375 | 0.100000 |
| `citation_only` | 0.991098 | 0.560831 | 0.395210 | 0.146667 |
| `validator_only` | 0.937870 | 0.075529 | 0.854890 | 0.160000 |
| `ledger_only` | 1.000000 | 0.737313 | 0.223565 | 0.220000 |
| `ledger_validator` | 0.997041 | 0.057692 | 0.857567 | 0.153333 |

`ledger_validator` is the strongest current attribution variant: it has high claim citation coverage, the lowest invalid citation rate, and the highest lexical support rate. `validator_only` is close behind, which suggests verifier-style prompt pressure is doing more than ledger formatting alone.

`ledger_only` is the weakest current attribution variant despite perfect citation coverage. This means the model frequently outputs citation-shaped references that do not resolve to valid retrieved evidence ids or do not lexically support the claim. Ledger ids alone are not enough.

`citation_only` also shows a major failure mode: asking for citations increases coverage, but many citations are invalid or weak. This is exactly why the paper claim should focus on auditable evidence handling, not citation formatting alone.

## Dataset Diagnosis

| Dataset | Invalid citation rate | Lexical support rate | Refusal rate |
|---|---:|---:|---:|
| `hotpotqa` | 0.315951 | 0.594855 | 0.116667 |
| `2wikimultihopqa` | 0.382895 | 0.563014 | 0.130000 |
| `musique` | 0.207770 | 0.745331 | 0.216667 |

MuSiQue still has the highest refusal rate, but its cited claims have the best lexical support after the `top_k=16` correction. 2WikiMultihopQA has the worst invalid citation rate, so its output format and evidence id handling need inspection before scaling.

## Decision

Do not scale this run to full split yet. The next implementation step should fix attribution mechanics before spending on larger runs:

1. Force all citation ids to be selected from retrieved evidence ids.
2. Add a deterministic citation sanitizer or reject invalid citation ids before scoring.
3. Separate citation-format compliance from citation-faithfulness scoring.
4. Consider implementing a real verifier pass for `validator_only` and `ledger_validator`.
5. Keep `hybrid_rag` marked as a prompt-policy slot until dense retrieval or reranking exists.

The current mini-main result is still useful: it shows that Ledger + Validator is better than Ledger-only for attribution auditability. It does not yet prove paper-grade attribution correctness.

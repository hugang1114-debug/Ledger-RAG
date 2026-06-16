# Gate 8 Corrected Result Analysis

## Scope

This analysis uses the corrected first main-result view:

- HotpotQA: `top_k=8`
- 2WikiMultihopQA: `top_k=8`
- MuSiQue: `top_k=16`
- Baselines: `vanilla_rag`, `ledger_validator`
- Sample count: 50 questions per dataset
- Total records: 300

No new model calls were made for this analysis.

## Aggregate Result

| Metric | Value |
|---|---:|
| Records | 300 |
| Answered records | 255 |
| Refusal rate | 0.150000 |
| Support hit rate | 0.960000 |
| Claims | 679 |
| Citations | 674 |
| Claim-to-citation rate | 0.992636 |
| Claim citation coverage | 0.941090 |
| Invalid citation count | 81 |
| Invalid citation rate | 0.120178 |

## Dataset Summary

| Dataset | Records | Support hit | Refusal | Claim coverage | Invalid citation rate | Cost |
|---|---:|---:|---:|---:|---:|---:|
| HotpotQA | 100 | 0.90 | 0.07 | 0.955357 | 0.076596 | 0.104152 |
| 2WikiMultihopQA | 100 | 1.00 | 0.12 | 0.926923 | 0.192913 | 0.101323 |
| MuSiQue | 100 | 0.98 | 0.26 | 0.943590 | 0.075676 | 0.148690 |

## Baseline Summary

| Baseline | Records | Refusal | Claims | Citations | Claim coverage | Invalid citation rate | Cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| vanilla_rag | 150 | 0.146667 | 341 | 310 | 0.885630 | 0.193548 | 0.176403 |
| ledger_validator | 150 | 0.153333 | 338 | 364 | 0.997041 | 0.057692 | 0.177759 |

## Dataset By Baseline

| Dataset | Baseline | Refusal | Claim coverage | Invalid citation rate |
|---|---|---:|---:|---:|
| HotpotQA | vanilla_rag | 0.06 | 0.914286 | 0.117647 |
| HotpotQA | ledger_validator | 0.08 | 0.991597 | 0.045113 |
| 2WikiMultihopQA | vanilla_rag | 0.16 | 0.850394 | 0.311927 |
| 2WikiMultihopQA | ledger_validator | 0.08 | 1.000000 | 0.103448 |
| MuSiQue | vanilla_rag | 0.22 | 0.899083 | 0.141414 |
| MuSiQue | ledger_validator | 0.30 | 1.000000 | 0.000000 |

## Main Findings

The corrected run supports the current Ledger-RAG claim direction for attribution quality, not general answer quality. `ledger_validator` has nearly complete claim citation coverage at 0.997041, compared with 0.885630 for `vanilla_rag`. It also has much lower invalid citation rate at 0.057692, compared with 0.193548 for `vanilla_rag`.

The tradeoff is refusal behavior. Overall refusal is similar between baselines, but MuSiQue shows higher refusal for `ledger_validator` at 0.30 versus 0.22 for `vanilla_rag`. This is consistent with stricter evidence requirements: the ledger prompt is less willing to answer when support is incomplete or hard to combine.

2WikiMultihopQA is the clearest attribution-quality win. `ledger_validator` reduces invalid citation rate from 0.311927 to 0.103448 and improves claim citation coverage from 0.850394 to 1.000000.

MuSiQue still needs caution. Raising MuSiQue from `top_k=8` to `top_k=16` reduced refusal substantially, but refusal remains higher than HotpotQA and 2Wiki. The remaining failures are likely tied to multi-hop evidence composition and evidence position, not provider errors.

## Example Patterns

Common invalid citation patterns in `vanilla_rag`:

- Citation ids that append non-existent suffixes such as `_ledger`.
- Citation fields containing a serialized list of evidence ids rather than one stable evidence id.
- Empty citation ids for explanatory claims.

Cleaner `ledger_validator` pattern:

- Claims are more consistently mapped to existing evidence ids.
- Multi-source claims more often cite multiple stable source document ids.
- The model refuses slightly more often when the evidence is incomplete.

## Interpretation

The current evidence is useful for a paper claim about traceability and auditability. It should not be framed as proof that Ledger-RAG universally improves answer accuracy. The strongest defensible claim is that ledger-style prompting improves citation structure and auditability under the same model and source snapshots.

## Next Analysis Steps

1. Add a stricter attribution metric that treats invalid citation ids as unsupported.
2. Build a small qualitative table with representative vanilla citation failures and ledger improvements.
3. Add or implement the remaining baseline families before making full Gate 8 claims.

# Claim to Experiments Map

This file maps the attribution-protocol claim to experiment families. Future experiments should target one or more rows in this table.

| Claim component | Experiment family | Primary metrics | Required baselines | Failure interpretation |
|---|---|---|---|---|
| Citation pointer validity | Deterministic pointer validation | Invalid Citation Rate, Citation ID Validity Rate | Citation prompting only, Deterministic citation validator only, Ledger pointer + validator | If invalid IDs are not caught or counted, the audit layer is not enforcing citation validity. |
| Claim-level coverage | Claim-to-citation audit | Claim Citation Coverage, Refusal Precision | Vanilla RAG, Citation prompting only, Ledger pointer + validator | If claims remain uncited or refusals hide missing evidence, attribution coverage is not improved. |
| Semantic attribution | Claim-to-span entailment evaluation | Citation Precision / Entailment Support Rate, Overclaim Rate | Prompt-based verifier, Post-hoc NLI verifier, Ledger pointer + validator + semantic verifier | If structurally valid citations do not support claims, the protocol only improves citation form. |
| Replayability | Snapshot and span replay checks | Span Replay Success Rate, Snapshot Replay Success Rate | Ledger pointer only, Ledger pointer + validator | If cited spans cannot be reconstructed from recorded pointers and hashes, the system is not auditable. |
| Ledger stress behavior | Invalid-ID, re-chunking, drift, position, and conflict stress tests | Validation error categories, replay rates, Overclaim Rate | Citation prompting only, Ledger pointer + validator, Ledger pointer + validator + semantic verifier | If the ledger fails under controlled stress, larger runs should not proceed. |
| Training contribution | Later SFT/DPO ablation | Invalid Citation Rate, Overclaim Rate, Entailment Support Rate | Ledger pointer + deterministic validator, optional ledger-trained model | If training helps style but not validated correctness, it is not a substitute for deterministic enforcement. |
| Engineering cost | Audit profiling | Cost per audited claim, Latency per audited claim | All runnable families | If attribution gains require disproportionate cost or latency, the result must be framed as limited. |

## Gate Rule

No main experiment should be added unless it names the claim component it tests, the baseline family it compares against, the metric denominator, and the failure condition that would falsify the expected contribution.

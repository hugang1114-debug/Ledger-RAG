# Claim to Experiments Map

This file maps the first-version Ledger-RAG research claim to experiment families. It is a gate document: future experiments should target one or more rows in this table.

| Claim component | Experiment family | Primary metrics | Required baselines | Failure interpretation |
|---|---|---|---|---|
| evidence traceability | Claim-to-span attribution comparison | citation precision, citation recall, support rate, unsupported-claim rate, overclaim rate | Hybrid RAG, citation-only, Ledger-only, Ledger + Validator | If support rate and unsupported-claim rate do not improve, the ledger is not proving traceability value. |
| auditability | Replay and provenance checks | span replay success, source hash match rate, claim-to-span mapping completeness, verifier record completeness | Citation-only, Ledger-only, Ledger + Validator | If spans cannot be replayed or hashes do not match, the system is not auditable even if answers look plausible. |
| long-task stability | Context length and evidence-position stress tests | support rate by context length, support rate by evidence position, answer quality by context bucket | Vanilla RAG, Hybrid RAG, citation-only, Ledger + Validator | If performance degrades similarly when evidence moves to the middle or context grows, the architecture is not mitigating long-task instability. |
| retrieval isolation | Oracle retrieval and real retrieval comparison | Recall@k, answer quality, support rate under oracle vs real retrieval | Vanilla RAG, Hybrid RAG, Ledger + Validator with oracle evidence | If gains appear only with a better retriever, the experiment does not isolate ledger value. |
| verifier contribution | Ledger-only vs verifier-only vs full system ablation | support rate, unsupported-claim rate, false insufficient rate, refusal rate | Ledger-only, Validator-only, Ledger + Validator | If the full system is not better than either component alone, the architecture does not justify combining ledger and verifier. |
| robustness | Noise and conflicting-evidence stress tests | support rate under noise, overclaim rate, conflict handling rate, refusal rate | Hybrid RAG, citation-only, Ledger + Validator | If misleading spans cause unsupported claims at the same rate as baselines, the verifier and ledger controls are insufficient. |
| engineering cost | System profiling | p50 latency, p95 latency, cost/query, peak memory, ledger size, index size | Hybrid RAG, Ledger-only, Ledger + Validator | If reliability gains require disproportionate latency or cost, the result should be framed as impractical or niche. |

## Gate Rule

No main experiment should be added unless it names the claim component it tests, the baseline family it compares against, and the metric that would falsify the expected contribution.


# Metric Protocol

Gate 6 locks metric definitions before any baseline comparison is run. This gate does not authorize implementation code, dataset downloads, or model runs.

## Reporting Principles

Report metrics by group. Do not collapse retrieval, answer quality, attribution, and system cost into one score. Ledger-RAG's core claim is about traceability, auditability, long-task stability, and acceptable cost; average answer quality alone cannot support that claim.

All metrics must be computed on the same run records defined in `docs/baseline-contract.yaml`. If a metric cannot be computed for a baseline family, the output must record `not_applicable` or `not_available` with a reason. Missing values must not be silently dropped.

Refusals must be included in denominators unless a metric definition explicitly states otherwise. Report refusal rate next to support and answer-quality metrics so a method cannot improve support by refusing most questions.

## Retrieval Metrics

Use these when gold evidence, supporting facts, or oracle evidence ids are available.

| Metric | Definition | Applies to | Failure signal |
|---|---|---|---|
| Recall@k | Fraction of gold evidence items appearing in the top-k retrieved evidence list. | Vanilla RAG, Hybrid RAG, Citation-only, Validator-only, Ledger-only, Ledger + Validator | Low recall means downstream attribution failure may be retrieval failure, not ledger failure. |
| Precision@k | Fraction of top-k retrieved evidence items that match gold evidence. | All retrieval variants | Low precision increases noise and tests robustness of ledger/verifier controls. |
| MRR | Reciprocal rank of the first gold evidence item, averaged over questions. | Retrieval variants with ranked evidence | Low MRR indicates correct evidence is buried. |
| nDCG | Discounted ranking quality using graded or binary relevance labels. | Datasets with ranked or mapped evidence relevance | Low nDCG indicates poor evidence ordering even if recall is acceptable. |

Retrieval metrics must be reported separately for real retrieval and oracle retrieval diagnostics.

## Answer-Quality Metrics

Use exact-match and F1 for short-answer datasets. Use ROUGE-L only where the dataset or benchmark expects summary-style comparison. Use claim-level correctness when answers are decomposed into atomic claims. Use FActScore only when its dependencies, knowledge source, and cost are explicitly recorded.

| Metric | Definition | Applies to | Failure signal |
|---|---|---|---|
| EM | Exact normalized answer match. | Short-answer QA | Shows task accuracy but not evidence support. |
| F1 | Token-level answer overlap with gold answer. | Short-answer QA | Useful for QA comparability, insufficient for Ledger-RAG claim alone. |
| ROUGE-L | Longest common subsequence overlap. | Long-form or summarization-style answers | Weak factual proxy; must not be the only long-answer metric. |
| Claim-level correctness | Fraction of atomic claims judged correct against gold answer/evidence. | Claim-decomposed outputs | Separates answer content from citation support. |
| FActScore | Fraction of supported atomic facts under a fixed factuality evaluator. | Long-form answers where feasible | Requires evaluator/version/cost recording. |

If answer quality improves while attribution metrics do not improve, the result does not support the main Ledger-RAG claim.

## Attribution Metrics

Attribution metrics are the primary evidence for the research claim.

| Metric | Definition | Applies to | Failure signal |
|---|---|---|---|
| Citation precision | Fraction of cited evidence items that support the associated claim. | Citation-capable baselines | Low precision indicates citation laundering or weak citation grounding. |
| Citation recall | Fraction of claims requiring evidence that cite at least one supporting evidence item. | Citation-capable baselines | Low recall indicates unsupported or under-cited claims. |
| Support rate | Fraction of atomic claims labeled `support` by the verifier or gold attribution mapping. | Validator-capable and ledger variants | Main traceability indicator. |
| Unsupported-claim rate | Fraction of atomic claims labeled `insufficient`, `refute`, or uncited when citation is required. | All claim-decomposed variants | Core failure metric for evidence traceability. |
| Overclaim rate | Fraction of claims whose strength exceeds cited evidence support. | Verifier-capable variants | Captures citations that are relevant but too weak. |
| Claim-to-span mapping completeness | Fraction of atomic claims with at least one valid evidence or ledger span id. | Citation-only and ledger variants | Auditability failure if incomplete. |
| Span replay success | Fraction of cited ledger spans that can be replayed from recorded source metadata. | Ledger-only and Ledger + Validator | Auditability failure if spans cannot be replayed. |

For methods without ledger spans, replay metrics are `not_applicable`; citation mapping metrics still apply when evidence ids exist.

## System Metrics

System metrics define acceptable engineering cost.

| Metric | Definition | Applies to | Failure signal |
|---|---|---|---|
| p50 latency | Median end-to-end latency per question. | All baselines | Cost of practical use. |
| p95 latency | 95th percentile end-to-end latency per question. | All baselines | Tail latency risk. |
| Cost/query | Estimated model/API/GPU cost per question. | All baselines | Reliability gain may be impractical if cost dominates. |
| Peak memory | Maximum memory used during run. | Implemented systems | Identifies scaling limits. |
| Index size | Size of retrieval index. | Retrieval variants | Separates retriever footprint from ledger footprint. |
| Ledger size | Size of ledger storage for run/corpus. | Ledger variants | Measures auditability storage overhead. |

## Aggregation Rules

- Report macro averages across questions.
- Also report dataset-level results; do not pool datasets without per-dataset tables.
- Report confidence intervals or bootstrap intervals when sample size supports it.
- Report refusal rate next to answer and attribution metrics.
- Keep oracle retrieval diagnostics separate from main results.
- Keep long-context stress results separate from main multi-hop QA tables.

## Metric Gate Rule

A future experiment card is runnable only if it lists the metric groups it will compute, the denominator for each metric, and how missing or non-applicable values are recorded.


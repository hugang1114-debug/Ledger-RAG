# E026 Gate 8U Mini Run Output Review

## Status

Completed review card. This card authorizes artifact inspection only and does not authorize additional model calls.

## Purpose

Inspect Gate 8T HotpotQA mini-run outputs to decide whether to scale the experiment or fix the pipeline first.

## Reviewed Run

- Run id: `gate8t_hotpotqa_mini_run`
- Artifact path: `artifacts/gate8/main_v1/mini_run/latest`
- Dataset: `hotpotqa`
- Split: `dev_distractor`
- Baselines: `vanilla_rag`, `ledger_validator`
- Records reviewed: 20

## Review Result

- Support-document retrieval hit rate: 0.0
- Refusal rate: 0.9
- Estimated cost: 0.123398 USD
- Recommendation: `fix_retrieval_before_scaling`

## Interpretation

The first real mini run validated that API calls, artifact writing, and summary generation work. It also showed that the current global lexical retrieval setup is not usable for scaling: support documents were not retrieved for the reviewed HotpotQA examples, so most model outputs were evidence-driven refusals.

## Next Step

Fix retrieval before expanding sample size, datasets, or baseline count. A reasonable next gate is a HotpotQA retrieval repair pass that compares question-scoped context retrieval, BM25 normalization, and support-doc hit rate before any further DeepSeek runs.

# E027 Gate 8V HotpotQA Retrieval Fix

## Status

Completed retrieval repair card. This step does not authorize additional model calls.

## Problem

Gate 8U reviewed the first HotpotQA mini run and found support-document retrieval hit rate `0.0`. The retrieved evidence came from unrelated global-corpus documents, causing evidence-driven refusals.

## Fix

For the HotpotQA `dev_distractor` v1 pipeline, retrieval now ranks only within each question's `context_source_doc_ids`. This matches the HotpotQA distractor setting used by the local source snapshot and prevents global lexical term-frequency noise from dominating.

## Validation

- Dry-run artifact path: `artifacts/gate8/main_v1/mini_run/retrieval_fix_dry_run`
- Model calls: 0
- Questions: 10
- Baselines: `vanilla_rag`, `ledger_validator`
- Support-document retrieval hit rate after fix: `1.0`
- Refusal rate after dry-run: `0.0`

## Next Step

Rerun the Gate 8T HotpotQA mini run with the fixed retrieval path before increasing sample size, adding datasets, or adding more baselines.

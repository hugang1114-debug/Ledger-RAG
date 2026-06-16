# E028 Gate 8W Fixed HotpotQA Mini Run

## Status

Completed fixed-retrieval mini run. This is not a paper result.

## Purpose

Rerun the Gate 8T HotpotQA mini run after Gate 8V scoped retrieval to each question's HotpotQA distractor context.

## Run Scope

- Dataset: `hotpotqa`
- Split: `dev_distractor`
- Questions: first 10 in stable snapshot order
- Baselines: `vanilla_rag`, `ledger_validator`
- Provider/model: `deepseek / deepseek-v4-pro`
- Artifact path: `artifacts/gate8/main_v1/mini_run/fixed_latest`

## Result

- Attempted calls: 20
- Successful records: 19
- Provider failures: 1
- Support-document hit rate on reviewed records: 1.0
- Refusal rate on reviewed records: 0.0
- Estimated cost: 0.021141 USD

## Interpretation

The retrieval fix worked. The previous failure mode was global lexical retrieval selecting unrelated corpus documents. The remaining issue is provider reliability for one request, not retrieval.

## Next Step

Add bounded provider retry/resume handling, then rerun only the failed request or rerun the same 20-call mini run once more before increasing sample size.

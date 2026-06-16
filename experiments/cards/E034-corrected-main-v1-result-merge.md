# E034 Corrected Main v1 Result Merge

## Status

Completed.

## Purpose

Create a corrected first main-result summary without rerunning model calls. The merge keeps the valid HotpotQA and 2WikiMultihopQA runs and replaces only MuSiQue with the `top_k=16` calibration run.

## Inputs

- HotpotQA: `artifacts/gate8/main_v1/runs/deepseek_v4_pro_50x2x3/hotpotqa`
- 2WikiMultihopQA: `artifacts/gate8/main_v1/runs/deepseek_v4_pro_50x2x3/2wikimultihopqa`
- MuSiQue: `artifacts/gate8/main_v1/runs/musique_topk16_50x2/musique`

## Corrected Configuration

- HotpotQA: `top_k=8`
- 2WikiMultihopQA: `top_k=8`
- MuSiQue: `top_k=16`
- Baselines: `vanilla_rag`, `ledger_validator`
- Sample count: 50 questions per dataset

## Corrected Aggregate Result

- Total run records: 300
- Total failures: 0
- Overall support hit rate: 0.96
- Overall refusal rate: 0.15
- Overall claim-to-citation rate: 0.992636
- Estimated cost across reused runs: 0.354165 USD

## Interpretation

This corrected summary is the best current first main-result view. It is still not a full Gate 8 pass because only two of the six planned baseline families have run.

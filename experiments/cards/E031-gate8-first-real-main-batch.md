# E031 Gate 8 First Real Main Batch

## Status

Completed.

## Scope

- Datasets: `hotpotqa`, `2wikimultihopqa`, `musique`
- Sample count: 50 questions per dataset
- Baselines: `vanilla_rag`, `ledger_validator`
- Provider/model: `deepseek / deepseek-v4-pro`
- Output root: `artifacts/gate8/main_v1/runs/deepseek_v4_pro_50x2x3`

## Result

- Total provider calls: 300
- Successful records: 300
- Failed records: 0
- Estimated cost: 0.299049 USD

## Review Summary

- HotpotQA support hit rate: 0.9; refusal rate: 0.07
- 2WikiMultihopQA support hit rate: 1.0; refusal rate: 0.12
- MuSiQue support hit rate: 0.84; refusal rate: 0.49

## Interpretation

The first real batch completed without provider failures. MuSiQue has a high refusal rate, especially compared with the other datasets, so scaling should wait until refusal behavior is inspected.

This is a real experiment batch, but it is not the full Gate 8 paper comparison because only two baseline families ran.

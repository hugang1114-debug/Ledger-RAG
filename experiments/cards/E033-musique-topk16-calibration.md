# E033 MuSiQue top_k 16 Calibration

## Status

Completed.

## Purpose

Check whether MuSiQue's high refusal rate in the first real main batch was caused by an insufficient evidence budget.

## Scope

- Dataset: `musique`
- Split: `dev`
- Sample count: 50 questions
- Baselines: `vanilla_rag`, `ledger_validator`
- Provider/model: `deepseek / deepseek-v4-pro`
- Retrieval evidence budget: `top_k=16`
- Artifact path: `artifacts/gate8/main_v1/runs/musique_topk16_50x2/musique`

## Result

- Provider calls: 100
- Successful records: 100
- Failed records: 0
- Estimated cost: 0.14869 USD

## Comparison To top_k 8

- Any-support hit rate improved from 0.84 to 0.98.
- All-support hit rate improved from 0.24 to 0.76.
- Refusal rate dropped from 0.49 to 0.26.

## Interpretation

The high MuSiQue refusal rate was primarily caused by incomplete multi-hop evidence retrieval. `top_k=16` is a better default for the next MuSiQue main batch than `top_k=8`.

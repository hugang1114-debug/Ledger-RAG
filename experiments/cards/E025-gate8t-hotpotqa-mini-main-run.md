# E025 Gate 8T HotpotQA Mini Main Run

## Status

Runnable mini-run card. This card authorizes a bounded HotpotQA mini run with DeepSeek-V4-Pro.

## Purpose

Validate the first real main-v1 pipeline shape on locked local HotpotQA snapshot/index metadata with real DeepSeek model calls.

## Scope

- Dataset: `hotpotqa`
- Split: `dev_distractor`
- Sample count: first 10 questions in stable snapshot order
- Baselines: `vanilla_rag`, `ledger_validator`
- Provider/model: `deepseek / deepseek-v4-pro`
- Output path: `artifacts/gate8/main_v1/mini_run/latest`

## Execution Command

```powershell
python scripts/run_gate8t_hotpotqa_mini_run.py --sample-count 10 --baselines vanilla_rag ledger_validator --output artifacts/gate8/main_v1/mini_run/latest
```

## Failure Criteria

- Missing `DEEPSEEK_API_KEY`.
- Missing HotpotQA source snapshot or lexical index.
- More than two JSON parse failures.
- More than two provider/API failures.

## Non-Goals

- This is not a paper result.
- This does not pass full Gate 8.
- This does not run all three main-v1 datasets.
- This does not run all six baseline families.
- This does not add raw model artifacts to git.

## Expected Artifacts

- `run_records.jsonl`
- `metric_records.jsonl`
- `retrieval_records.jsonl`
- `request_manifest.jsonl`
- `cost_summary.json`
- `mini_run_summary.yaml`

Raw provider responses remain ignored under `artifacts/`.

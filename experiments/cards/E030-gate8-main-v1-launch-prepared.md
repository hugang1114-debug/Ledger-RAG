# E030 Gate 8 Main v1 Launch Prepared

## Status

Prepared. This card records the first real main batch command, but does not execute it.

## Scope

- Datasets: `hotpotqa`, `2wikimultihopqa`, `musique`
- Splits: locked `main_v1` source snapshots from `snapshots/main_v1/source_snapshots.json`
- Baselines: `vanilla_rag`, `ledger_validator`
- Provider/model: `deepseek / deepseek-v4-pro`
- Sample count: 50 questions per dataset
- Expected provider calls: 300
- Output root: `artifacts/gate8/main_v1/runs/deepseek_v4_pro_50x2x3`

## Command

```powershell
python scripts/run_gate8_main_v1_batch.py --sample-count 50 --baselines vanilla_rag ledger_validator --output-root artifacts/gate8/main_v1/runs/deepseek_v4_pro_50x2x3 --max-provider-attempts 3
```

## Resume Command

```powershell
python scripts/run_gate8_main_v1_batch.py --sample-count 50 --baselines vanilla_rag ledger_validator --output-root artifacts/gate8/main_v1/runs/deepseek_v4_pro_50x2x3_resume --resume-root artifacts/gate8/main_v1/runs/deepseek_v4_pro_50x2x3 --max-provider-attempts 3
```

## Interpretation

This is the first real main batch, not the final six-baseline paper comparison. The remaining baseline families still need implementation or explicit exclusion before claiming Gate 8 as fully passed.

## Verification Before Launch

The batch runner dry-run passed across all three datasets with one sample and two baselines.

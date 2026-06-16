# Gate 8 Snapshot Index Promotion

Gate 8J promotes source snapshot and lexical retrieval index metadata after local validation. It does not download datasets, rebuild indexes, evaluate retrieval quality, run baselines, call models, select a provider, freeze prompts, approve budget, create result artifacts, or pass Gate 8 by itself.

## What This Clears

Gate 8J clears stale dataset and index readiness blockers when all three `main_v1` datasets have:

- locked source snapshot metadata
- local dataset snapshot paths
- local lexical index manifests
- index manifests matching dataset id, split, source snapshot id, and processed corpus hash

The promotion is metadata-only. It may set snapshot records to `ready` and sync concrete dataset/index fields into `configs/gate8/main_v1_readiness.yaml`, but it does not authorize main comparison execution.

## Commands

Inspect promotion readiness:

```powershell
python scripts/check_gate8_snapshot_index_promotion.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
```

Promote validated metadata:

```powershell
python scripts/promote_gate8_snapshot_indexes.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
```

## Remaining Gate 8 Blockers

After promotion, Gate 8 still remains blocked by provider evidence, prompt and generation config freeze, cost budget approval, execution card, reproducibility review, baseline execution, and metric record generation.

# E015 Gate 8 Snapshot Index Promotion

## Purpose

Validate existing local source snapshot and lexical retrieval index metadata, then promote tracked snapshot/index readiness metadata.

## Execution Status

This is a metadata-only readiness card. It authorizes only local inspection and tracked metadata promotion.

## Authorized Commands

```powershell
python scripts/check_gate8_snapshot_index_promotion.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
python scripts/promote_gate8_snapshot_indexes.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
```

## Not Authorized

- dataset downloads
- index rebuilding
- retrieval evaluation
- baseline execution
- model calls
- embedding calls
- reranker calls
- provider or model selection
- live pricing checks
- prompt freeze
- budget approval
- result artifact creation

## Success Criteria

- snapshot/index promotion check reports promotable metadata
- snapshot records are promoted to `ready`
- `main_v1_readiness.yaml` contains concrete dataset and index metadata
- strict snapshot readiness passes
- strict freeze readiness still fails
- Gate 8 remains readiness in progress

## Cost Class

Local metadata validation and tracked metadata promotion only. No model, API, provider, cloud, dataset download, index rebuild, retrieval evaluation, baseline, metric, or result artifact cost is authorized.

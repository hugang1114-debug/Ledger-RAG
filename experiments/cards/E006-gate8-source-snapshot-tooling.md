# E006 Gate 8 Source Snapshot Tooling

## Status

Non-running readiness card. This card validates source snapshot metadata only. It does not authorize dataset downloads, retrieval index builds, model calls, or baseline execution.

## Research Question

Can the project make Gate 8 source snapshot blockers explicit and machine-checkable before real dataset snapshot work starts?

## Scope

This card covers pending registry entries for the `main_v1` datasets:

- HotpotQA
- 2WikiMultihopQA
- MuSiQue

The registry is `snapshots/main_v1/source_snapshots.json`. Records are allowed to remain pending because no dataset files are downloaded in this step.

## Command

Metadata check:

```powershell
python scripts/check_gate8_snapshot_readiness.py --registry snapshots/main_v1/source_snapshots.json
```

Strict execution gate:

```powershell
python scripts/check_gate8_snapshot_readiness.py --registry snapshots/main_v1/source_snapshots.json --require-ready
```

Strict mode is expected to exit nonzero until the snapshot, license, hash, build-command, and index fields are locked.

## Expected Cost Class

None. This step reads tracked metadata and uses Python standard library code only.

## Failure Criteria

This card fails if the checker writes files, downloads data, uses network access, treats pending snapshots as execution-ready, or reports Gate 8 as passed.

## Outputs

- `snapshots/main_v1/source_snapshots.json`
- `src/ledger_rag_snapshot/`
- `scripts/check_gate8_snapshot_readiness.py`

No result artifact is produced by this card.

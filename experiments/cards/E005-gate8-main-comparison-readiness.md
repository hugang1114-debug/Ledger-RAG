# E005 Gate 8 Main Comparison Readiness

## Status

Non-running readiness card. This card does not authorize dataset downloads, model calls, retrieval index builds, or baseline execution.

## Research Question

Can the project define the conditions required for a reproducible Gate 8 main comparison before any real baseline run is attempted?

## Scope

This readiness step covers the `main_v1` datasets selected in Gate 4:

- HotpotQA
- 2WikiMultihopQA
- MuSiQue

It also covers the six Gate 5 baseline families:

- Vanilla RAG
- Hybrid RAG
- Citation-only
- Validator-only
- Ledger-only
- Ledger + Validator

## Readiness Checks

Gate 8 execution remains unauthorized until:

- every dataset has a complete source snapshot record
- `source_snapshot_id`, raw data hash, processed corpus hash, split hash, and license note are recorded
- retrieval index build commands are recorded
- model/provider selection and prompt versions are frozen
- cost budget is approved from current official pricing
- metric groups from Gate 6 are mapped to executable metric configs
- artifact paths under ignored `artifacts/` are selected

## Command Authorization

No command is authorized by this card. A later execution card must name exact commands, configs, dataset snapshots, output paths, model/provider versions, and cost class.

## Expected Cost Class

None. This card creates documentation and config metadata only.

## Failure Criteria

This readiness gate fails if any document implies that Gate 8 has passed, if a main baseline run is launched without locked snapshots, or if a config selects a model/provider before source snapshots and budget approval are recorded.

## Outputs

- `docs/main-comparison-readiness.md`
- `docs/source-snapshot-protocol.md`
- `configs/gate8/main_v1_readiness.yaml`

No result artifact is produced by this card.

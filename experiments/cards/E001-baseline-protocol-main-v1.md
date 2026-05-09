# E001: Main v1 Baseline Protocol

## Research Question

Do the six baseline families produce comparable outputs under one shared run contract for the main v1 dataset shortlist?

## Gate

Gate 5: Baseline Protocol Locked.

## Dataset and License

Use the main v1 dataset decisions from `docs/dataset-decision-matrix.yaml`: HotpotQA, 2WikiMultihopQA, and MuSiQue. This card does not authorize downloads.

## Methods

Compare Vanilla RAG, Hybrid RAG, Citation-only, Validator-only, Ledger-only, and Ledger + Validator under the shared contract in `docs/baseline-contract.yaml`.

## Metrics

Metrics are not locked in this gate. Later Gate 6 must define retrieval, answer-quality, attribution, and system-cost metrics before this card can become runnable.

## Failure Criteria

The protocol fails if any baseline needs a different dataset split, evidence budget, answer schema, citation schema, or run metadata schema.

## Inputs

- `docs/baseline-protocol.md`
- `docs/baseline-contract.yaml`
- `docs/dataset-decision-matrix.yaml`

## Outputs

No run outputs are allowed in Gate 5.

## Command / Config

No command is authorized. This is a non-running protocol card.

## Cost Class

No compute cost.

## Reviewer Notes

This card becomes executable only after Gate 6 locks metrics and a later gate provides implementation code and dataset snapshots.


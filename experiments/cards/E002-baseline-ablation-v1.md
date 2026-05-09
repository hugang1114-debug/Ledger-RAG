# E002: Ledger and Verifier Ablation Protocol

## Research Question

How much of the Ledger-RAG effect is attributable to ledger persistence, semantic verification, and their combination?

## Gate

Gate 5: Baseline Protocol Locked.

## Dataset and License

Use only datasets approved by Gate 4. This card does not authorize downloads.

## Methods

Compare Citation-only, Validator-only, Ledger-only, and Ledger + Validator. Use Hybrid RAG as the retrieval-controlled reference where applicable.

## Metrics

Metrics are not locked in this gate. Gate 6 must define support rate, unsupported-claim rate, refusal rate, false insufficient rate, latency, and cost before execution.

## Failure Criteria

The ablation protocol fails if ledger and verifier variants do not share the same retrieved evidence, answer style, evidence budget, and output contract.

## Inputs

- `docs/claim-to-experiments.md`
- `docs/baseline-protocol.md`
- `docs/baseline-contract.yaml`

## Outputs

No run outputs are allowed in Gate 5.

## Command / Config

No command is authorized. This is a non-running protocol card.

## Cost Class

No compute cost.

## Reviewer Notes

The later runnable version must explicitly separate deterministic citation checks from semantic support judgments.


# E003: Main v1 Metric Protocol

## Research Question

Which retrieval, answer-quality, attribution, and system-cost metrics must every future main comparison report?

## Gate

Gate 6: Metric Protocol Locked.

## Dataset and License

Use only datasets approved by Gate 4. This card does not authorize downloads.

## Methods

Apply the metric groups in `docs/metric-protocol.md` to the baseline families defined in `docs/baseline-protocol.md`.

## Metrics

Required groups:

- retrieval: Recall@k, Precision@k, MRR, nDCG where gold evidence exists
- answer quality: EM, F1, ROUGE-L where appropriate, claim-level correctness, FActScore where feasible
- attribution: citation precision/recall, support rate, unsupported-claim rate, overclaim rate, mapping completeness, span replay success
- system: p50/p95 latency, cost/query, peak memory, index size, ledger size

## Failure Criteria

The metric protocol fails if answer quality is reported without attribution metrics, if refusals are omitted from denominators, or if oracle retrieval diagnostics are mixed into main results.

## Inputs

- `docs/baseline-contract.yaml`
- `docs/baseline-protocol.md`
- `docs/metric-contract.yaml`
- `docs/metric-protocol.md`

## Outputs

No metric output files are allowed in Gate 6.

## Command / Config

No command is authorized. This is a non-running metric protocol card.

## Cost Class

No compute cost.

## Reviewer Notes

The later runnable version must state denominators, missing-value handling, and aggregation level for every metric.


# E004: Gate 7 Offline Pilot

## Research Question

Can the project produce inspectable end-to-end artifacts for ingest, retrieval, ledger spans, rule-based claims, verification, and metrics without external datasets or model calls?

## Gate

Gate 7: Pilot Experiment Passed.

## Dataset and License

Use the tracked synthetic fixture at `fixtures/gate7_offline/pilot.json`. No external dataset download is authorized.

## Methods

Run the deterministic `ledger_validator` pilot:

- fixture ingest
- offline lexical retrieval
- rule-based answer generation from expected fixture claims
- rule-based support verification
- Gate 6 metric subset

## Metrics

The pilot writes `metric_record.json` using the sections from `docs/metric-contract.yaml`. Metrics validate artifact shape and deterministic computation only; they are not paper results.

## Failure Criteria

The pilot fails if any required artifact is missing, if output JSON lacks required contract sections, if answerable claims are not labeled `support`, or if insufficient cases are not labeled `insufficient`.

## Inputs

- `fixtures/gate7_offline/pilot.json`
- `docs/baseline-contract.yaml`
- `docs/metric-contract.yaml`

## Outputs

Generated files under ignored `artifacts/gate7/offline_pilot/latest/`:

- `run_record.json`
- `metric_record.json`
- `ledger.jsonl`
- `retrieval.jsonl`
- `claims.jsonl`
- `verdicts.jsonl`

## Command / Config

```powershell
python scripts/run_gate7_offline_pilot.py --fixture fixtures/gate7_offline/pilot.json --output artifacts/gate7/offline_pilot/latest
```

## Cost Class

No external compute cost. Python standard library only.

## Reviewer Notes

This pilot validates the pipeline shape. It must not be cited as evidence that Ledger-RAG improves research accuracy.


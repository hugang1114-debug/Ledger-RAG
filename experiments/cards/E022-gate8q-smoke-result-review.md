# E022 Gate 8Q Smoke Result Review

## Research Question

Can the Gate 8P DeepSeek smoke result be reviewed and summarized without committing raw provider output or secrets?

## Dataset And License Status

This card reviews the existing Gate 8P smoke artifacts generated from the tracked synthetic Gate 7 fixture. It does not download datasets.

## Method Variants And Baselines

No baseline comparison is run. The review inspects one `ledger_validator` smoke-run artifact set.

## Metrics

The tracked summary records:

- artifact file hashes
- artifact file sizes
- provider and model
- run id and question id
- estimated cost and budget ceiling
- token usage
- answer presence
- claim count
- citation count
- secret scan result
- pass/fail status

It does not record raw answer text or raw provider response content.

## Failure Criteria

- Any required artifact is missing.
- Estimated cost exceeds the 10 USD smoke budget ceiling.
- Answer, atomic claim, or citation is missing.
- A secret-like pattern is found in reviewed artifacts.
- Full Gate 8 execution is implied to be authorized.
- Raw provider response content is added to tracked metadata.

## Command

```powershell
python scripts/review_gate8p_smoke_result.py --artifact-dir artifacts/gate8/smoke/deepseek/latest --summary configs/gate8/deepseek_smoke_result_summary.yaml --write-summary --require-pass
```

## Output Paths

- Tracked summary: `configs/gate8/deepseek_smoke_result_summary.yaml`
- Ignored raw artifacts: `artifacts/gate8/smoke/deepseek/latest/`

## Expected Cost Class

Zero. This card reviews existing artifacts and does not call an external provider.

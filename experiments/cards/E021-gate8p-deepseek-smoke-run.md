# E021 Gate 8P DeepSeek Smoke Run

## Research Question

Can the project perform one authorized DeepSeek-V4-Pro smoke call and write contract-shaped artifacts without unlocking the full Gate 8 main comparison?

## Dataset And License Status

This card uses the tracked synthetic Gate 7 fixture at `fixtures/gate7_offline/pilot.json`. It does not download external datasets and does not use main-v1 benchmark data.

## Method Variants And Baselines

This smoke run uses only `ledger_validator` artifact shape. It does not compare baseline families.

Provider:

- `deepseek_v4_pro`

Question:

- `q_traceability`

## Metrics

The metric record reports smoke-level shape and system fields only. It is not a research result and does not support the paper claim.

## Failure Criteria

- `DEEPSEEK_API_KEY` is missing from local environment or `.env.local`.
- The request cannot be sent to DeepSeek.
- The response cannot be parsed as JSON.
- Required artifact files are missing.
- `run_record.json` or `metric_record.json` lacks required top-level contract sections.
- Any API key appears in tracked files or committed artifacts.
- Full Gate 8 execution is accidentally authorized.

## Commands

Dry-run:

```powershell
python scripts/run_gate8p_deepseek_smoke.py --fixture fixtures/gate7_offline/pilot.json --output artifacts/gate8/smoke/deepseek/dry_run --question-id q_traceability --dry-run
```

Real smoke run:

```powershell
python scripts/run_gate8p_deepseek_smoke.py --fixture fixtures/gate7_offline/pilot.json --output artifacts/gate8/smoke/deepseek/latest --question-id q_traceability
```

## Output Paths

- `artifacts/gate8/smoke/deepseek/latest/request.json`
- `artifacts/gate8/smoke/deepseek/latest/response.json`
- `artifacts/gate8/smoke/deepseek/latest/run_record.json`
- `artifacts/gate8/smoke/deepseek/latest/metric_record.json`
- `artifacts/gate8/smoke/deepseek/latest/cost_estimate.json`

## Expected Cost Class

Tiny. The run is one question, capped under the Gate 8O 10 USD smoke budget.

# E020 Gate 8O DeepSeek Smoke Run Authorization

## Research Question

Can the project safely authorize a small DeepSeek-V4-Pro smoke run without unlocking the full Gate 8 main comparison?

## Dataset And License Status

No dataset files are downloaded or processed in this card. The future smoke run must use the locked main-v1 source snapshots and local retrieval indexes already recorded in Gate 8 readiness metadata.

## Method Variants And Baselines

This card authorizes only the provider and budget scope for a future smoke run. It does not compare baseline families.

Authorized provider:

- `deepseek_v4_pro`

Authorized scope:

- one smoke run only
- budget ceiling: 10 USD
- API key source: local environment or `.env.local`

Not authorized:

- main comparison runs
- GPT-5.4 calls
- cross-provider comparisons
- training or fine-tuning

## Metrics

No metrics are produced by this card. The future smoke run must produce contract-shaped run and metric records before any research claim is made.

## Failure Criteria

- The selected provider is not `deepseek_v4_pro`.
- The smoke budget is not explicitly approved.
- The checker reports `smoke_run_authorized: false`.
- Full execution is accidentally authorized.
- Any API key or secret is added to tracked files.

## Command

```powershell
python scripts/check_gate8_provider_budget_preflight.py --provider-candidates configs/gate8/provider_candidates.yaml --budget-preflight configs/gate8/budget_preflight.yaml --require-smoke-authorized
```

## Output Paths

No run artifacts are created by this card.

## Expected Cost Class

Zero for this authorization card. The later smoke run is capped at 10 USD unless a later card changes the budget.

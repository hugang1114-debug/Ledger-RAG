# E019 Gate 8N Select DeepSeek Primary Provider

## Status

Non-running readiness card. This card does not authorize API calls, API key checks, model output generation, dataset downloads, baseline runs, or result artifacts.

## Purpose

Record DeepSeek-V4-Pro as the primary provider for the first smoke run and likely main-v1 run while keeping execution blocked.

## Scope

- Primary provider: DeepSeek-V4-Pro
- Optional credibility-check provider: GPT-5.4
- Smoke budget ceiling: 10 USD
- Execution authorization: false

## Commands

Inspect-only:

```powershell
python scripts/check_gate8_provider_budget_preflight.py --provider-candidates configs/gate8/provider_candidates.yaml --budget-preflight configs/gate8/budget_preflight.yaml
```

Strict execution readiness, expected to fail:

```powershell
python scripts/check_gate8_provider_budget_preflight.py --provider-candidates configs/gate8/provider_candidates.yaml --budget-preflight configs/gate8/budget_preflight.yaml --require-ready
```

## Failure Criteria

- DeepSeek-V4-Pro is not the selected provider.
- More than one provider is final-selected.
- Any provider is marked authorized to run.
- Strict mode succeeds before explicit smoke-run authorization.

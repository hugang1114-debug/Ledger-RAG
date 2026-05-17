# E018 Gate 8M Provider Budget Preflight

## Status

Non-running readiness card. This card does not authorize API calls, model output generation, dataset downloads, baseline runs, or result artifacts.

## Purpose

Validate that GPT-5.4 and DeepSeek-V4-Pro provider candidates plus the initial smoke-run budget are recorded before a later execution gate.

## Scope

- Provider candidates: OpenAI GPT-5.4 and DeepSeek-V4-Pro
- Smoke budget: 10 USD
- Main budget: requires later approval
- Selected provider: unset
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

- Either provider candidate is missing.
- Any candidate is marked authorized to run.
- Smoke budget is missing or nonpositive.
- Budget include/exclude scope is empty.
- Strict mode succeeds before explicit execution authorization.


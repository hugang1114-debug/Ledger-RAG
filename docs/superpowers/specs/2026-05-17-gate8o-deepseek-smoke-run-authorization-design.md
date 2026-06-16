# Gate 8O DeepSeek Smoke Run Authorization Design

## Purpose

Gate 8O authorizes only the first DeepSeek-V4-Pro smoke run. It does not authorize the main comparison, does not execute model calls, does not create run artifacts, and does not pass Gate 8.

The goal is to remove the `smoke_run_not_yet_authorized` blocker while keeping full execution blocked until the smoke run command, API runtime, pricing recheck, and output artifacts are handled in a later gate.

## Scope

In scope:

- Record `deepseek_v4_pro` smoke-run authorization in tracked metadata.
- Keep the smoke budget ceiling at 10 USD.
- Require `DEEPSEEK_API_KEY` to be supplied from local environment or `.env.local`, never from tracked files.
- Add checker output for `smoke_run_authorized`.
- Add a CLI mode that succeeds only when smoke authorization is present.
- Preserve `execution_authorized: false` for main comparison execution.

Out of scope:

- Running the smoke run.
- Calling DeepSeek or any other provider.
- Authorizing all six-baseline main comparison runs.
- Committing secrets, raw outputs, or result artifacts.

## Design

`configs/gate8/provider_candidates.yaml` becomes the provider-side authorization record for the smoke run. It keeps `authorized_to_run: false` and `execution_authorized: false`, but records `smoke_run_authorized: true`, `smoke_run_scope: deepseek_v4_pro_smoke_only`, and the required environment variable name.

`configs/gate8/budget_preflight.yaml` becomes the budget-side authorization record for the smoke run. It keeps `main_run_budget_usd: unset_requires_later_approval` and `budget_owner_approval: pending`, but records `smoke_budget_owner_approval: approved_for_smoke_run`.

The provider/budget checker reports:

- `provider_budget_preflight_ready`
- `smoke_run_authorized`
- `execution_authorized`
- `smoke_authorization_blockers`
- `execution_blockers`

Strict full readiness still fails until main execution is authorized. The new smoke authorization mode can pass before full Gate 8 execution is ready.

## Validation

The tests verify that:

- DeepSeek remains the selected provider.
- The smoke budget is approved for smoke only.
- The smoke checker mode exits zero.
- Full `--require-ready` still exits nonzero.
- Changing the selected provider or smoke budget approval blocks smoke authorization.

## Reality Notes

DeepSeek prices and model limits are treated as run-date facts. The tracked metadata records the latest known official pricing source, but the actual smoke run must recheck official pricing before spending budget.

# Gate 8N Select DeepSeek Primary Provider Design

## Purpose

Gate 8N selects DeepSeek-V4-Pro as the primary provider for the first smoke run and likely main-v1 run. It does not authorize API calls, check API keys, run baselines, generate model outputs, or pass Gate 8.

The goal is to replace the Gate 8M `selected_provider: unset` state with an explicit primary provider decision while keeping execution blocked until a later smoke-run authorization gate.

## Recommended Approach

Promote DeepSeek-V4-Pro from candidate to primary provider in the existing Gate 8M preflight metadata.

This means:

- `deepseek_v4_pro` becomes `final_selected: true`.
- `openai_gpt_5_4` remains `final_selected: false`.
- `selected_provider: deepseek_v4_pro`.
- `execution_authorized: false`.
- `authorized_to_run: false`.
- GPT-5.4 remains an optional credibility-check candidate, not a required main-run provider.

This is narrower than creating a new provider subsystem and safer than jumping to execution authorization.

Rejected alternatives:

- Run DeepSeek immediately: unsafe because API key/runtime, live pricing, and smoke-run command scope are not locked.
- Remove GPT-5.4 entirely: unnecessary because it remains useful as optional small-sample external validity evidence.
- Select both providers: invalid for main comparison because all six baseline families need one primary provider for comparable first-run results.

## Scope

In scope:

- Update provider candidate metadata to mark DeepSeek-V4-Pro as primary selected.
- Keep OpenAI GPT-5.4 as optional credibility-check candidate.
- Update budget/preflight checker semantics so primary-provider selection can pass while execution remains blocked.
- Add tests for exactly one selected provider.
- Add tests that selected provider must be one of the tracked candidates.
- Update docs and readiness matrix to show DeepSeek selected.
- Add non-running card `experiments/cards/E019-gate8n-select-deepseek-primary-provider.md`.

Out of scope:

- No API calls.
- No API key lookup.
- No provider SDK setup.
- No smoke-run execution.
- No model output generation.
- No budget spend.
- No final Gate 8 pass.

## Provider Decision Semantics

After Gate 8N, provider preflight default output should be:

```json
{
  "provider_budget_preflight_ready": true,
  "execution_authorized": false,
  "selected_provider": "deepseek_v4_pro"
}
```

Strict mode must still exit nonzero because `execution_authorized` remains false.

The checker should enforce:

- exactly one provider candidate has `final_selected: true`
- selected provider equals that selected candidate id
- selected provider is `deepseek_v4_pro`
- selected candidate remains `authorized_to_run: false`
- budget remains non-executable

## Budget Semantics

The smoke budget remains 10 USD. It is a planned ceiling, not authorization to spend.

The main budget remains unset and requires later approval.

The later smoke-run authorization gate must still confirm:

- API key/runtime availability
- run-date DeepSeek pricing
- run-date DeepSeek model limits
- terms/data policy status
- exact sample size
- exact command and output path
- explicit permission to spend up to the smoke budget

## Documentation Requirements

Update provider comparison docs to state:

- DeepSeek-V4-Pro is now the primary provider for smoke and likely main-v1 runs.
- GPT-5.4 is optional credibility-check evidence, not part of the required first main run.
- Results must be reported as DeepSeek-conditioned unless later cross-provider checks are run.
- Same provider must be used across all six baseline families for the first comparable run.

## Testing

Tests should cover:

- selected provider is `deepseek_v4_pro`
- exactly one candidate is final-selected
- no candidate is authorized to run
- default checker exits zero and reports preflight ready
- strict checker exits nonzero because execution remains blocked
- invalid selected provider fails readiness
- multiple final-selected candidates fail readiness
- marker scan finds no unresolved markers or internal report links

## Success Criteria

Gate 8N is complete when:

- DeepSeek-V4-Pro is selected as primary provider in tracked metadata
- OpenAI GPT-5.4 remains optional credibility-check candidate
- provider/budget preflight remains ready
- execution remains unauthorized
- strict mode still fails
- tests pass
- no API calls or result artifacts are produced
- changes are committed with a focused message


# Gate 8M Provider Budget Preflight Design

## Purpose

Gate 8M locks the preflight layer for choosing between OpenAI GPT-5.4 and DeepSeek-V4-Pro before any paid main experiment runs. It does not call provider APIs, run baselines, approve execution, or pass Gate 8.

The goal is to make provider choice and budget scope explicit enough that the next run gate can safely decide whether to execute a smoke run.

## Recommended Approach

Use a dual-candidate provider registry plus a separate budget preflight config.

The provider registry records both candidates as non-executable options:

- `openai_gpt_5_4`
- `deepseek_v4_pro`

The budget config records what counts toward experiment spend, the smoke-run budget ceiling, the main-run budget ceiling, retry buffer assumptions, and whether execution is authorized. This keeps model choice, budget, and run authorization separate.

Rejected alternatives:

- Replace OpenAI candidate with DeepSeek immediately: too early, because DeepSeek needs official evidence locking and smoke-run stability checks.
- Keep only OpenAI GPT-5.4: more expensive and less useful for cost-controlled smoke runs.
- Approve main execution in this gate: unsafe, because provider runtime availability, API key environment, final pricing check, and execution card review are still unresolved.

## Scope

In scope:

- Add `docs/gate8-provider-comparison.md`.
- Add `configs/gate8/provider_candidates.yaml`.
- Add `configs/gate8/budget_preflight.yaml`.
- Add a stdlib-only checker at `scripts/check_gate8_provider_budget_preflight.py`.
- Add supporting module code under `src/ledger_rag_gate8/` if needed.
- Add tests for provider candidate shape, budget scope, and non-execution authorization.
- Add non-running card `experiments/cards/E018-gate8m-provider-budget-preflight.md`.
- Update `README.md` and `configs/gate8/main_v1_readiness.yaml`.

Out of scope:

- No API calls.
- No API key checks.
- No model output generation.
- No baseline runs.
- No cost-incurring request.
- No provider final selection.
- No Gate 8 pass.

## Provider Candidate Semantics

Both providers are candidates, not executable decisions.

Each provider candidate record should include:

- `id`
- `provider`
- `model`
- `candidate_locked`
- `final_selected`
- `authorized_to_run`
- `official_model_url`
- `official_pricing_url`
- `pricing_checked_at`
- `input_usd_per_1m_tokens`
- `cached_input_usd_per_1m_tokens`
- `output_usd_per_1m_tokens`
- `context_window_note`
- `max_output_note`
- `json_output_support`
- `tool_call_support`
- `terms_or_data_policy_note`
- `risk_notes`
- `recommended_role`

Expected candidate roles:

- OpenAI GPT-5.4: high-trust small-sample comparison and later credibility check.
- DeepSeek-V4-Pro: first smoke-run and likely cost-controlled main-run candidate if JSON/citation behavior is stable.

## Budget Semantics

Budget preflight should distinguish smoke-run budget from main-run budget.

Recommended initial values:

- `smoke_run_budget_usd: 10`
- `main_run_budget_usd: unset_requires_later_approval`
- `retry_buffer_fraction: 0.30`
- `authorized_to_run: false`

Budget includes:

- generator input tokens
- generator output tokens
- verifier input tokens
- verifier output tokens
- repeated calls across six baseline families
- retry and JSON repair calls
- provider tool costs if later enabled

Budget excludes:

- local lexical retrieval index construction
- local dataset source snapshots
- local result storage
- literature PDFs and project docs
- ignored local caches

## Readiness Semantics

The new checker should report two layers:

- `provider_budget_preflight_ready`: true when both candidates and budget scope are valid.
- `execution_authorized`: false until an explicit later run gate authorizes model calls.

After Gate 8M, expected default output:

```json
{
  "provider_budget_preflight_ready": true,
  "execution_authorized": false,
  "selected_provider": "unset"
}
```

Strict mode should still exit nonzero while `execution_authorized` is false or `selected_provider` is unset.

Preflight readiness must fail if:

- either candidate is missing
- a candidate is marked `authorized_to_run: true`
- more than one candidate is marked final selected
- any official source URL is missing
- any required price field is missing or nonnumeric where a price is expected
- smoke-run budget is missing or not positive
- budget includes/excludes are empty
- execution is authorized in this gate

## Documentation Requirements

`docs/gate8-provider-comparison.md` should explain:

- GPT-5.4 is the stronger, more expensive credibility candidate.
- DeepSeek-V4-Pro is the cheaper smoke/main candidate pending behavior checks.
- The project claim is about Ledger-RAG traceability and auditability, not proving one provider is best.
- Provider choice affects external validity and must be reported with all results.

The doc should cite official source URLs in metadata fields and state that pricing must be rechecked on the actual run date.

## Testing

Tests should cover:

- provider candidates file contains exactly `openai_gpt_5_4` and `deepseek_v4_pro`
- both candidates are candidate-locked but not final-selected and not authorized
- budget preflight has a positive smoke budget and unset main budget
- checker default mode exits zero and reports preflight ready
- checker strict mode exits nonzero because execution is unauthorized
- accidental authorization fails candidate readiness
- marker scan finds no unresolved markers or internal report links

## Success Criteria

Gate 8M is complete when:

- provider candidates and budget preflight metadata are tracked
- checker reports provider/budget preflight ready
- strict execution check still fails
- no API calls or result artifacts are produced
- tests pass
- changes are committed with a focused message


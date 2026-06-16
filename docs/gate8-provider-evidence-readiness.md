# Gate 8 Provider Evidence Readiness

Gate 8 provider evidence readiness records which provider/model is supported by official sources, local runtime evidence, and budget notes before any main baseline execution can be authorized.

This remains a non-executable readiness state. It does not authorize main baseline runs, full budget spend, prompt/config freeze, model calls, embedding calls, reranker calls, metric computation, or Gate 8 passage.

## Current State

Gate 8R locks provider evidence for:

- `provider: deepseek`
- `model: deepseek-v4-pro`
- `provider_evidence_locked: true`
- `provider_selected: true`
- `authorized_to_run: false`

The lock uses the Gate 8N provider selection, Gate 8O smoke-only authorization, Gate 8P one-question smoke run, and Gate 8Q reviewed smoke summary. The raw smoke response remains ignored under `artifacts/`; the tracked evidence is the hash/cost summary in `configs/gate8/deepseek_smoke_result_summary.yaml`.

## Readiness Semantics

The checker now distinguishes two states:

- `provider_evidence_locked_ready`: provider/model evidence is locked and internally consistent.
- `provider_evidence_ready`: strict execution readiness for provider evidence.

After Gate 8R, `provider_evidence_locked_ready` is expected to be `true`, while strict `provider_evidence_ready` remains `false` because `authorized_to_run` and `run_authorized` remain false.

## Evidence Slots

The locked DeepSeek registry keeps all required slots reviewed:

- `official_pricing_source`
- `official_model_docs_source`
- `official_terms_privacy_source`
- `model_id_version_source`
- `context_window_source`
- `output_limit_source`
- `rate_limit_or_throughput_source`
- `api_key_or_runtime_availability_note`
- `cost_budget_approval_note`

Official model and pricing evidence points to the DeepSeek pricing/model page. Runtime and smoke budget evidence points to the tracked Gate 8Q smoke summary, not to raw artifacts or secrets.

## CLI Contract

Inspect-only mode:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --provider-decision configs/gate8/provider_decision.yaml
```

Strict execution mode:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --provider-decision configs/gate8/provider_decision.yaml --require-ready
```

Strict mode is expected to fail until main-run pricing is rechecked, main budget is approved, prompts/configs are frozen, and a main execution card authorizes baseline runs.

## Execution Boundary

Gate 8R locks provider evidence only. It does not approve the main comparison budget or authorize additional provider calls.

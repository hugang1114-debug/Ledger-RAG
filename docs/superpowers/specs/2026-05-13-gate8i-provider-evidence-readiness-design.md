# Gate 8I Provider Evidence Readiness Design

## Purpose

Gate 8I adds a provider-evidence scaffold for the future Gate 8 main comparison. It defines which official provider evidence must be recorded before a provider/model can be selected and before main baseline execution can be authorized.

This gate remains a readiness gate. It does not choose a provider, choose a model, check live prices, claim pricing, store API keys, call models, run baselines, compute metrics, create result artifacts, or pass Gate 8.

## Recommended Approach

Use a tracked provider evidence registry plus a standard-library-only validator.

The registry should define required evidence slots without filling them:

- official pricing source
- official model documentation source
- official terms, data retention, or privacy source
- model id and version source
- context window source
- output limit source
- rate-limit or throughput source
- API key or local runtime availability note
- cost budget approval note

Default checker mode should exit `0` and report missing evidence. Strict mode should exit nonzero until every evidence slot is filled, reviewed, and linked to the provider decision metadata.

## Alternatives Considered

1. Run provider shortlist research now.

This would require browsing official provider documentation and pricing. It may be useful later, but it would create time-sensitive evidence before budget and execution timing are settled.

2. Select a provider and model now.

This is premature because provider choice depends on run budget, API/runtime availability, model documentation checked on the execution date, and prompt/config freeze state.

## Scope

In scope:

- create a tracked provider evidence registry with required official-source evidence slots
- create a local readiness checker for evidence coverage and lockout state
- update provider decision metadata to reference the evidence registry
- update freeze readiness to block while provider evidence is incomplete
- add tests for missing evidence, strict mode, and non-selection behavior
- update docs and experiment card references

Out of scope:

- live provider documentation lookup
- live pricing lookup
- provider/model selection
- API key storage
- cost budget approval
- model calls
- embedding calls
- reranker calls
- baseline execution
- metric computation
- result artifact creation
- source snapshot status promotion
- prompt finalization

## Provider Evidence Registry

Create `configs/gate8/provider_evidence_registry.yaml`.

The registry should include:

- `gate`
- `stage`
- `status`
- `authorized_to_run: false`
- `provider_evidence_locked: false`
- `provider_selected: false`
- `provider: unset`
- `model: unset`
- `evidence_slots`
- `blockers`

Each evidence slot should include:

- `evidence_id`
- `required_for`
- `official_source_url`
- `checked_at`
- `evidence_status`
- `reviewer`
- `notes`

All source URLs, check timestamps, reviewer fields, and final provider/model fields should remain unset in this gate.

## Validator

Create a standard-library-only validator that reads the provider evidence registry and reports:

- `provider_evidence_ready`
- `authorized_to_run`
- `provider_selected`
- `provider`
- `model`
- `missing_evidence_ids`
- `unreviewed_evidence_ids`
- `blockers`
- `checked_configs`
- `validation_errors`

Default mode exits `0` and prints JSON. Strict mode exits nonzero while any evidence slot is missing, unreviewed, or while provider/model selection remains unset.

The checker should not browse, fetch URLs, write files, or validate prices. It only checks tracked metadata shape and lockout state.

## Provider Decision Integration

Gate 8I should update `configs/gate8/provider_decision.yaml` to reference `configs/gate8/provider_evidence_registry.yaml`.

Provider decision metadata should remain:

- `selected: false`
- `provider: unset`
- `model: unset`
- `run_authorized: false`

The provider decision record should continue to require official pricing/model docs checked on the run date. Gate 8I adds the evidence registry reference but does not satisfy those requirements.

## Freeze Integration

Gate 8G freeze readiness should be able to reference the provider evidence registry. Freeze readiness should remain blocked while:

- provider evidence is not locked
- provider is not selected
- model is not selected
- live pricing and model documentation are not checked on the run date
- cost budget is not approved
- prompt/config registries remain locked out

Gate 8I should not make freeze readiness pass.

## Tests

Tests should cover:

- provider evidence registry exists and loads
- required evidence slots are present
- default provider evidence readiness reports not ready
- strict provider evidence readiness exits nonzero
- missing evidence slots produce blockers
- provider decision remains unselected after integration
- freeze readiness remains not ready after provider evidence registry references are added

## Success Criteria

Gate 8I is complete when:

- provider evidence registry exists
- provider evidence checker exists
- provider decision references the evidence registry
- freeze readiness references the evidence registry
- tests pass
- docs and experiment card exist
- README and Gate 8 readiness docs reference the evidence registry and checker
- placeholder and report-link scan returns no matches
- strict provider evidence readiness exits nonzero
- strict freeze readiness exits nonzero
- no provider, model, price, API key, final prompt, dataset, index, model call, or result artifact is created

## Implementation Boundary

The next implementation should be committed separately from this design. It must preserve Gate 8 readiness status and all execution lockouts.

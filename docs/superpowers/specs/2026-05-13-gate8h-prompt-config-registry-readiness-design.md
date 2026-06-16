# Gate 8H Prompt Config Registry Readiness Design

## Purpose

Gate 8H adds prompt and generation-config registry readiness for the future Gate 8 main comparison. It ensures every Gate 5 baseline family has an explicit prompt slot and generation config slot before any provider/model run can be authorized.

This gate remains a readiness gate. It does not write final prompt text, select a provider, check live prices, call models, run baselines, compute metrics, create result artifacts, or pass Gate 8.

## Recommended Approach

Use tracked YAML metadata plus a small standard-library-only validator.

The registries define the shape of prompt/config coverage without freezing final content:

- `configs/gate8/prompt_registry.yaml`
- `configs/gate8/generation_config_registry.yaml`

The checker confirms all six baseline families are represented and reports lockout blockers while prompt/config versions remain unfrozen.

## Alternatives Considered

1. Write final prompt templates now.

This is too early because provider/model behavior, context window, and cost budget are not locked. Final prompt text should be frozen after provider selection and before real execution.

2. Select provider/model first.

This would require checking official documentation and pricing on the execution date. It is not necessary to define prompt/config registry shape.

## Scope

In scope:

- add a tracked prompt registry with one slot for each Gate 5 baseline family
- add a tracked generation config registry with shared config slots and one baseline mapping per family
- add a local CLI that checks registry coverage and lockout status
- add tests for baseline coverage, missing-family detection, and CLI strict mode
- update Gate 8 readiness docs and freeze readiness references
- keep all prompt/config entries unfinalized and unauthorized

Out of scope:

- final prompt text
- provider/model selection
- official pricing checks
- API key storage
- baseline execution
- metric computation
- result artifact creation
- source snapshot status promotion
- retrieval index rebuilds

## Registry Shape

The prompt registry should include:

- `gate`
- `stage`
- `status`
- `authorized_to_run: false`
- `prompt_versions_locked: false`
- `baseline_prompt_slots`

Each prompt slot should include:

- `baseline_family`
- `prompt_version`
- `prompt_status`
- `prompt_file`
- `requires_provider_freeze`
- `notes`

The generation config registry should include:

- `gate`
- `stage`
- `status`
- `authorized_to_run: false`
- `generation_config_locked: false`
- `shared_constraints`
- `baseline_generation_slots`

Each generation config slot should include:

- `baseline_family`
- `generation_config_version`
- `config_status`
- `requires_provider_freeze`
- `notes`

All slot statuses should remain locked out with values such as `slot_reserved`, `unset`, or `required_later`.

## Validator

Create a standard-library-only validator that reads the two registries and reports:

- `prompt_config_ready`
- `authorized_to_run`
- `baseline_families`
- `missing_prompt_families`
- `missing_generation_families`
- `blockers`
- `checked_configs`
- `validation_errors`

Default mode exits `0` and prints JSON. Strict mode exits nonzero while any blocker remains.

The validator should not parse full YAML. It can use a narrow parser that supports the registry shape controlled by this project.

## Freeze Integration

Gate 8G freeze readiness should be able to reference the prompt and generation config registries. It should remain not ready while:

- prompt versions are not locked
- generation config is not locked
- registries contain unfinalized slots
- provider/budget/execution blockers remain

Gate 8H should not make freeze readiness pass.

## Tests

Tests should cover:

- both registries exist and load
- all six Gate 5 baseline families have prompt slots
- all six Gate 5 baseline families have generation config slots
- default prompt/config readiness reports not ready
- strict prompt/config readiness exits nonzero
- missing baseline families produce validation errors or blockers
- Gate 8G freeze readiness remains not ready after registry references are added

## Success Criteria

Gate 8H is complete when:

- prompt registry exists
- generation config registry exists
- prompt/config checker exists
- tests pass
- docs and experiment card exist
- README and Gate 8 readiness docs reference the registries
- placeholder and report-link scan returns no matches
- strict prompt/config readiness exits nonzero
- freeze readiness still exits nonzero in strict mode
- no provider, prompt text, datasets, indexes, model calls, or result artifacts are created

## Implementation Boundary

The next implementation should be committed separately from this design. It should keep Gate 8 in readiness status and preserve all execution lockouts.

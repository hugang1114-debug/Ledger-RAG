# Gate 8G Freeze Readiness Design

## Purpose

Gate 8G adds an execution-preflight layer for the future Gate 8 main comparison. It verifies whether provider selection, prompt/config freeze, cost budget, and run authorization are locked before any main baseline command can be allowed.

This gate remains a readiness gate. It does not select a provider, check live prices, create prompt text, call models, run retrieval evaluation, run baselines, promote source snapshots to `ready`, or create result artifacts.

## Recommended Approach

Use a small, standard-library-only readiness validator backed by tracked YAML metadata.

The validator reads existing Gate 8F metadata plus one new freeze-readiness config and reports a JSON summary. Default mode exits `0` for inspection, even when blocked. Strict mode exits nonzero until all execution-preflight fields are locked.

This approach is preferred because it makes the remaining execution blockers machine-checkable without prematurely choosing a model provider or claiming current pricing.

## Alternatives Considered

1. Lock a provider and model now.

This would require checking official model documentation and pricing on the execution date. It is too early because run budget, prompt versions, and final execution commands are not locked.

2. Write prompt templates only.

This would move part of Gate 8 forward but leave no central guard for provider, budget, prompt, and run authorization state. It would not solve the execution-control gap.

## Scope

In scope:

- add a tracked freeze-readiness config with unset provider, prompt, budget, and authorization fields
- add a local CLI that checks freeze readiness from tracked metadata
- add tests for default and strict readiness behavior
- document the freeze requirements and non-execution boundary
- add a non-running experiment card for the metadata/tooling step
- update Gate 8 readiness references

Out of scope:

- provider selection
- live pricing checks
- API key storage
- prompt template content
- model or embedding calls
- baseline execution
- metric computation
- result artifact creation
- source snapshot status promotion
- retrieval index rebuilds

## Components

### Freeze Readiness Config

Create `configs/gate8/freeze_readiness.yaml`.

The config should include:

- `gate`
- `stage`
- `status`
- `authorized_to_run: false`
- references to `configs/gate8/main_v1_run_matrix.yaml`
- references to `configs/gate8/provider_decision.yaml`
- provider freeze fields
- prompt/config freeze fields
- budget approval fields
- execution review fields
- explicit blocker list

All execution-enabling fields must default to locked-out values.

### Freeze Readiness CLI

Create `scripts/check_gate8_freeze_readiness.py`.

The CLI should:

- use Python standard library only
- read YAML-like tracked configs without adding PyYAML
- validate required top-level fields
- verify run matrix authorization is false
- verify provider decision remains selected false and run authorized false
- report provider, prompt, budget, and execution blockers
- print a JSON summary
- exit `0` by default
- exit nonzero with `--require-ready` while blockers remain

The parser can remain intentionally narrow because the project controls the config shape.

### Tests

Add `tests/test_gate8_freeze_readiness.py`.

Tests should cover:

- required config files exist and load
- default config is valid but not ready
- provider, prompt, budget, and execution blockers are reported
- default CLI exits `0` and reports readiness false
- strict CLI exits nonzero while blockers remain
- run matrix and provider decision lockout fields are respected

### Documentation

Create `docs/gate8-freeze-readiness.md`.

The document should explain:

- Gate 8G is an execution-preflight readiness layer
- no provider is selected in this gate
- no pricing is checked in this gate
- future execution must check official pricing and model docs on the run date
- prompt/config versions must be frozen before main baseline runs
- budget approval must be tracked before execution
- Gate 8 remains not passed

### Experiment Card

Create `experiments/cards/E012-gate8-freeze-readiness.md`.

The card authorizes only:

- metadata creation
- local readiness validation
- docs updates
- tests for the readiness validator

It prohibits:

- model calls
- provider selection
- price claims
- prompt finalization
- baseline execution
- result artifact creation
- snapshot promotion

## Data Flow

The validator reads:

- `configs/gate8/freeze_readiness.yaml`
- `configs/gate8/main_v1_run_matrix.yaml`
- `configs/gate8/provider_decision.yaml`

It outputs:

- `gate`
- `stage`
- `freeze_ready`
- `authorized_to_run`
- `blockers`
- `checked_configs`
- `validation_errors`

It writes no files.

## Failure Behavior

Default mode:

- exits `0`
- reports blockers in JSON
- never authorizes execution

Strict mode:

- exits `1` or another nonzero code while any blocker or validation error remains
- exits `0` only when every freeze requirement is locked and authorization metadata explicitly allows execution

## Success Criteria

Gate 8G is complete when:

- freeze-readiness config exists
- validator CLI exists
- tests pass
- docs and E012 card exist
- placeholder and report-link scan returns no matches
- default readiness reports not ready
- strict readiness exits nonzero
- no datasets, indexes, provider calls, model calls, or result artifacts are created

## Implementation Boundary

The next implementation should be committed separately from this design. It should not alter the existing source snapshot registry readiness status and should not change Gate 8 from readiness in progress to passed.

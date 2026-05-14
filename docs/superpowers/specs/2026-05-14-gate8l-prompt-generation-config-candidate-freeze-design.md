# Gate 8L Prompt and Generation Config Candidate Freeze Design

## Purpose

Gate 8L turns the existing Gate 8H prompt and generation config placeholders into auditable candidate artifacts for the future main comparison. It does not authorize model calls, run baselines, approve cost, or pass Gate 8.

The immediate goal is to make the six Gate 5 baseline families comparable before execution by fixing candidate prompt text, candidate answer format, candidate evidence budget, and candidate generation settings in tracked files.

## Recommended Approach

Use prompt files plus registry metadata.

Each baseline family gets a tracked prompt file under `prompts/gate8/main_v1/`, and the prompt registry records the prompt version, file path, SHA256 hash, baseline family, status, and non-execution authorization state. The generation config registry records shared candidate generation constraints and per-baseline config slots.

This is stronger than a registry-only freeze because the exact prompt text is reviewable and hashable. It is safer than a final execution freeze because it keeps `authorized_to_run: false` and requires a later run-date provider, price, budget, and execution review.

Rejected alternatives:

- Registry-only candidate lock: faster, but prompt text could drift outside the registry.
- Final prompt/config execution lock: too early because provider runtime behavior, budget approval, and execution card are still unresolved.

## Scope

In scope:

- Add candidate prompt files for all six baseline families:
  - `vanilla_rag`
  - `hybrid_rag`
  - `citation_only`
  - `validator_only`
  - `ledger_only`
  - `ledger_validator`
- Update `configs/gate8/prompt_registry.yaml` from reserved slots to candidate-locked prompt entries.
- Update `configs/gate8/generation_config_registry.yaml` with candidate shared constraints and candidate per-baseline generation config versions.
- Extend prompt/config readiness tooling to report candidate readiness separately from final execution readiness.
- Add tests that verify prompt files exist, hashes match, all baseline families are covered, and accidental authorization is rejected.
- Add a non-running experiment card for this readiness layer.
- Update Gate 8 readiness docs/config to reference the candidate freeze check.

Out of scope:

- No API calls.
- No model output generation.
- No dataset download.
- No retrieval or metric run.
- No cost approval.
- No final provider decision activation.
- No Gate 8 pass.

## Prompt Artifact Design

Prompt files live at:

```text
prompts/gate8/main_v1/<baseline_family>.md
```

Each prompt should be short, explicit, and compatible with the shared baseline contract. It must specify:

- answer object shape: global answer plus atomic claims
- evidence visibility rules
- citation behavior for the baseline family
- insufficient-evidence behavior
- forbidden behavior, especially citing evidence not provided to that run

Prompt files should not contain provider-specific API syntax. They are model-facing instruction candidates, not execution wrappers.

## Registry Design

`configs/gate8/prompt_registry.yaml` should remain non-executable:

```yaml
authorized_to_run: false
prompt_versions_locked: false
prompt_text_frozen: false
candidate_prompt_versions_locked: true
candidate_prompt_text_frozen: true
```

Each baseline slot should record:

- `baseline_family`
- `prompt_version`
- `prompt_status: candidate_locked`
- `prompt_file`
- `prompt_sha256`
- `authorized_to_run: false`
- `notes`

`configs/gate8/generation_config_registry.yaml` should also remain non-executable:

```yaml
authorized_to_run: false
generation_config_locked: false
candidate_generation_config_locked: true
shared_answer_style_locked: false
candidate_shared_answer_style_locked: true
shared_evidence_budget_locked: false
candidate_shared_evidence_budget_locked: true
```

Candidate shared constraints should include:

- `answer_style: global_answer_with_atomic_claims`
- `citation_granularity: evidence_item_or_ledger_span`
- `max_evidence_items: 8`
- `max_atomic_claims: 8`
- `temperature: 0`
- `max_output_tokens: 2048`
- `provider_support_recheck_required: true`

The candidate config records intended comparison constraints. Final provider support must still be checked on the run date before execution.

## Readiness Semantics

The readiness checker should expose two layers:

- `prompt_config_candidate_ready`: true only when candidate prompt files, hashes, baseline coverage, and candidate generation constraints are valid.
- `prompt_config_ready`: true only for final execution readiness.

After Gate 8L, the expected state is:

```json
{
  "prompt_config_candidate_ready": true,
  "prompt_config_ready": false,
  "authorized_to_run": false
}
```

Strict `--require-ready` must still exit nonzero because Gate 8 execution remains blocked.

Candidate readiness must fail if:

- any baseline family is missing
- any prompt file is missing
- any prompt hash mismatches file contents
- any prompt slot sets `authorized_to_run: true`
- any registry top-level authorization is true
- candidate generation constraints are unset
- prompt files contain placeholder markers or report `turn...` links

## Documentation and Card Updates

Update:

- `docs/gate8-prompt-config-readiness.md`
- `configs/gate8/main_v1_readiness.yaml`
- `README.md` if the visible gate status needs to mention Gate 8L

Add:

- `experiments/cards/E012-gate8l-prompt-generation-config-candidate-freeze.md`

The card must state that no command is authorized to call a model or run the main comparison. Its purpose is prompt/config candidate readiness only.

## Testing

Add or extend tests for:

- all six prompt files exist
- prompt SHA256 values are deterministic and match registry entries
- all six prompt slots and generation slots use candidate-locked status
- default readiness exits zero and reports candidate ready but final ready false
- strict readiness exits nonzero
- accidental authorization in prompt registry, generation config registry, or per-slot entries is rejected
- placeholder scan finds no unresolved markers or internal report links in docs, cards, configs, and prompt files

Run the full existing test suite after implementation because Gate 8 readiness layers share config contracts.

## Success Criteria

Gate 8L is complete when:

- prompt files and generation config candidate metadata are tracked
- candidate readiness is true
- final prompt/config execution readiness remains false
- strict prompt/config readiness still fails
- no model call, result artifact, or dataset mutation occurs
- tests pass
- changes are committed with a focused message

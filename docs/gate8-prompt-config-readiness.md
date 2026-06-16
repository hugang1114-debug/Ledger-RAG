# Gate 8 Prompt Config Readiness

Gate 8H reserved prompt and generation config slots for the future main comparison. Gate 8L candidate-locked the prompt files and shared generation constraints. Gate 8S promotes those reviewed candidate artifacts to final locked prompt/config metadata for the first DeepSeek main-v1 path.

This document still describes a non-executable readiness state. Gate 8S does not check live prices, call models, run baselines, compute metrics, create result artifacts, approve the main budget, authorize run commands, or pass Gate 8.

## Current State

After Gate 8S, the current registries are intentionally non-executable but final-locked:

- `prompt_versions_locked: true`
- `prompt_text_frozen: true`
- `generation_config_locked: true`
- `shared_answer_style_locked: true`
- `shared_evidence_budget_locked: true`
- `authorized_to_run: false`
- `candidate_prompt_versions_locked: true`
- `candidate_prompt_text_frozen: true`
- `candidate_generation_config_locked: true`
- `candidate_shared_answer_style_locked: true`
- `candidate_shared_evidence_budget_locked: true`

Each Gate 5 baseline family has a reserved prompt slot and generation config slot:

- `vanilla_rag`
- `hybrid_rag`
- `citation_only`
- `validator_only`
- `ledger_only`
- `ledger_validator`

## Remaining Execution Requirements

Before a main baseline run can be authorized, the project must still record:

- main budget approval
- DeepSeek pricing, model docs, terms, and runtime checks on the actual run date
- execution card with exact commands and output paths
- reproducibility review
- explicit run command authorization

## Gate 8S Final Freeze

Gate 8S locks the final prompt/config metadata for all six baseline families. The checker separates this from execution authorization:

Expected default checker state after Gate 8S:

```json
{
  "prompt_config_frozen_ready": true,
  "prompt_config_ready": false,
  "authorized_to_run": false
}
```

Strict mode is still expected to fail because the prompt and generation registries remain `authorized_to_run: false`.

## CLI Contract

Default mode is inspect-only:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml
```

Strict mode is for execution authorization checks:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml --require-ready
```

Strict mode is expected to fail until budget, run-date provider evidence, execution card review, and run command authorization are locked.

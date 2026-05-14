# Gate 8 Prompt Config Readiness

Gate 8H reserves prompt and generation config slots for the future main comparison. It does not write final prompt text, select a provider, check live prices, call models, run baselines, compute metrics, create result artifacts, promote source snapshots, or pass Gate 8.

## Current State

After Gate 8L, the current registries are intentionally non-executable but candidate-locked:

- `prompt_versions_locked: false`
- `prompt_text_frozen: false`
- `generation_config_locked: false`
- `shared_answer_style_locked: false`
- `shared_evidence_budget_locked: false`
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

## Future Freeze Requirements

Before a main baseline run can be authorized, the project must record:

- final prompt version id for each baseline family
- final prompt file path for each baseline family
- generation config version id for each baseline family
- shared answer style
- shared max evidence budget
- deterministic settings where supported
- model/provider assumptions checked on the run date
- execution card with exact commands and output paths

## Gate 8L Candidate Freeze

Gate 8L adds candidate prompt files and candidate generation constraints. Candidate readiness may pass, but final prompt/config execution readiness remains blocked.

Expected default checker state after Gate 8L:

```json
{
  "prompt_config_candidate_ready": true,
  "prompt_config_ready": false,
  "authorized_to_run": false
}
```

Strict mode is still expected to fail until final provider selection, run-date price and API checks, budget approval, execution card review, and explicit run authorization are recorded.

## CLI Contract

Default mode is inspect-only:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml
```

Strict mode is for execution authorization checks:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml --require-ready
```

Strict mode is expected to fail until prompt text, generation config, provider, and execution metadata are locked.

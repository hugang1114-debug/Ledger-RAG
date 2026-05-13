# Gate 8 Prompt Config Readiness

Gate 8H reserves prompt and generation config slots for the future main comparison. It does not write final prompt text, select a provider, check live prices, call models, run baselines, compute metrics, create result artifacts, or pass Gate 8.

## Current State

The current registries are intentionally non-executable:

- `prompt_versions_locked: false`
- `prompt_text_frozen: false`
- `generation_config_locked: false`
- `shared_answer_style_locked: false`
- `shared_evidence_budget_locked: false`
- `authorized_to_run: false`

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

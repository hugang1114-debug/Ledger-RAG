# E024 Gate 8S Main Prompt Config Freeze

## Status

Non-running readiness card. This card authorizes metadata updates and local readiness checks only.

## Purpose

Promote the reviewed Gate 8L candidate prompt and generation config artifacts to final locked metadata for the first DeepSeek `main_v1` path.

## Scope

- Lock final prompt versions for all six Gate 5 baseline families.
- Lock final generation config versions for all six Gate 5 baseline families.
- Lock shared answer style, citation granularity, max evidence budget, max claim budget, temperature, and max output tokens.
- Keep all prompt/config registries `authorized_to_run: false`.
- Keep main comparison execution blocked.

## Baselines Covered

- `vanilla_rag`
- `hybrid_rag`
- `citation_only`
- `validator_only`
- `ledger_only`
- `ledger_validator`

## Non-Goals

- No model calls.
- No dataset downloads.
- No retrieval index rebuilds.
- No main baseline runs.
- No result artifacts.
- No main budget approval.

## Validation Commands

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml --require-ready
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml
```

Expected result: prompt/config frozen readiness is true, strict execution readiness remains false.

## Remaining Blockers

- Main budget approval.
- Run-date DeepSeek pricing/model/terms/runtime recheck.
- Main execution card review.
- Reproducibility review.
- Explicit run command authorization.

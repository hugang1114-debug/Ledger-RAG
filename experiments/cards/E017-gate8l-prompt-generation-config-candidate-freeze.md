# E017 Gate 8L Prompt Generation Config Candidate Freeze

## Status

Non-running readiness card. This card does not authorize model calls, dataset downloads, baseline runs, or result artifacts.

## Purpose

Freeze candidate prompt text and candidate generation constraints for the six Gate 5 baseline families before final Gate 8 execution approval.

## Scope

- Baselines: Vanilla RAG, Hybrid RAG, Citation-only, Validator-only, Ledger-only, Ledger + Validator
- Datasets: main_v1 source snapshots only
- Provider: candidate OpenAI `gpt-5.4-mini`, execution unauthorized

## Commands

Inspect-only:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml
```

Strict final readiness, expected to fail:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml --require-ready
```

## Failure Criteria

- Any baseline prompt file is missing.
- Any prompt hash mismatches the registry.
- Candidate readiness is false.
- Final readiness is true before explicit execution authorization.
- Any model call or result artifact is produced.

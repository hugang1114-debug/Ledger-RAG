# E013 Gate 8 Prompt Config Readiness

## Purpose

Create prompt and generation config registry readiness checks for all Gate 5 baseline families. This card authorizes registry metadata and local validation tooling only.

## Authorized Scope

- create `configs/gate8/prompt_registry.yaml`
- create `configs/gate8/generation_config_registry.yaml`
- create `docs/gate8-prompt-config-readiness.md`
- create `scripts/check_gate8_prompt_config_readiness.py`
- create standard-library-only readiness helper code
- add tests for registry coverage and strict lockout behavior
- update Gate 8 readiness references

## Prohibited Actions

- final prompt text creation
- model calls
- embedding calls
- reranker calls
- provider selection
- live pricing claims
- baseline execution
- retrieval evaluation
- metric computation
- result artifact creation
- source snapshot status promotion to `ready`

## Expected Outputs

- `configs/gate8/prompt_registry.yaml`
- `configs/gate8/generation_config_registry.yaml`
- `docs/gate8-prompt-config-readiness.md`
- `src/ledger_rag_gate8/prompt_config_readiness.py`
- `scripts/check_gate8_prompt_config_readiness.py`
- `tests/test_gate8_prompt_config_readiness.py`
- README and readiness doc references

## Success Criteria

- all six Gate 5 baseline families have prompt slots
- all six Gate 5 baseline families have generation config slots
- default prompt/config readiness command exits `0`
- default prompt/config readiness reports `prompt_config_ready: false`
- strict prompt/config readiness command exits nonzero
- Gate 8G freeze readiness remains blocked
- no provider, final prompt text, model calls, or result artifacts are created

## Cost Class

Local metadata and tests only. No model, API, provider, or cloud cost is authorized.

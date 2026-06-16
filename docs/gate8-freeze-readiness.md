# Gate 8 Freeze Readiness

Gate 8G adds an execution-preflight check for the future main comparison. It does not select a provider, check live prices, finalize prompts, call models, run baselines, compute metrics, create result artifacts, or pass Gate 8.

## Current State

The current Gate 8G metadata keeps execution locked:

- `authorized_to_run: false`
- `provider_freeze_selected: false`
- `prompt_versions_locked: false`
- `generation_config_locked: false`
- `cost_budget_approved: false`
- `execution_authorized: false`
- provider evidence registry is not locked or reviewed

This is intentional. The project now has source snapshots and local lexical indexes, but main execution still needs provider, prompt, budget, and reproducibility decisions.

## Future Freeze Requirements

Before any main baseline command can run, the project must record:

- provider name and model id
- official pricing source checked on the run date
- official model documentation checked on the run date
- terms or data-retention note checked on the run date
- locked provider evidence registry with reviewed official evidence
- API key or local runtime availability note
- prompt version ids for all comparable baselines
- generation config version id
- approved cost budget note
- execution card with exact commands and output paths
- reproducibility review covering paths, seeds, configs, and ignored artifact destinations

## CLI Contract

The local checker reads:

- `configs/gate8/freeze_readiness.yaml`
- `configs/gate8/main_v1_run_matrix.yaml`
- `configs/gate8/provider_decision.yaml`

Default mode is inspect-only:

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml
```

Strict mode is for execution authorization checks:

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml --require-ready
```

Strict mode is expected to fail until provider, prompt, budget, execution card, and reproducibility metadata are locked.

Provider evidence strict mode is also required before freeze can authorize execution:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --require-ready
```

This strict provider evidence check is expected to fail until official provider evidence is reviewed, the registry is locked, and model calls are authorized by a future execution gate.

## Prohibited In Gate 8G

- model calls
- embedding calls
- reranker calls
- provider selection
- price claims without official run-date verification
- prompt finalization
- baseline execution
- metric computation
- result artifact creation
- source snapshot status promotion
- retrieval index rebuilds

Gate 8G exists to make the remaining execution blockers explicit and machine-checkable.

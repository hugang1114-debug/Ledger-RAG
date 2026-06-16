# E014 Gate 8 Provider Evidence Readiness

## Purpose

Create a non-running provider evidence readiness registry for the future Gate 8 main comparison. This card authorizes metadata validation only; it does not authorize execution.

## Authorized Scope

- create `configs/gate8/provider_evidence_registry.yaml`
- create `docs/gate8-provider-evidence-readiness.md`
- create this experiment card

## Authorized Commands

This card records the planned local validation contract only. The checker is implemented in a later task, so these command strings are not authorized to run under this card until `scripts/check_gate8_provider_evidence_readiness.py` exists.

Planned inspect-only command:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml
```

Planned strict readiness command:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --require-ready
```

After the checker exists, the default command is inspect-only. The strict command must fail until all official provider evidence is recorded and reviewed under a later authorized gate.

## Prohibited Actions

- live provider lookup
- live pricing lookup
- provider/model selection
- API key storage
- model calls
- embedding/reranker calls
- baseline execution
- metric computation
- result artifacts
- running the planned checker before it is implemented

## Expected Outputs

- `configs/gate8/provider_evidence_registry.yaml`
- `docs/gate8-provider-evidence-readiness.md`
- `experiments/cards/E014-gate8-provider-evidence-readiness.md`

## Success Criteria

- all nine provider evidence slots are present
- provider evidence remains unlocked
- provider and model remain unset
- `authorized_to_run` remains `false`
- strict readiness remains blocked until official evidence is recorded and reviewed
- no provider, model, price, API key, model call, baseline run, metric, or result artifact is created

## Cost Class

Local metadata validation only. No model, API, provider, or cloud cost is authorized.

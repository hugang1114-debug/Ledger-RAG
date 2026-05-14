# E016 Gate 8K OpenAI Provider Evidence Candidate Lock

## Status

Non-running readiness card. This card records provider evidence metadata only.

## Purpose

Lock OpenAI `gpt-5.4-mini` as the first Gate 8 provider/model candidate while keeping main comparison execution unauthorized.

## Scope

- Record official OpenAI source URLs checked on 2026-05-14.
- Record candidate provider/model/snapshot metadata.
- Keep API key availability and cost budget unresolved.
- Keep `run_authorized: false`.

## Not Authorized

- No model calls.
- No baseline runs.
- No prompt/config freeze.
- No budget approval.
- No result artifacts.
- No final Gate 8 passage.

## Verification Commands

```powershell
python -m pytest tests/test_gate8_provider_evidence_readiness.py -v
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --require-ready
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml --require-ready
```

Strict provider and freeze checks are expected to fail until runtime, budget, prompt/config, and execution authorization are locked.

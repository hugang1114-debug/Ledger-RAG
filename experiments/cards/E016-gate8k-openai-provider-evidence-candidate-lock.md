# E016 Gate 8K OpenAI Provider Evidence Candidate Lock

## Status

Non-running readiness card. This card records provider evidence metadata only.

## Purpose

Lock OpenAI `gpt-5.4-mini` as the first Gate 8 provider/model candidate while keeping main comparison execution unauthorized.

## Research Question

Can Gate 8K record enough official provider evidence to identify OpenAI `gpt-5.4-mini` as the first main-comparison candidate without authorizing model calls, baseline runs, prompt/config freeze, budget approval, or Gate 8 passage?

## Gate

Gate 8K provider evidence candidate lock for the Gate 8 main comparison readiness layer.

## Dataset And License Status

No dataset is executed by this card. The eventual Gate 8 main comparison remains scoped to the existing main v1 datasets and their locked source snapshot metadata, but this card only records provider candidate evidence.

Dataset license status is unchanged by this card. No dataset download, transformation, retrieval evaluation, or baseline execution is authorized.

## Methods And Baselines

No method variant or baseline is run. The Gate 5 baseline families remain future execution targets only:

- Vanilla RAG
- Hybrid RAG
- Citation-only
- Validator-only
- Ledger-only
- Ledger + Validator

This card does not promote any method, prompt, generation config, provider decision, or baseline result.

## Scope

- Record official OpenAI source URLs checked on 2026-05-14.
- Record candidate provider/model/snapshot metadata.
- Keep API key availability and cost budget unresolved.
- Keep `run_authorized: false`.

## Inputs

- `configs/gate8/provider_evidence_registry.yaml`
- `configs/gate8/main_v1_readiness.yaml`
- `configs/gate8/provider_decision.yaml`
- Official OpenAI provider source URLs recorded in the provider evidence registry.

## Outputs

- Candidate provider/model metadata only.
- Readiness documentation updates only.
- No result artifacts.
- No model outputs.
- No baseline run records.
- No metric records.

## Metrics

No experiment metrics are computed. Readiness is assessed only by metadata checks that distinguish candidate readiness from strict execution readiness.

## Failure Criteria

- Candidate provider/model metadata is missing or inconsistent across readiness docs and config.
- Candidate evidence is described as execution authorization.
- API/runtime availability or cost budget is treated as resolved.
- `authorized_to_run` or `run_authorized` is set to `true`.
- Any model call, baseline run, prompt/config freeze, budget approval, result artifact, or Gate 8 passage is claimed from this card.

## Exact Commands

```powershell
python -m pytest tests/test_gate8_provider_evidence_readiness.py -v
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --require-ready
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml --require-ready
```

Strict provider and freeze checks are expected to fail until runtime, budget, prompt/config, and execution authorization are locked.

## Output Paths

No output paths are authorized for generated experiment artifacts. Future main comparison artifacts remain reserved under ignored Gate 8 artifact paths only after a later execution card authorizes them.

## Expected Cost Class

No-cost metadata-only readiness update. No provider API calls, model calls, embeddings, reranking, baseline runs, or metric jobs are authorized.

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

## Reviewer Notes

This card is intentionally non-running and non-executable. It records a candidate lock only; final provider selection, live recheck, API/runtime availability, cost budget approval, prompt/config freeze, execution authorization, and main baseline execution remain unresolved.

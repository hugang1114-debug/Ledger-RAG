# Gate 8 Provider Evidence Readiness

Gate 8I creates the provider evidence readiness scaffold for the future Gate 8 main comparison. It defines the official evidence that must be recorded and reviewed before any provider or model can be selected and before any main baseline execution can be authorized.

This is a non-executable readiness state. It does not choose a provider, choose a model, check live prices, store API keys, call models, run baselines, compute metrics, create result artifacts, promote source snapshots, or pass Gate 8.

## Current State

The provider evidence registry remains locked out for execution:

- `provider_evidence_locked: false`
- `provider_selected: false`
- `provider: unset`
- `model: unset`
- `authorized_to_run: false`

Gate 8K partially records and reviews candidate evidence for OpenAI `gpt-5.4-mini` official source slots. That candidate state is metadata only: it records the first provider/model candidate and official-source evidence checked on 2026-05-14.

Execution evidence remains incomplete because API/runtime availability and cost budget approval are unresolved, final provider selection is unset, and `authorized_to_run` remains `false`. The final provider/model decision fields remain unset even though candidate provider/model metadata is recorded separately as `candidate_provider` and `candidate_model`.

## Gate 8K Candidate State

The checker now distinguishes candidate readiness from execution readiness. After Gate 8K, default inspection may report `provider_candidate_ready: true`, while strict readiness still reports `provider_evidence_ready: false`.

This means official candidate evidence exists, but model calls remain blocked by unresolved runtime availability, cost budget approval, final provider selection, prompt/config freeze, and execution authorization.

## Required Evidence Slots

Gate 8I requires these evidence slots before strict readiness can pass:

- `official_pricing_source`
- `official_model_docs_source`
- `official_terms_privacy_source`
- `model_id_version_source`
- `context_window_source`
- `output_limit_source`
- `rate_limit_or_throughput_source`
- `api_key_or_runtime_availability_note`
- `cost_budget_approval_note`

Official evidence must come from provider documentation, provider pricing pages, provider terms or privacy pages, official model documentation, or an approved internal availability or budget note. Dynamic pages and report-local links are not sufficient evidence.

## CLI Contract

These exact command forms define the local validation contract for the implemented checker. The checker is runnable under Gate 8I for metadata inspection only; it does not authorize model calls, live provider lookup, live pricing lookup, or baseline execution.

Default mode is inspect-only:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml
```

Strict mode is for execution authorization checks:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --require-ready
```

Strict mode is expected to fail until all official evidence slots are recorded, reviewed, linked to a concrete provider/model decision, and the registry explicitly locks `provider_evidence_locked: true` under an authorized later gate.

## Execution Boundary

Gate 8I authorizes only non-executing metadata inspection with the implemented checker. It does not authorize live provider lookup, live pricing lookup, provider/model selection, API key storage, model calls, embedding calls, reranker calls, baseline execution, metric computation, or result artifacts.

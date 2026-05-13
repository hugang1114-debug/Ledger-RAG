# Gate 8 Provider Evidence Readiness

Gate 8I creates the provider evidence readiness scaffold for the future Gate 8 main comparison. It defines the official evidence that must be recorded and reviewed before any provider or model can be selected and before any main baseline execution can be authorized.

This is a non-executable readiness state. It does not choose a provider, choose a model, check live prices, store API keys, call models, run baselines, compute metrics, create result artifacts, promote source snapshots, or pass Gate 8.

## Current State

The provider evidence registry is intentionally locked out:

- `provider_evidence_locked: false`
- `provider_selected: false`
- `provider: unset`
- `model: unset`
- `authorized_to_run: false`

Every evidence slot is present but incomplete. Source URLs, check timestamps, reviewer fields, provider, and model remain unset until a later execution-preparation gate records official evidence close to the run date.

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

These exact command forms define the planned local validation contract for the future checker. They are not runnable under Gate 8I until `scripts/check_gate8_provider_evidence_readiness.py` is implemented in a later task.

Planned default mode is inspect-only:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml
```

Planned strict mode is for execution authorization checks:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --require-ready
```

After the checker exists, strict mode must fail until all official evidence slots are recorded, reviewed, linked to a concrete provider/model decision, and the registry explicitly locks `provider_evidence_locked: true` under an authorized later gate.

## Execution Boundary

Gate 8I does not authorize running the planned checker before it exists. It also does not authorize live provider lookup, live pricing lookup, provider/model selection, API key storage, model calls, embedding calls, reranker calls, baseline execution, metric computation, or result artifacts.

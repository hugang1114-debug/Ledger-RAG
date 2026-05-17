# E023 Gate 8R DeepSeek Provider Evidence Lock

## Research Question

Can the project lock DeepSeek-V4-Pro as the evidence-backed primary provider while keeping full Gate 8 execution blocked?

## Dataset And License Status

No dataset is executed by this card. Main-v1 dataset readiness remains unchanged.

## Method Variants And Baselines

No baseline family is run. This is provider metadata and evidence review only.

## Evidence Inputs

- Gate 8N selected `deepseek_v4_pro` as primary provider.
- Gate 8O authorized only a DeepSeek smoke run under the 10 USD ceiling.
- Gate 8P executed one DeepSeek smoke call.
- Gate 8Q reviewed smoke artifacts into `configs/gate8/deepseek_smoke_result_summary.yaml`.
- Official DeepSeek provider/model/pricing source: `https://api-docs.deepseek.com/quick_start/pricing`.

## Success Criteria

- `provider_evidence_locked_ready: true`.
- `provider_evidence_ready: false`.
- Provider/model are `deepseek / deepseek-v4-pro` in registry and decision metadata.
- No raw provider response, API key, or secret is tracked.
- Main budget and full execution remain unauthorized.

## Commands

```powershell
python -m pytest tests/test_gate8_provider_evidence_readiness.py -v
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --provider-decision configs/gate8/provider_decision.yaml
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --provider-decision configs/gate8/provider_decision.yaml --require-ready
```

Strict mode is expected to exit nonzero.

## Expected Cost Class

Zero. This card does not call external providers.

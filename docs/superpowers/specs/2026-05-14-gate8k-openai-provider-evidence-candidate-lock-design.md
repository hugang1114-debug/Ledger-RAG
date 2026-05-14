# Gate 8K OpenAI Provider Evidence Candidate Lock Design

## Purpose

Gate 8K records an OpenAI provider/model candidate for the future Gate 8 main comparison while keeping execution locked. It closes part of the provider-evidence gap created in Gate 8I, but it does not authorize model calls, baseline runs, result artifacts, or final Gate 8 passage.

The candidate provider is OpenAI. The candidate model is `gpt-5.4-mini`, using the pinned snapshot `gpt-5.4-mini-2026-03-17` when the API accepts that model id. The model is chosen as the first candidate because the official model page lists a 400,000 token context window, a 128,000 token maximum output, Responses API support, and lower token prices than `gpt-5.4` and `gpt-5.5`. This is a pragmatic v1 choice for repeated baseline comparisons; it is not a claim that `gpt-5.4-mini` is the best possible research model.

## Official Evidence Checked

Evidence was checked from official OpenAI sources on 2026-05-14:

- OpenAI model index: `https://developers.openai.com/api/docs/models`
- `gpt-5.4-mini` model page: `https://developers.openai.com/api/docs/models/gpt-5.4-mini`
- OpenAI pricing page: `https://platform.openai.com/docs/pricing/`
- OpenAI service terms: `https://openai.com/policies/service-terms/`
- OpenAI business data page: `https://openai.com/business-data/`
- OpenAI privacy policy: `https://openai.com/policies/privacy-policy/`

The implementation must store URLs and checked dates, not copied report claims. Pricing, model availability, context window, output limit, rate limits, and terms remain temporally unstable and must be rechecked on the actual run date before Gate 8 execution can be authorized.

## Scope

In scope:

- Update provider evidence metadata to record OpenAI as the provider candidate.
- Record `gpt-5.4-mini` and the preferred snapshot id as the model candidate.
- Mark official source slots as `reviewed` when official source URLs, checked dates, and reviewer notes are present.
- Add checker support for candidate-locked-but-not-authorized state.
- Keep `api_key_or_runtime_availability_note` and `cost_budget_approval_note` unresolved unless local runtime and budget approval are explicitly verified later.
- Update docs and the Gate 8 readiness matrix to show provider evidence is partially locked but execution remains blocked.

Out of scope:

- No API calls.
- No API key lookup beyond documenting that runtime availability is still unverified.
- No model output generation.
- No baseline execution.
- No price or budget estimate treated as final.
- No provider comparison across Anthropic, Google, or local models.
- No prompt/config freeze.
- No result files.

## Metadata Semantics

Gate 8K introduces a candidate state distinct from final readiness:

- `provider_candidate_selected: true`
- `provider_evidence_candidate_locked: true`
- `provider_evidence_locked: false`
- `provider_selected: false`
- `authorized_to_run: false`

The checker should report a new candidate-level readiness field, for example `provider_candidate_ready: true`, when the official candidate evidence is present. It must continue to report `provider_evidence_ready: false` until every execution-level blocker is cleared.

The provider decision file should mirror the candidate while remaining non-executable:

- `selected: false`
- `candidate_provider: openai`
- `candidate_model: gpt-5.4-mini`
- `candidate_model_snapshot: gpt-5.4-mini-2026-03-17`
- `run_authorized: false`

## Evidence Slot Handling

Gate 8K can mark these slots as reviewed:

- `official_pricing_source`
- `official_model_docs_source`
- `official_terms_privacy_source`
- `model_id_version_source`
- `context_window_source`
- `output_limit_source`
- `rate_limit_or_throughput_source`

Gate 8K must keep these slots unresolved:

- `api_key_or_runtime_availability_note`
- `cost_budget_approval_note`

This means strict provider evidence readiness must still fail after Gate 8K. The failure is intentional because a provider candidate is not enough to run the main comparison.

## Checker Behavior

The provider evidence checker should distinguish three states:

1. Empty scaffold: no candidate and no final evidence.
2. Candidate locked: official candidate evidence exists, but execution remains blocked.
3. Execution ready: all evidence reviewed, runtime and budget verified, provider decision selected, and authorization enabled.

Gate 8K should move the project from state 1 to state 2 only.

Expected checker behavior after Gate 8K:

- Default provider evidence check exits `0`.
- Summary includes `provider_candidate_ready: true`.
- Summary includes `provider_evidence_ready: false`.
- `--require-ready` exits nonzero.
- Remaining blockers include runtime availability, budget approval, final provider selection, and execution authorization.

## Files

Expected files to modify or add:

- `configs/gate8/provider_evidence_registry.yaml`
- `configs/gate8/provider_decision.yaml`
- `configs/gate8/main_v1_readiness.yaml`
- `docs/model-provider-readiness.md`
- `docs/gate8-provider-evidence-readiness.md`
- `docs/main-comparison-readiness.md`
- `experiments/cards/E016-gate8k-openai-provider-evidence-candidate-lock.md`
- `src/ledger_rag_gate8/provider_evidence_readiness.py`
- `tests/test_gate8_provider_evidence_readiness.py`

No dataset, retrieval index, artifact, model output, or secret files should be created.

## Testing

Required verification:

- Provider evidence checker reports candidate readiness but not execution readiness.
- Strict provider evidence readiness still exits nonzero.
- Strict freeze readiness still exits nonzero.
- Gate 8J snapshot/index readiness remains passing.
- Placeholder and report-link scan has no matches.
- Git status shows only ignored caches, datasets, artifacts, and PDFs outside tracked changes.

## Success Criteria

Gate 8K is complete when:

- Official OpenAI evidence URLs and checked dates are tracked.
- `gpt-5.4-mini` candidate metadata is recorded with the preferred snapshot id.
- Candidate readiness is machine-checkable.
- Execution remains locked.
- Tests prove candidate lock and execution lock are separate states.

Gate 8K does not complete Gate 8. It only reduces provider evidence ambiguity before a later freeze gate.

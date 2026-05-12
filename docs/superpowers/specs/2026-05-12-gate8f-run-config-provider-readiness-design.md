# Gate 8F Run Config And Provider Readiness Design

## Purpose

Gate 8F prepares the non-running configuration layer needed before any real Gate 8 main comparison. It locks the shape of the main v1 run matrix, provider decision metadata, prompt/config readiness rules, and cost-budget evidence requirements.

Gate 8F does not select a model provider, check current prices, run prompts, call models, run baselines, compute metrics, or mark Gate 8 ready.

## Current State

Gate 8A through Gate 8E established:

- source snapshots for HotpotQA, 2WikiMultihopQA, and MuSiQue
- local lexical retrieval index artifacts for all three datasets
- a source snapshot registry with `retrieval_index_path` set for all three records
- strict readiness still failing because snapshot `status` remains `source_ready`

The remaining readiness questions are operational rather than dataset-preparation questions: which provider will run, how model and prompt versions are frozen, how cost is approved, and which dataset-baseline combinations are authorized later.

## Scope

In scope:

- create a non-executable main v1 run matrix covering three datasets and six baseline families
- create provider decision metadata with `selected: false`
- define provider selection criteria without picking a provider
- define current-price verification requirements without recording stale prices
- define prompt/config freeze requirements without writing final prompts
- define artifact path conventions for future runs
- add a non-running experiment card for Gate 8F
- update readiness docs and config to reference the new metadata

Out of scope:

- selecting OpenAI, Anthropic, local, or any other model provider
- checking live provider prices
- creating API keys or secrets
- calling model, embedding, reranker, or evaluator providers
- writing final prompt text
- running retrieval evaluation, generation, verification, baseline comparisons, or metrics
- changing source snapshot status from `source_ready` to `ready`
- creating result files under `artifacts/`

## Recommended Approach

Use documentation plus YAML metadata only. Gate 8F should make the future execution surface explicit while preserving the current lockout.

This is safer than selecting a provider now because model availability and pricing are temporally unstable. Any future run must re-check official provider pricing and model terms at execution time. The provider decision file should therefore record selection criteria, required evidence, and unset fields rather than pretending a provider choice is already approved.

## Files To Add

`docs/gate8-run-config-readiness.md`

- describes what is locked by the run matrix
- states that no command is authorized by this gate
- names the three datasets and six baselines
- states that every future executable run must reference the same source snapshot id, retrieval index path, prompt version, model version, and artifact root

`docs/model-provider-readiness.md`

- defines provider selection criteria
- requires official price and terms checks at execution time
- requires model id, version/date, context window, rate limits, data retention note, and deterministic settings
- states `selected: false` until a later gate explicitly selects a provider

`configs/gate8/main_v1_run_matrix.yaml`

- records three dataset ids and six baseline families
- points to source snapshot ids and retrieval index manifest paths from `snapshots/main_v1/source_snapshots.json`
- records metric groups from Gate 6
- records artifact root conventions
- sets `authorized_to_run: false`

`configs/gate8/provider_decision.yaml`

- records provider decision status
- keeps provider, model, pricing, API key, and prompt versions unset
- records required evidence fields for future selection
- records disallowed behavior such as using stale prices or undocumented model aliases

`experiments/cards/E011-gate8-run-config-readiness.md`

- authorizes only metadata creation
- forbids model calls, baseline runs, metric runs, result files, and status promotion

## Main V1 Run Matrix Shape

The run matrix should contain one dataset entry per source-ready dataset:

- `hotpotqa`
- `2wikimultihopqa`
- `musique`

Each dataset entry should include:

- `dataset_id`
- `split`
- `source_snapshot_id`
- `source_snapshot_registry_path`
- `retrieval_index_path`
- `question_source`
- `artifact_root`

The matrix should contain one baseline entry per Gate 5 baseline family:

- `vanilla_rag`
- `hybrid_rag`
- `citation_only`
- `validator_only`
- `ledger_only`
- `ledger_validator`

Each baseline entry should include:

- `baseline_family`
- `requires_provider`
- `requires_generation`
- `requires_verifier`
- `requires_ledger`
- `authorized_to_run: false`

Hybrid retrieval should remain defined as a baseline family but blocked for execution until a dense or hybrid retrieval implementation is separately locked. Gate 8F should not pretend that the current lexical index is enough for a true hybrid baseline.

## Provider Decision Shape

The provider decision file should keep:

- `selected: false`
- `provider: unset`
- `model: unset`
- `pricing_checked_at: unset`
- `pricing_source: unset`
- `terms_checked_at: unset`
- `data_retention_note: unset`
- `api_key_required: true`
- `api_key_present: false`
- `prompt_versions_locked: false`
- `run_authorized: false`

Required future evidence:

- official pricing URL checked on the run date
- official model documentation URL checked on the run date
- model id and version/date
- context window and output limit
- rate limit or throughput note
- data retention or privacy note
- deterministic parameter settings
- cost budget approval note

## Readiness Semantics

After Gate 8F:

- Gate 8 remains `readiness_in_progress`
- `authorized_to_run` remains `false`
- provider remains unselected
- prompt versions remain unlocked
- no result artifacts exist
- snapshot registry statuses remain `source_ready`
- strict readiness still fails

Gate 8F should reduce ambiguity, not clear the final status blocker.

## Error Handling And Guardrails

Any future validator or execution script should reject:

- a run matrix with `authorized_to_run: true`
- provider metadata with stale or missing official pricing evidence
- model aliases without official documentation
- prompt versions that are not frozen
- hybrid baseline execution without a locked hybrid retrieval implementation
- any run that writes results before an execution card exists

Gate 8F may document these guardrails but should not implement a full runner.

## Tests And Verification

Gate 8F is a documentation/config gate. Verification should include:

- required files exist
- placeholder scan has no matches
- run matrix contains all three datasets
- run matrix contains all six baseline families
- provider decision file keeps `selected: false` and `run_authorized: false`
- readiness check still reports `gate8_ready: false`
- git status shows no model outputs or result artifacts staged

## Follow-Up Gate

The next gate should be a deliberate provider and prompt freeze gate. That later gate may browse official provider docs and pricing, decide on a model/provider, freeze prompt versions, and update the provider decision metadata. It still should not run main baselines until an execution card authorizes exact commands.

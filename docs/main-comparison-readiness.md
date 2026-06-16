# Main Comparison Readiness

Gate 8 readiness is a preparation layer, not a completed main comparison. Gate 8 is not passed until the selected datasets are converted into locked source snapshots, all required baseline families run against the same inputs, and comparable run and metric records are produced.

## Target Scope

The first real main comparison is locked to the `main_v1` dataset set from Gate 4:

- HotpotQA
- 2WikiMultihopQA
- MuSiQue

These datasets are selected because they are static, replayable multihop QA targets with realistic support-fact evaluation paths. They remain blocked for execution until their source snapshots, licenses, splits, and processed corpora are recorded.

## Required Baseline Families

The Gate 8 comparison must include all six Gate 5 baseline families under the same input, corpus snapshot, evidence budget, answer style, and output contract:

- Vanilla RAG
- Hybrid RAG
- Citation-only
- Validator-only
- Ledger-only
- Ledger + Validator

No result may be reported as a main comparison if one family is run on a different split, corpus version, evidence budget, prompt contract, or metric schema.

## Required Metric Groups

Gate 8 uses the Gate 6 metric groups:

- retrieval: recall and ranking quality for expected evidence
- answer quality: exact-match or task-appropriate answer correctness
- attribution: citation precision, citation recall, support rate, unsupported claim rate, and mapping completeness
- system: latency, cost, ledger size, index size, and failure count
- aggregation: dataset-level and baseline-level summaries without hiding attribution failures inside one combined score

Each metric record must cite the metric definition, dataset snapshot, baseline family, code/config version, and aggregation rule.

## Readiness Blockers

Gate 8 cannot run while any blocker remains:

- dataset snapshots are missing for HotpotQA, 2WikiMultihopQA, or MuSiQue
- source snapshot ids and hashes are unset
- retrieval index build commands are not recorded
- model/provider choice is not selected and versioned
- prompt/config versions are not frozen
- cost budget is not approved from current official pricing
- run reproducibility review has not confirmed paths, seeds, commands, and artifact destinations
- evaluation scripts or metric plans are not pinned for each dataset

Gate 8K locks an OpenAI `gpt-5.4-mini` candidate, but Gate 8 remains blocked until the candidate is rechecked on the run date and promoted through the execution freeze.

## Ready-To-Run Conditions

Before authorizing main baseline execution, the project must have:

- one source snapshot record per dataset and split
- one retrieval index build record per dataset snapshot
- one run config per baseline family using the shared Gate 5 contract
- one metric config using the Gate 6 contract
- one artifact destination per dataset and baseline family under ignored `artifacts/`
- one cost budget note based on current provider pricing
- one execution card that names the exact command and output paths

## Snapshot Readiness Check

Gate 8A adds a tracked source snapshot registry at `snapshots/main_v1/source_snapshots.json`. The registry is allowed to contain pending records while datasets have not been downloaded or processed, but the metadata shape must stay valid.

Run the local readiness check before any Gate 8 execution card is written:

```powershell
python scripts/check_gate8_snapshot_readiness.py --registry snapshots/main_v1/source_snapshots.json
```

Use strict mode only when deciding whether main baseline execution is authorized:

```powershell
python scripts/check_gate8_snapshot_readiness.py --registry snapshots/main_v1/source_snapshots.json --require-ready
```

Strict mode is expected to fail until license notes, source snapshot ids, data hashes, split hashes, build command records, and retrieval index paths are locked.

Gate 8B starts source snapshot locking with HotpotQA dev distractor only:

```powershell
python scripts/build_hotpotqa_source_snapshot.py --registry snapshots/main_v1/source_snapshots.json --output-root datasets/source_snapshots --split dev_distractor
```

This command may set HotpotQA to `source_ready`, but it does not build a retrieval index and does not pass Gate 8.

Gate 8C adds the 2WikiMultihopQA dev source snapshot builder:

```powershell
python scripts/build_2wiki_source_snapshot.py --registry snapshots/main_v1/source_snapshots.json --output-root datasets/source_snapshots --split dev
```

This command may set 2WikiMultihopQA to `source_ready`, but it also does not build a retrieval index and does not pass Gate 8.

Gate 8D adds the MuSiQue answerable dev source snapshot builder:

```powershell
python scripts/build_musique_source_snapshot.py --registry snapshots/main_v1/source_snapshots.json --output-root datasets/source_snapshots --split dev
```

This command may set MuSiQue to `source_ready`, but it does not build a retrieval index and does not pass Gate 8.

Gate 8E builds local lexical retrieval index artifacts for all three source-ready datasets:

```powershell
python scripts/build_gate8_lexical_indexes.py --registry snapshots/main_v1/source_snapshots.json --index-root datasets/retrieval_indexes/main_v1
```

This command may set `retrieval_index_path` for HotpotQA, 2WikiMultihopQA, and MuSiQue, but it does not run retrieval evaluation, does not run baselines, and does not pass Gate 8.

Gate 8J promotes snapshot/index metadata after local validation:

```powershell
python scripts/check_gate8_snapshot_index_promotion.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
python scripts/promote_gate8_snapshot_indexes.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
```

This promotion may make strict snapshot readiness pass, but it does not run baselines, call models, compute metrics, create result artifacts, or pass Gate 8.

Gate 8F locks non-executable run matrix and provider-readiness metadata:

```powershell
configs/gate8/main_v1_run_matrix.yaml
configs/gate8/provider_decision.yaml
```

These files may define the future dataset/baseline matrix and provider evidence requirements, but they do not select a provider, freeze prompts, approve budget, run baselines, or pass Gate 8.

Gate 8G adds an execution-preflight freeze readiness check:

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml
```

Strict mode remains blocked until provider, prompt, budget, execution card, and reproducibility metadata are locked:

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml --require-ready
```

This check is metadata-only. It does not select a provider, check live prices, write prompts, run baselines, compute metrics, create result artifacts, or pass Gate 8.

Gate 8H adds prompt and generation config registry readiness checks:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml
```

Strict mode remains blocked until prompt versions, prompt files, shared generation config, provider assumptions, and execution metadata are locked:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml --require-ready
```

This check reserves prompt/config slots only. It does not write final prompt text, select a provider, check live prices, run baselines, compute metrics, create result artifacts, or pass Gate 8.

## Provider Evidence Registry

Gate 8I adds `configs/gate8/provider_evidence_registry.yaml` as the tracked registry for official provider evidence. Gate 8 cannot run until this registry is locked with reviewed official evidence for pricing, model docs, terms/privacy, model id/version, context window, output limits, rate limits/throughput, runtime availability, and approved budget.

Default mode is metadata inspection only:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml
```

Strict mode is for future execution authorization checks:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --require-ready
```

Strict mode fails until a future execution gate records reviewed official evidence and authorizes model calls.

## Prohibited Actions In This Layer

- do not download datasets except through explicitly authorized source snapshot builders
- do not build retrieval indexes except through the approved Gate 8E local lexical index builder
- do not call model or embedding providers
- do not run main baselines
- do not create result files
- do not claim paper evidence from readiness documents

This layer exists so Gate 8 can later run from stable inputs rather than live or mutable sources.

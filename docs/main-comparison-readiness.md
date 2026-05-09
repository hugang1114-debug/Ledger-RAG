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

## Prohibited Actions In This Layer

- do not download datasets
- do not build retrieval indexes
- do not call model or embedding providers
- do not run main baselines
- do not create result files
- do not claim paper evidence from readiness documents

This layer exists so Gate 8 can later run from stable inputs rather than live or mutable sources.

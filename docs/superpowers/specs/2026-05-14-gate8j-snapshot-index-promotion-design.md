# Gate 8J Snapshot Index Promotion Design

## Purpose

Gate 8J promotes the dataset snapshot and retrieval index metadata that is already locally present and verifiable. It clears stale snapshot/index readiness blockers without running baselines, calling models, evaluating retrieval quality, or claiming that Gate 8 has passed.

The current state is internally inconsistent: `snapshots/main_v1/source_snapshots.json` records source snapshots and retrieval index paths for HotpotQA, 2WikiMultihopQA, and MuSiQue, while strict snapshot readiness still fails because each record remains `status: source_ready`. `configs/gate8/main_v1_readiness.yaml` also still contains unset dataset path, hash, split, and index fields even though the source snapshot registry now has concrete values.

Gate 8J should resolve that metadata drift using local validation only.

## Recommended Approach

Add a tracked promotion readiness layer with a standard-library-only validator and an explicit promotion command.

The validator should inspect:

- `snapshots/main_v1/source_snapshots.json`
- each recorded `dataset_path`
- each recorded `retrieval_index_path`
- the corresponding local index manifest
- `configs/gate8/main_v1_readiness.yaml`

The promotion command should update tracked metadata only when every local check passes:

- promote each snapshot record from `source_ready` to `ready`
- keep the registry gate status as `readiness_in_progress`
- sync dataset fields in `configs/gate8/main_v1_readiness.yaml` from the snapshot registry
- remove stale dataset/index unset blockers from `main_v1_readiness.yaml`
- keep provider, prompt, budget, freeze, run authorization, and execution blockers in place

Gate 8J should add tests proving that metadata promotion is refused when an index manifest is missing, malformed, or mismatched.

## Alternatives Considered

1. Leave snapshot registry as `source_ready` until the main baseline run.

This is overly conservative because local source snapshots and lexical index artifacts already exist. Keeping stale status blockers makes the readiness report less useful and hides the remaining blockers that actually matter.

2. Mark Gate 8 ready after promoting snapshot/index metadata.

This is wrong. Dataset and index readiness is necessary, but not sufficient. Gate 8 still requires provider evidence, prompt/generation config freeze, cost budget approval, execution card, reproducibility review, baseline runs, and metric records.

3. Rebuild indexes inside the promotion command.

This broadens the step unnecessarily. Gate 8E already owns index building. Gate 8J should validate and promote existing artifacts. If an index is missing, Gate 8J should fail with a clear blocker and point back to the Gate 8E builder.

## Scope

In scope:

- validate all three `main_v1` snapshot records
- validate local retrieval index manifest existence
- validate index manifest identity against dataset id, split, source snapshot id, and corpus hash when those fields are present
- promote snapshot records to `ready` only after local checks pass
- sync `configs/gate8/main_v1_readiness.yaml` dataset fields from the snapshot registry
- update readiness docs and add a non-running experiment card
- add tests for pass and fail cases

Out of scope:

- downloading datasets
- rebuilding retrieval indexes
- running retrieval evaluation
- running any baseline
- calling model, embedding, reranker, or provider APIs
- selecting a provider or model
- checking live provider pricing
- freezing prompt text
- approving budget
- creating main result artifacts
- marking Gate 8 completed

## Promotion Preconditions

Each dataset record can be promoted only if:

- `dataset_id` is one of `hotpotqa`, `2wikimultihopqa`, or `musique`
- `decision` is `main_v1`
- `status` is `source_ready` or `ready`
- `dataset_path` is set and exists locally
- `source_snapshot_id`, `raw_data_hash`, `processed_corpus_hash`, and `split_hash` are set
- `license_note` is set
- `build_command_record` is non-empty
- `retrieval_index_path` is set and exists locally
- index manifest identity agrees with the snapshot record where comparable fields exist

If any precondition fails, the promotion command must make no tracked metadata change and must report the blockers.

## Data Flow

1. Load the snapshot registry JSON.
2. Validate registry shape using the existing snapshot registry rules.
3. For each snapshot record, resolve local dataset and index paths relative to the repository root.
4. Load the index manifest JSON for the recorded retrieval index.
5. Compare dataset id, split, source snapshot id, and corpus hash between the snapshot record and index manifest.
6. Build a readiness summary with per-dataset blockers.
7. If running in inspect mode, print JSON and make no changes.
8. If running in promote mode and blockers are empty, update snapshot statuses and sync `main_v1_readiness.yaml`.
9. Run strict snapshot readiness again. It may pass for snapshot/index readiness, but Gate 8 freeze readiness must remain blocked.

## Public Interface

Inspect-only command:

```powershell
python scripts/check_gate8_snapshot_index_promotion.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
```

Promotion command:

```powershell
python scripts/promote_gate8_snapshot_indexes.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
```

The promotion command is authorized only for local metadata updates. It must not create dataset files, index files, model outputs, run records, metric records, or result artifacts.

## Metadata Updates

After a successful Gate 8J promotion:

- `snapshots/main_v1/source_snapshots.json` should have `status: ready` for HotpotQA, 2WikiMultihopQA, and MuSiQue.
- `configs/gate8/main_v1_readiness.yaml` should copy concrete dataset path, source snapshot id, raw data hash, processed corpus hash, split hash, retrieval index path, and license note values from the snapshot registry.
- stale blockers related to dataset paths, source snapshot ids, raw hashes, processed corpus hashes, split hashes, and retrieval indexes should be removed from `not_ready`.
- blockers for provider, prompt, budget, freeze, run authorization, and reproducibility review should remain.
- `authorized_to_run` must remain `false`.

## Testing

Tests should cover:

- valid current local snapshot/index records are promotable
- missing index manifest blocks promotion
- mismatched dataset id blocks promotion
- mismatched split blocks promotion
- mismatched source snapshot id blocks promotion
- mismatched processed corpus hash blocks promotion
- promotion changes only tracked metadata files
- strict snapshot readiness passes after promotion
- strict freeze readiness still fails after promotion
- `main_v1_readiness.yaml` remains non-executable after promotion

## Success Criteria

Gate 8J is complete when:

- snapshot/index promotion checker exists
- promotion command exists
- tests pass
- snapshot records are promoted to `ready` only after local validation
- `main_v1_readiness.yaml` is synced with concrete dataset/index metadata
- stale dataset/index blockers are removed
- provider, prompt, budget, freeze, and execution blockers remain
- strict snapshot readiness passes
- strict freeze readiness still fails
- no dataset, index, model, baseline, metric, or result artifact is created by Gate 8J

## Implementation Boundary

The next implementation should be committed separately from this design. It must preserve the project rule that Gate 8 is not passed until real main baselines run on locked snapshots and produce comparable run and metric records.

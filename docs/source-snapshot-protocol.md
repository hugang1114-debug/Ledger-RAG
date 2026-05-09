# Source Snapshot Protocol

Main comparisons must run only from immutable source snapshots. No Gate 8 run may use live dataset pages, mutable working directories, ad hoc downloads, or files whose provenance cannot be replayed.

## Snapshot Record

Each dataset split used in a main comparison must have a source snapshot record with these fields:

- `source_snapshot_id`: stable id for the dataset, split, source version, processing version, and short hash prefix
- `dataset_id`: canonical dataset id used in config files
- `dataset_name`: human-readable dataset name
- `split`: split name and any subset filter
- `official_url`: official dataset page or repository used as the source
- `license_note`: local note describing the license or terms status and where it was checked
- `raw_data_hash`: SHA256 digest over the raw downloaded files or a manifest of raw file digests
- `processed_corpus_hash`: SHA256 digest over the normalized corpus records used by retrieval
- `split_hash`: SHA256 digest over ordered question ids, split metadata, and filtering rules
- `build_command_record`: exact command, script path, script version, environment note, and timestamp used to create the processed snapshot
- `storage_class`: expected local storage class: `small`, `medium`, `large`, or `unknown`
- `notes`: reproduction risks, source quirks, or evaluation-script constraints

Gate 8A stores pending main v1 records in `snapshots/main_v1/source_snapshots.json`. Pending records may use `unset` for fields that require an actual dataset snapshot, but those fields block main comparison execution.

## Hash Rules

Raw data hashing must happen before normalization. If the raw source contains multiple files, the project records a deterministic manifest containing path, byte size, and SHA256 for each file, then hashes the manifest.

Processed corpus hashing must happen after normalization and before index construction. The normalized records must be serialized in a deterministic order so the same input produces the same `processed_corpus_hash`.

Split hashing must include the ordered question ids and any sampling or filtering rule. A sampled pilot split and a full evaluation split are different snapshots.

## Build Command Record

The build command record must be sufficient for another agent to recreate the processed snapshot. It records:

- command line
- source script path
- script git commit or file hash
- input paths
- output paths
- Python or toolchain version
- timestamp in ISO 8601 format
- manual decisions made during conversion

## Execution Rule

Main comparisons may reference only `source_snapshot_id` values that resolve to complete snapshot records. If a snapshot has an unset hash, unclear license note, missing build command, or mutable source dependency, it is not eligible for Gate 8 execution.

Downloaded data files, processed corpora, indexes, and run outputs remain outside git unless explicitly approved. Git tracks the snapshot metadata and protocol, not the large data.

The local metadata check is:

```powershell
python scripts/check_gate8_snapshot_readiness.py --registry snapshots/main_v1/source_snapshots.json
```

The strict execution gate is:

```powershell
python scripts/check_gate8_snapshot_readiness.py --registry snapshots/main_v1/source_snapshots.json --require-ready
```

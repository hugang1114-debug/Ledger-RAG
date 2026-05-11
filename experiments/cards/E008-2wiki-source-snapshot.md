# E008 2WikiMultihopQA Source Snapshot

## Status

Source snapshot card. This card authorizes only the 2WikiMultihopQA dev source snapshot build from official sources. It does not authorize retrieval index builds, model calls, baseline execution, or metric comparison.

## Research Question

Can the project lock a second real `main_v1` dataset source snapshot with deterministic hashes and preserved reasoning/evidence fields before Gate 8 execution?

## Dataset

- Dataset: 2WikiMultihopQA
- Split: dev
- Official repository: https://github.com/Alab-NII/2wikimultihop
- Raw data source: `https://www.dropbox.com/s/ms2m13252h6xubs/data_ids_april7.zip?dl=1`
- Evaluation script: `https://raw.githubusercontent.com/Alab-NII/2wikimultihop/main/2wikimultihop_evaluate_v1.1.py`
- License note: Apache-2.0 per official repository LICENSE

If the official raw data source is unavailable, do not use mirrors. Leave the registry record pending and keep the official-source blocker visible.

## Command

```powershell
python scripts/build_2wiki_source_snapshot.py --registry snapshots/main_v1/source_snapshots.json --output-root datasets/source_snapshots --split dev
```

## Expected Outputs

Ignored local dataset artifacts:

- `datasets/source_snapshots/2wikimultihopqa/dev/raw_manifest.json`
- `datasets/source_snapshots/2wikimultihopqa/dev/processed/corpus.jsonl`
- `datasets/source_snapshots/2wikimultihopqa/dev/processed/questions.jsonl`
- `datasets/source_snapshots/2wikimultihopqa/dev/processed/split_manifest.json`
- `datasets/source_snapshots/2wikimultihopqa/dev/snapshot_record.json`

Tracked metadata:

- `snapshots/main_v1/source_snapshots.json`

## Failure Criteria

This step fails if it uses a non-official mirror, marks Gate 8 as ready, builds a retrieval index, runs a model, drops `evidences_id` or `answer_id`, or changes any non-2WikiMultihopQA registry record.

## Expected Cost Class

Local storage and CPU only. No model/API cost.

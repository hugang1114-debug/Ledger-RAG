# E007 HotpotQA Source Snapshot

## Status

Source snapshot card. This card authorizes only the HotpotQA dev distractor source snapshot build from official sources. It does not authorize retrieval index builds, model calls, baseline execution, or metric comparison.

## Research Question

Can the project lock one real `main_v1` dataset source snapshot with deterministic hashes and replayable processed files before Gate 8 execution?

## Dataset

- Dataset: HotpotQA
- Split: dev distractor
- Official homepage: https://hotpotqa.github.io/
- Raw data source: `http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json`
- License note: CC BY-SA 4.0 per official HotpotQA homepage

If the official raw data source is unavailable, do not use mirrors. Leave the registry record pending and keep the official-source blocker visible.

## Command

```powershell
python scripts/build_hotpotqa_source_snapshot.py --registry snapshots/main_v1/source_snapshots.json --output-root datasets/source_snapshots --split dev_distractor
```

## Expected Outputs

Ignored local dataset artifacts:

- `datasets/source_snapshots/hotpotqa/dev_distractor/raw_manifest.json`
- `datasets/source_snapshots/hotpotqa/dev_distractor/processed/corpus.jsonl`
- `datasets/source_snapshots/hotpotqa/dev_distractor/processed/questions.jsonl`
- `datasets/source_snapshots/hotpotqa/dev_distractor/processed/split_manifest.json`
- `datasets/source_snapshots/hotpotqa/dev_distractor/snapshot_record.json`

Tracked metadata:

- `snapshots/main_v1/source_snapshots.json`

## Failure Criteria

This step fails if it uses a non-official mirror, marks Gate 8 as ready, builds a retrieval index, runs a model, or changes any non-HotpotQA registry record.

## Expected Cost Class

Local storage and CPU only. No model/API cost.

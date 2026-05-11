# E009 MuSiQue Source Snapshot

## Purpose

Lock the MuSiQue answerable dev split as a Gate 8 source snapshot from official sources only. This is a source preparation step, not a baseline run and not a paper result.

## Dataset And License

- dataset: MuSiQue
- split: dev
- variant: MuSiQue-Answerable
- official repository: https://github.com/StonyBrookNLP/musique
- official raw data file: https://drive.google.com/uc?export=download&id=1tGdADlNjWFaHLeZZGShh2IRcpO6Lv24h
- official evaluation script: https://raw.githubusercontent.com/StonyBrookNLP/musique/main/evaluate_v1.0.py
- license source: https://raw.githubusercontent.com/StonyBrookNLP/musique/main/LICENSE
- license note: CC BY 4.0 per the official StonyBrookNLP/MuSiQue repository

If the official Google Drive or GitHub sources are unreachable, this card does not authorize mirrors or alternate uploads.

## Authorized Command

```powershell
python scripts/build_musique_source_snapshot.py --registry snapshots/main_v1/source_snapshots.json --output-root datasets/source_snapshots --split dev
```

## Expected Outputs

- ignored local data under `datasets/source_snapshots/musique/dev/`
- tracked registry update for only the `musique` entry in `snapshots/main_v1/source_snapshots.json`
- `source_ready` status for MuSiQue only if official data, license, and provenance files are fetched or provided from official prior downloads
- `retrieval_index_path` remains `unset`

## Failure Criteria

- non-official mirror is used
- retrieval indexes are built
- model, embedding, or baseline commands are run
- question decomposition or support paragraph metadata is dropped
- non-MuSiQue registry records are changed
- Gate 8 is marked ready or passed

## Cost Class

Local CPU and storage only. No model/API/provider cost is authorized.

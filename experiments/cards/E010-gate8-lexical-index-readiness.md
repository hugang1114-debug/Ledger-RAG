# E010 Gate 8 Lexical Index Readiness

## Purpose

Build deterministic local lexical retrieval index artifacts for the three `main_v1` source-ready datasets. This card authorizes index artifact construction only.

## Authorized Datasets

- HotpotQA dev distractor
- 2WikiMultihopQA dev
- MuSiQue answerable dev

## Authorized Command

```powershell
python scripts/build_gate8_lexical_indexes.py --registry snapshots/main_v1/source_snapshots.json --index-root datasets/retrieval_indexes/main_v1
```

## Expected Outputs

- ignored index artifacts under `datasets/retrieval_indexes/main_v1/`
- tracked `retrieval_index_path` updates in `snapshots/main_v1/source_snapshots.json`
- dataset `status` remains `source_ready`
- Gate 8 strict readiness remains blocked

## Failure Criteria

- model, embedding, reranker, or provider call is made
- retrieval evaluation is run
- baseline execution is run
- source snapshot hashes are changed
- dataset status is changed to `ready`
- generated index files are staged into git

## Cost Class

Local CPU and storage only. No model/API/provider cost is authorized.

# Gate 8E Retrieval Index Readiness Design

## Purpose

Gate 8E builds local retrieval index artifacts for the three locked `main_v1` source snapshots: HotpotQA, 2WikiMultihopQA, and MuSiQue. This gate is a readiness step only. It proves that each processed corpus can be converted into a deterministic retrieval index artifact and recorded in snapshot metadata.

Gate 8E does not run retrieval evaluation, baselines, generation, verification, model calls, embedding calls, or paper-result comparisons.

## Scope

In scope:

- build one local lexical retrieval index per locked source snapshot
- use only existing processed corpora under ignored `datasets/source_snapshots/`
- store generated indexes under ignored `datasets/retrieval_indexes/main_v1/`
- update `snapshots/main_v1/source_snapshots.json` only to set `retrieval_index_path`
- keep each dataset status as `source_ready`
- keep Gate 8 strict readiness failing until later gates explicitly mark snapshots ready
- add tests that prove deterministic index construction and safe registry updates

Out of scope:

- dense embeddings
- hybrid retrieval
- rerankers
- retrieval quality evaluation
- baseline runs
- model/provider selection
- cost budget approval
- prompt or generation config freeze
- changing source snapshot hashes

## Recommended Approach

Use a standard-library-only lexical index builder. The builder tokenizes corpus text deterministically, records document metadata, and writes a compact inverted index with document frequency and term frequency data.

This approach is intentionally conservative. It clears the concrete `retrieval_index_path` blocker without introducing embedding providers, vector databases, GPU dependencies, or model cost. Dense and hybrid retrieval remain protocol-defined baselines, but their executable implementation belongs in a later provider/config gate.

## Public Interfaces

Main command:

```powershell
python scripts/build_gate8_lexical_indexes.py --registry snapshots/main_v1/source_snapshots.json --index-root datasets/retrieval_indexes/main_v1
```

Optional single-dataset command:

```powershell
python scripts/build_gate8_lexical_indexes.py --registry snapshots/main_v1/source_snapshots.json --index-root datasets/retrieval_indexes/main_v1 --dataset hotpotqa
```

The command must refuse records that are not `source_ready` or that have missing `dataset_path`, `source_snapshot_id`, or `processed_corpus_hash`.

## Artifact Shape

Each dataset index directory is:

```text
datasets/retrieval_indexes/main_v1/<dataset_id>/<split>/
```

Required files:

- `documents.jsonl`
- `postings.jsonl`
- `index_manifest.json`

`documents.jsonl` records:

- `internal_doc_id`
- `source_doc_id`
- `source_uri`
- `title`
- `source_hash`
- `text_hash`
- `token_count`

`postings.jsonl` records:

- `token`
- `document_frequency`
- `total_term_frequency`
- `postings`

Each posting contains:

- `internal_doc_id`
- `term_frequency`

`index_manifest.json` records:

- `dataset_id`
- `split`
- `source_snapshot_id`
- `processed_corpus_hash`
- `retriever_family: lexical`
- `tokenizer_version`
- `document_count`
- `term_count`
- `documents_hash`
- `postings_hash`
- `index_hash`
- `build_command_record`

## Data Flow

1. Load the source snapshot registry.
2. Select all main v1 records or one requested dataset.
3. Validate each selected record is `source_ready`.
4. Read `<dataset_path>/processed/corpus.jsonl`.
5. Normalize and tokenize each corpus row deterministically.
6. Write sorted document rows.
7. Write sorted posting rows.
8. Hash document rows and posting rows.
9. Write `index_manifest.json`.
10. Update only `retrieval_index_path` for the selected registry records.

No source snapshot field other than `retrieval_index_path` is changed.

## Error Handling

The builder exits nonzero when:

- the registry is missing or invalid
- a selected dataset id is unknown
- a selected record is not `source_ready`
- `dataset_path` is unset or missing
- the processed `corpus.jsonl` file is missing
- the processed corpus hash in the registry does not match the current corpus file hash rule
- an index write fails

The command must not partially mark a registry record with a path unless its index manifest was successfully written.

## Readiness Semantics

After successful Gate 8E execution:

- `source_ready_count` remains `3`
- `retrieval_index_path` is set for HotpotQA, 2WikiMultihopQA, and MuSiQue
- strict Gate 8 readiness still fails because each snapshot `status` remains `source_ready`, not `ready`
- later gates must handle model/provider selection, prompt/config freeze, budget approval, reproducibility review, and final status promotion

## Tests

Add tests for:

- deterministic tokenization
- deterministic index output and hashes across repeated builds
- index manifest contains source snapshot id and processed corpus hash
- registry update changes only `retrieval_index_path`
- CLI builds from a fixture registry and fixture corpus
- CLI refuses unknown datasets
- strict readiness still fails after index paths are set because status is not `ready`

Run the existing Gate 7 and Gate 8 source snapshot test set after implementation.

## Documentation Updates

Update:

- `README.md`
- `docs/main-comparison-readiness.md`
- `docs/source-snapshot-protocol.md`
- `configs/gate8/main_v1_readiness.yaml`
- add `experiments/cards/E010-gate8-lexical-index-readiness.md`

The experiment card must state that Gate 8E is allowed to build local lexical index artifacts only and does not authorize retrieval evaluation or baseline runs.

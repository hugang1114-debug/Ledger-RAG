# Citation Pointer Schema

## Pointer Format

Canonical citation pointer:

```text
dataset_id/source_id/snapshot_hash/span_id/span_hash
```

Example:

```text
hotpotqa/doc_yoruba/78487b5e57e5423c/sent_0003/9b3a...
```

Each field must be slash-safe and non-empty. The model may emit this string, but the audit layer must not trust it until deterministic validation completes.

## Field Semantics

| Field | Meaning | Validation |
|---|---|---|
| `dataset_id` | Dataset or corpus namespace | Must match a known dataset in the run ledger. |
| `source_id` | Stable source document ID | Source existence check. |
| `snapshot_hash` | Hash or stable prefix for the source snapshot | Snapshot replay check and drift detection. |
| `span_id` | Stable span identifier independent of retrieval position | Span existence check. |
| `span_hash` | Hash of normalized span text | Span hash consistency check. |

## Required Checks

1. Malformed citation ID: pointer does not have five non-empty fields.
2. Source existence check: `dataset_id/source_id` exists in the ledger.
3. Span existence check: `span_id` exists for the source.
4. Snapshot replay check: the pointer snapshot hash matches the ledger span snapshot.
5. Span hash consistency check: normalized span text hashes to `span_hash`.
6. Retrieved-evidence membership check: the pointer belongs to evidence retrieved for this question/run.
7. Semantic support check: the claim is evaluated against the cited span after structural validation.

## Validation Categories

- `valid_citation`
- `nonexistent_citation_id`
- `citation_id_not_in_retrieved_evidence`
- `wrong_snapshot_hash`
- `wrong_span_hash`
- `malformed_citation_id`
- `structurally_valid_but_semantically_unsupported_citation`
- `overclaim_partially_supported_claim`

## Structural vs Semantic Validity

Structural validation is deterministic and must not rely on model self-reporting. It answers whether a citation pointer is well formed, resolves to a ledger span, matches hashes, and belongs to the retrieved evidence.

Semantic support is a separate claim-to-span judgment. A citation can be structurally valid but semantically unsupported, contradictory, or only partially supportive.

## Minimal Implementation

The standard-library implementation lives in `src/ledger_rag_attribution/pointers.py`. It provides:

- `EvidenceSpan`
- `CitationPointer`
- `compute_span_hash`
- `build_citation_id`
- `validate_citation`

The module is intentionally small. It is a deterministic audit primitive, not a full retriever or verifier.

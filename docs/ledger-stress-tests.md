# Ledger-Specific Stress Tests

These tests should run before scaling any paper-grade evaluation.

## 1. Invalid-ID Injection

Inject fake citation IDs into otherwise valid model outputs.

Expected behavior:

- malformed pointers are labeled `malformed_citation_id`
- nonexistent source or span IDs are labeled `nonexistent_citation_id`
- citations outside retrieved evidence are labeled `citation_id_not_in_retrieved_evidence`
- invalid IDs are rejected, sanitized, or explicitly counted

Minimal executable coverage: `tests/test_ledger_stress_designs.py::test_invalid_id_injection_is_caught_deterministically`

## 2. Re-Chunking Stability

Change chunk boundaries or retrieval positions while preserving a stable span ID and span text.

Expected behavior:

- old pointers still replay if `source_id`, `snapshot_hash`, `span_id`, and `span_hash` match
- retrieval position changes do not invalidate the pointer
- span text changes trigger `wrong_span_hash`

Minimal executable coverage: `tests/test_ledger_stress_designs.py::test_rechunking_stability_uses_stable_span_identifier_not_position`

## 3. Source Version Drift

Modify the source snapshot after citations have been created.

Expected behavior:

- old citations replay only against the old snapshot
- new snapshots with changed text cannot satisfy old pointers
- mismatched snapshots are labeled `wrong_snapshot_hash`

Minimal executable coverage: `tests/test_ledger_stress_designs.py::test_source_version_drift_requires_old_snapshot_hash_for_replay`

## 4. Evidence Position Shift

Move supporting evidence to different context positions.

Expected behavior:

- attribution validity depends on pointer identity and span hash, not context rank
- semantic support should remain stable when the same span is cited

Minimal executable coverage: `tests/test_ledger_stress_designs.py::test_evidence_position_shift_does_not_change_pointer_validity`

## 5. Conflicting Evidence

Provide contradictory spans that are structurally valid.

Expected behavior:

- deterministic validation accepts structurally valid pointers
- semantic verifier labels contradiction or unsupported support separately
- overclaim and cherry-picking errors are counted instead of hidden

Minimal executable coverage: `tests/test_ledger_stress_designs.py::test_conflicting_evidence_can_be_structurally_valid_but_semantically_unsupported`

## Reporting

Stress-test reports should include counts by validation status, semantic label, refusal label, cost per audited claim, and latency per audited claim.

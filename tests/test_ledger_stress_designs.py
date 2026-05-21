from ledger_rag_attribution.pointers import (
    EvidenceSpan,
    PointerValidationStatus,
    build_citation_id,
    validate_citation,
)


def test_invalid_id_injection_is_caught_deterministically():
    span = EvidenceSpan("hotpotqa", "doc1", "snapA", "stable_fact", "A supported fact.")

    result = validate_citation(
        "hotpotqa/doc1/snapA/fake_span/fake_hash",
        ledger_spans=[span],
        retrieved_citation_ids={"hotpotqa/doc1/snapA/fake_span/fake_hash"},
    )

    assert result.status == PointerValidationStatus.NONEXISTENT_CITATION_ID


def test_rechunking_stability_uses_stable_span_identifier_not_position():
    old_span = EvidenceSpan("hotpotqa", "doc1", "snapA", "stable_fact", "A supported fact.", position=0)
    rechunked_span = EvidenceSpan("hotpotqa", "doc1", "snapA", "stable_fact", "A supported fact.", position=12)
    citation_id = build_citation_id(old_span)

    result = validate_citation(
        citation_id,
        ledger_spans=[rechunked_span],
        retrieved_citation_ids={citation_id},
        semantic_label="entailed",
    )

    assert result.status == PointerValidationStatus.VALID


def test_source_version_drift_requires_old_snapshot_hash_for_replay():
    old_span = EvidenceSpan("hotpotqa", "doc1", "snapA", "stable_fact", "Old wording.")
    new_span = EvidenceSpan("hotpotqa", "doc1", "snapB", "stable_fact", "New wording.")
    old_citation_id = build_citation_id(old_span)

    result = validate_citation(
        old_citation_id,
        ledger_spans=[new_span],
        retrieved_citation_ids={old_citation_id},
    )

    assert result.status == PointerValidationStatus.WRONG_SNAPSHOT_HASH


def test_evidence_position_shift_does_not_change_pointer_validity():
    span = EvidenceSpan("hotpotqa", "doc1", "snapA", "stable_fact", "A supported fact.", position=99)
    citation_id = build_citation_id(span)

    result = validate_citation(
        citation_id,
        ledger_spans=[span],
        retrieved_citation_ids={citation_id},
        semantic_label="entailed",
    )

    assert result.status == PointerValidationStatus.VALID


def test_conflicting_evidence_can_be_structurally_valid_but_semantically_unsupported():
    span = EvidenceSpan("hotpotqa", "doc_conflict", "snapA", "conflict_fact", "The answer is not Yoruba people.")
    citation_id = build_citation_id(span)

    result = validate_citation(
        citation_id,
        ledger_spans=[span],
        retrieved_citation_ids={citation_id},
        semantic_label="contradictory",
    )

    assert result.structurally_valid is True
    assert result.status == PointerValidationStatus.SEMANTICALLY_UNSUPPORTED

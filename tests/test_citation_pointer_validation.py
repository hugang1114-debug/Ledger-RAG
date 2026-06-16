import pytest

from ledger_rag_attribution.pointers import (
    EvidenceSpan,
    PointerValidationStatus,
    build_citation_id,
    compute_span_hash,
    validate_citation,
)


def _span(span_id="s1", text="The Ida is a sword used by the Yoruba people."):
    return EvidenceSpan(
        dataset_id="hotpotqa",
        source_id="doc_yoruba",
        snapshot_hash="snap123",
        span_id=span_id,
        text=text,
    )


def test_validates_citation_pointer_against_ledger_and_retrieved_evidence():
    span = _span()
    citation_id = build_citation_id(span)

    result = validate_citation(
        citation_id,
        ledger_spans=[span],
        retrieved_citation_ids={citation_id},
        semantic_label="entailed",
    )

    assert result.status == PointerValidationStatus.VALID
    assert result.structurally_valid is True
    assert result.semantic_status == "entailed"


def test_rejects_malformed_pointer_before_ledger_lookup():
    result = validate_citation(
        "not/a/full/pointer",
        ledger_spans=[_span()],
        retrieved_citation_ids=set(),
    )

    assert result.status == PointerValidationStatus.MALFORMED_CITATION_ID
    assert result.structurally_valid is False


def test_reports_nonexistent_source_or_span_separately_from_retrieval_membership():
    span = _span()
    missing_source_id = "hotpotqa/doc_missing/snap123/s1/" + compute_span_hash(span.text)
    missing_span_id = "hotpotqa/doc_yoruba/snap123/s999/" + compute_span_hash(span.text)

    missing_source = validate_citation(
        missing_source_id,
        ledger_spans=[span],
        retrieved_citation_ids={missing_source_id},
    )
    missing_span = validate_citation(
        missing_span_id,
        ledger_spans=[span],
        retrieved_citation_ids={missing_span_id},
    )

    assert missing_source.status == PointerValidationStatus.NONEXISTENT_CITATION_ID
    assert missing_source.details["missing"] == "source"
    assert missing_span.status == PointerValidationStatus.NONEXISTENT_CITATION_ID
    assert missing_span.details["missing"] == "span"


def test_reports_not_retrieved_only_after_pointer_resolves():
    span = _span()
    citation_id = build_citation_id(span)

    result = validate_citation(
        citation_id,
        ledger_spans=[span],
        retrieved_citation_ids=set(),
    )

    assert result.status == PointerValidationStatus.CITATION_ID_NOT_IN_RETRIEVED_EVIDENCE
    assert result.structurally_valid is False


def test_reports_snapshot_and_span_hash_mismatches():
    span = _span()
    right_hash = compute_span_hash(span.text)
    wrong_snapshot = f"hotpotqa/doc_yoruba/wrongsnap/s1/{right_hash}"
    wrong_span_hash = "hotpotqa/doc_yoruba/snap123/s1/badspanhash"

    snapshot_result = validate_citation(
        wrong_snapshot,
        ledger_spans=[span],
        retrieved_citation_ids={wrong_snapshot},
    )
    hash_result = validate_citation(
        wrong_span_hash,
        ledger_spans=[span],
        retrieved_citation_ids={wrong_span_hash},
    )

    assert snapshot_result.status == PointerValidationStatus.WRONG_SNAPSHOT_HASH
    assert hash_result.status == PointerValidationStatus.WRONG_SPAN_HASH


@pytest.mark.parametrize(
    ("semantic_label", "expected"),
    [
        ("unsupported", PointerValidationStatus.SEMANTICALLY_UNSUPPORTED),
        ("contradictory", PointerValidationStatus.SEMANTICALLY_UNSUPPORTED),
        ("partially_supported", PointerValidationStatus.OVERCLAIM_PARTIALLY_SUPPORTED),
    ],
)
def test_structurally_valid_pointer_can_have_separate_semantic_failure_status(semantic_label, expected):
    span = _span()
    citation_id = build_citation_id(span)

    result = validate_citation(
        citation_id,
        ledger_spans=[span],
        retrieved_citation_ids={citation_id},
        semantic_label=semantic_label,
    )

    assert result.status == expected
    assert result.structurally_valid is True
    assert result.semantic_status == semantic_label

from ledger_rag_attribution.pointers import EvidenceSpan, build_citation_id, validate_citation, validation_record
from ledger_rag_attribution.semantic import evaluate_claim_span, semantic_support_records, summarize_semantic_support


def test_evaluates_entailed_claim_span_pair():
    result = evaluate_claim_span(
        "The Ida is used by Yoruba people.",
        "The Ida is a sword used by the Yoruba people of West Africa.",
    )

    assert result["status"] == "evaluated"
    assert result["verdict"] == "entailed"
    assert result["confidence"] > 0
    assert "Yoruba people" in result["evidence_excerpt"]


def test_evaluates_unsupported_claim_span_pair():
    result = evaluate_claim_span(
        "The Ida is used by Finnish sailors.",
        "The Ida is a sword used by the Yoruba people of West Africa.",
    )

    assert result["status"] == "evaluated"
    assert result["verdict"] == "unsupported"


def test_evaluates_partially_supported_claim_span_pair():
    result = evaluate_claim_span(
        "The Ida is a ceremonial sword used by Yoruba people.",
        "The Ida is a sword used by the Yoruba people of West Africa.",
    )

    assert result["status"] == "evaluated"
    assert result["verdict"] == "partially_supported"


def test_structurally_invalid_citation_skips_semantic_evaluation():
    invalid = {
        "claim_id": "c1",
        "citation_id": "bad",
        "structural_validity": "invalid",
        "validation_error": "malformed_citation_id",
    }

    records = semantic_support_records(
        claims_by_id={"c1": "The Ida is used by Yoruba people."},
        validation_records=[invalid],
        span_text_by_citation_id={},
    )

    assert records[0]["status"] == "skipped"
    assert records[0]["verdict"] == "insufficient_evidence"
    assert "structural validation failed" in records[0]["rationale"]


def test_semantic_summary_counts_verdict_rates():
    records = [
        {"status": "evaluated", "verdict": "entailed"},
        {"status": "evaluated", "verdict": "unsupported"},
        {"status": "evaluated", "verdict": "partially_supported"},
        {"status": "evaluated", "verdict": "contradictory"},
        {"status": "skipped", "verdict": "insufficient_evidence"},
    ]

    summary = summarize_semantic_support(records)

    assert summary["entailment_support_rate"] == 0.2
    assert summary["unsupported_citation_rate"] == 0.2
    assert summary["partially_supported_rate"] == 0.2
    assert summary["contradictory_rate"] == 0.2
    assert summary["semantic_evaluation_skip_rate"] == 0.2


def test_semantic_support_records_resolve_valid_citation_text():
    span = EvidenceSpan("hotpotqa", "doc_yoruba", "snap123", "s1", "The Ida is used by Yoruba people.")
    citation_id = build_citation_id(span)
    validation = validation_record(
        validate_citation(citation_id, ledger_spans=[span], retrieved_citation_ids={citation_id}),
        claim_id="c1",
    )

    records = semantic_support_records(
        claims_by_id={"c1": "The Ida is used by Yoruba people."},
        validation_records=[validation],
        span_text_by_citation_id={citation_id: span.text},
    )

    assert records[0]["status"] == "evaluated"
    assert records[0]["verdict"] == "entailed"

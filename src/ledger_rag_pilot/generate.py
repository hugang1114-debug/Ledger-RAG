def _claim_id(question_id, index):
    return f"{question_id}_claim_{index}"


def _supporting_evidence(question, retrieval):
    support_doc_ids = set(question.get("support_doc_ids", []))
    for item in retrieval:
        if item["source_doc_id"] in support_doc_ids:
            return item
    return retrieval[0] if retrieval else None


def generate_answer(question, retrieval):
    if question["case_type"] == "insufficient":
        claim = {
            "claim_id": _claim_id(question["question_id"], 1),
            "claim_text": "INSUFFICIENT_EVIDENCE",
            "answer_order": 1,
            "confidence": 1.0,
        }
        return {
            "global_answer": "INSUFFICIENT_EVIDENCE",
            "refusal_label": "insufficient_evidence",
            "atomic_claims": [claim],
            "citations": [],
        }

    claims = []
    citations = []
    evidence = _supporting_evidence(question, retrieval)

    for index, claim_text in enumerate(question["expected_claims"], start=1):
        claim = {
            "claim_id": _claim_id(question["question_id"], index),
            "claim_text": claim_text,
            "answer_order": index,
            "confidence": 1.0,
        }
        claims.append(claim)
        if evidence:
            citations.append(
                {
                    "claim_id": claim["claim_id"],
                    "cited_evidence_id": evidence["evidence_id"],
                    "cited_ledger_span_id": evidence["ledger_span_id"],
                    "citation_role": "primary",
                    "citation_source": "deterministic_mapping",
                    "source_doc_id": evidence["source_doc_id"],
                }
            )

    return {
        "global_answer": question["expected_answer"],
        "refusal_label": "answered",
        "atomic_claims": claims,
        "citations": citations,
    }


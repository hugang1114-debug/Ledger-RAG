def verify_answer(question, answer, retrieval):
    if answer["refusal_label"] == "insufficient_evidence":
        return [
            {
                "claim_id": claim["claim_id"],
                "verifier_enabled": True,
                "label": "insufficient",
                "score": 1.0,
                "verifier_name": "offline_fixture_verifier",
                "rationale": "fixture marks this question as insufficient evidence",
            }
            for claim in answer["atomic_claims"]
        ]

    support_doc_ids = set(question.get("support_doc_ids", []))
    citations_by_claim = {citation["claim_id"]: citation for citation in answer["citations"]}
    verdicts = []

    for claim in answer["atomic_claims"]:
        citation = citations_by_claim.get(claim["claim_id"])
        supported = (
            claim["claim_text"] in question.get("expected_claims", [])
            and citation is not None
            and citation["source_doc_id"] in support_doc_ids
        )
        verdicts.append(
            {
                "claim_id": claim["claim_id"],
                "verifier_enabled": True,
                "label": "support" if supported else "insufficient",
                "score": 1.0 if supported else 0.0,
                "verifier_name": "offline_fixture_verifier",
                "rationale": "claim matches fixture support mapping" if supported else "claim lacks fixture support mapping",
            }
        )

    return verdicts


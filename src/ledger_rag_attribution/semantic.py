import re


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "was",
    "were",
    "with",
}

NEGATIONS = {"no", "not", "never", "none", "without"}
EVALUATOR_NAME = "local_deterministic_claim_span_heuristic_v1"


def _tokens(text):
    return [
        token
        for token in re.findall(r"[a-z0-9]+", str(text).lower())
        if token not in STOPWORDS
    ]


def _excerpt(text, limit=240):
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def evaluate_claim_span(claim_text, span_text):
    claim_tokens = set(_tokens(claim_text))
    span_tokens = set(_tokens(span_text))
    if not claim_tokens or not span_tokens:
        return {
            "status": "evaluated",
            "verdict": "insufficient_evidence",
            "evidence_excerpt": _excerpt(span_text),
            "rationale": "claim or cited span has no comparable content tokens",
            "confidence": 0.0,
            "evaluator_name": EVALUATOR_NAME,
        }

    overlap = claim_tokens & span_tokens
    overlap_ratio = len(overlap) / max(len(claim_tokens), 1)
    claim_has_negation = bool(claim_tokens & NEGATIONS)
    span_has_negation = bool(span_tokens & NEGATIONS)
    non_negation_overlap = bool((claim_tokens - NEGATIONS) & (span_tokens - NEGATIONS))

    if claim_has_negation != span_has_negation and non_negation_overlap and overlap_ratio >= 0.5:
        verdict = "contradictory"
        rationale = "claim and cited span share content but differ on explicit negation"
        confidence = round(overlap_ratio, 6)
    elif claim_tokens <= span_tokens:
        verdict = "entailed"
        rationale = "all claim content tokens appear in the cited span"
        confidence = 1.0
    elif overlap_ratio >= 0.65:
        verdict = "partially_supported"
        rationale = "most claim content appears in the cited span, but some claim content is missing"
        confidence = round(overlap_ratio, 6)
    else:
        verdict = "unsupported"
        rationale = "too little claim content is supported by the cited span"
        confidence = round(overlap_ratio, 6)

    return {
        "status": "evaluated",
        "verdict": verdict,
        "evidence_excerpt": _excerpt(span_text),
        "rationale": rationale,
        "confidence": confidence,
        "evaluator_name": EVALUATOR_NAME,
    }


def semantic_support_records(claims_by_id, validation_records, span_text_by_citation_id):
    records = []
    for validation in validation_records:
        claim_id = validation.get("claim_id", "")
        citation_id = validation.get("citation_id", "")
        if validation.get("structural_validity") != "valid":
            records.append(
                {
                    "claim_id": claim_id,
                    "citation_id": citation_id,
                    "status": "skipped",
                    "verdict": "insufficient_evidence",
                    "evidence_excerpt": "",
                    "rationale": f"structural validation failed: {validation.get('validation_error', 'unknown')}",
                    "confidence": 0.0,
                    "evaluator_name": EVALUATOR_NAME,
                }
            )
            continue
        span_text = span_text_by_citation_id.get(citation_id)
        if span_text is None:
            records.append(
                {
                    "claim_id": claim_id,
                    "citation_id": citation_id,
                    "status": "error",
                    "verdict": "insufficient_evidence",
                    "evidence_excerpt": "",
                    "rationale": "structurally valid citation could not be resolved to span text",
                    "confidence": 0.0,
                    "evaluator_name": EVALUATOR_NAME,
                }
            )
            continue
        evaluated = evaluate_claim_span(claims_by_id.get(claim_id, ""), span_text)
        evaluated.update({"claim_id": claim_id, "citation_id": citation_id})
        records.append(evaluated)
    return records


def summarize_semantic_support(records):
    total = len(records)
    counts = {
        "entailed": 0,
        "unsupported": 0,
        "partially_supported": 0,
        "contradictory": 0,
        "skipped": 0,
        "error": 0,
    }
    for record in records:
        if record.get("status") == "skipped":
            counts["skipped"] += 1
        elif record.get("status") == "error":
            counts["error"] += 1
        verdict = record.get("verdict")
        if verdict in counts:
            counts[verdict] += 1

    def rate(value):
        return round(value / total, 6) if total else 0.0

    return {
        "semantic_evaluator_name": EVALUATOR_NAME,
        "semantic_evaluation_count": total,
        "entailment_support_rate": rate(counts["entailed"]),
        "unsupported_citation_rate": rate(counts["unsupported"]),
        "partially_supported_rate": rate(counts["partially_supported"]),
        "contradictory_rate": rate(counts["contradictory"]),
        "semantic_evaluation_skip_rate": rate(counts["skipped"]),
        "semantic_evaluation_error_rate": rate(counts["error"]),
    }

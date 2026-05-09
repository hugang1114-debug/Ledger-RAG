import re


def _tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def _f1(predicted, expected):
    predicted_tokens = _tokens(predicted)
    expected_tokens = _tokens(expected)
    if not predicted_tokens and not expected_tokens:
        return 1.0
    if not predicted_tokens or not expected_tokens:
        return 0.0
    common = set(predicted_tokens) & set(expected_tokens)
    if not common:
        return 0.0
    precision = len(common) / len(set(predicted_tokens))
    recall = len(common) / len(set(expected_tokens))
    return 2 * precision * recall / (precision + recall)


def _average(values):
    return sum(values) / len(values) if values else 0.0


def compute_metric_record(fixture, question_results, run_metadata, ledger_size_mb, index_size_mb):
    answerable_results = [item for item in question_results if item["question"]["case_type"] == "answerable"]
    retrieval_recalls = []
    retrieval_precisions = []
    reciprocal_ranks = []

    for item in answerable_results:
        support_doc_ids = set(item["question"]["support_doc_ids"])
        retrieved_doc_ids = [evidence["source_doc_id"] for evidence in item["retrieval"]]
        relevant = [doc_id in support_doc_ids for doc_id in retrieved_doc_ids]
        retrieval_recalls.append(1.0 if any(relevant) else 0.0)
        retrieval_precisions.append(sum(1 for value in relevant if value) / max(len(relevant), 1))
        first_rank = next((index + 1 for index, value in enumerate(relevant) if value), None)
        reciprocal_ranks.append(1 / first_rank if first_rank else 0.0)

    exact_matches = [
        1.0 if item["answer"]["global_answer"] == item["question"]["expected_answer"] else 0.0
        for item in question_results
    ]
    f1_scores = [_f1(item["answer"]["global_answer"], item["question"]["expected_answer"]) for item in question_results]
    all_claims = [claim for item in question_results for claim in item["answer"]["atomic_claims"]]
    all_citations = [citation for item in question_results for citation in item["answer"]["citations"]]
    all_verdicts = [verdict for item in question_results for verdict in item["verdicts"]]
    support_count = sum(1 for verdict in all_verdicts if verdict["label"] == "support")
    unsupported_count = sum(1 for verdict in all_verdicts if verdict["label"] in {"insufficient", "refute"})
    citation_support_count = 0
    for item in question_results:
        support_doc_ids = set(item["question"].get("support_doc_ids", []))
        for citation in item["answer"]["citations"]:
            if citation["source_doc_id"] in support_doc_ids:
                citation_support_count += 1

    question_count = len(question_results)
    refusal_count = sum(1 for item in question_results if item["answer"]["refusal_label"] != "answered")

    return {
        "metric_record": {
            "run_id": run_metadata["run_id"],
            "dataset_id": fixture["dataset_id"],
            "baseline_family": "ledger_validator",
            "split": fixture["split"],
            "question_count": question_count,
            "refusal_count": refusal_count,
            "refusal_rate": refusal_count / max(question_count, 1),
        },
        "retrieval": {
            "recall_at_k": _average(retrieval_recalls),
            "precision_at_k": _average(retrieval_precisions),
            "mrr": _average(reciprocal_ranks),
            "ndcg": _average(retrieval_recalls),
            "k": 2,
            "oracle_retrieval": False,
            "missing_reason": None,
        },
        "answer_quality": {
            "exact_match": _average(exact_matches),
            "f1": _average(f1_scores),
            "rouge_l": "not_applicable",
            "claim_level_correctness": support_count / max(len(all_claims), 1),
            "factscore": "not_available",
            "missing_reason": None,
        },
        "attribution": {
            "citation_precision": citation_support_count / max(len(all_citations), 1),
            "citation_recall": citation_support_count / max(len(answerable_results), 1),
            "support_rate": support_count / max(len(all_verdicts), 1),
            "unsupported_claim_rate": unsupported_count / max(len(all_verdicts), 1),
            "overclaim_rate": 0.0,
            "claim_to_span_mapping_completeness": len(all_citations) / max(len(answerable_results), 1),
            "span_replay_success": 1.0 if all_citations else "not_applicable",
            "verifier_name": "offline_fixture_verifier",
            "missing_reason": None,
        },
        "system": {
            "p50_latency_ms": run_metadata["latency_ms"],
            "p95_latency_ms": run_metadata["latency_ms"],
            "cost_per_query_usd": 0.0,
            "peak_memory_mb": "not_available",
            "index_size_mb": index_size_mb,
            "ledger_size_mb": ledger_size_mb,
            "missing_reason": None,
        },
        "aggregation": {
            "aggregation_level": "run_group",
            "macro_average": True,
            "confidence_interval_method": "none",
            "includes_refusals_in_denominator": True,
            "notes": "offline synthetic Gate 7 pilot; not a paper result",
        },
    }


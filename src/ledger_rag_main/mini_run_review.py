import json
from collections import defaultdict
from pathlib import Path


def _read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def _safe_rate(numerator, denominator):
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 6)


def _questions_by_id(questions_path):
    rows = _read_jsonl(questions_path)
    return {row["question_id"]: row for row in rows}


def _support_docs(question):
    return {ref["source_doc_id"] for ref in question.get("support_evidence_refs", []) if ref.get("source_doc_id")}


def _record_stats(record, questions):
    question = questions.get(record["input"]["question_id"], {})
    support_docs = _support_docs(question)
    retrieved_docs = {item.get("source_doc_id") for item in record.get("retrieved_evidence", [])}
    usage = record.get("run_metadata", {}).get("usage", {})
    claims = record.get("answer", {}).get("atomic_claims", [])
    citations = record.get("citations", [])
    return {
        "support_hit": bool(support_docs & retrieved_docs),
        "refusal": record.get("answer", {}).get("refusal_label") != "answered",
        "citation_count": len(citations),
        "claim_count": len(claims),
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "estimated_cost_usd": float(record.get("run_metadata", {}).get("estimated_cost_usd") or 0),
    }


def _summarize_stats(stats):
    count = len(stats)
    support_hit_count = sum(1 for item in stats if item["support_hit"])
    refusal_count = sum(1 for item in stats if item["refusal"])
    citation_count = sum(item["citation_count"] for item in stats)
    claim_count = sum(item["claim_count"] for item in stats)
    prompt_tokens = sum(item["prompt_tokens"] for item in stats)
    completion_tokens = sum(item["completion_tokens"] for item in stats)
    estimated_cost = round(sum(item["estimated_cost_usd"] for item in stats), 6)
    return {
        "record_count": count,
        "support_hit_count": support_hit_count,
        "support_hit_rate": _safe_rate(support_hit_count, count),
        "refusal_count": refusal_count,
        "refusal_rate": _safe_rate(refusal_count, count),
        "citation_count": citation_count,
        "claim_count": claim_count,
        "claim_to_citation_rate": _safe_rate(citation_count, claim_count),
        "total_prompt_tokens": prompt_tokens,
        "total_completion_tokens": completion_tokens,
        "estimated_cost_usd": estimated_cost,
    }


def _recommendation(overall):
    if overall["support_hit_rate"] < 0.8:
        return "fix_retrieval_before_scaling"
    if overall["refusal_rate"] > 0.5:
        return "inspect_prompt_refusal_behavior_before_scaling"
    return "eligible_for_larger_mini_run"


def review_mini_run(run_dir, questions_path):
    run_dir = Path(run_dir)
    questions = _questions_by_id(questions_path)
    records = _read_jsonl(run_dir / "run_records.jsonl")
    stats = [_record_stats(record, questions) for record in records]
    by_baseline_records = defaultdict(list)
    for record, record_stats in zip(records, stats):
        by_baseline_records[record["run_metadata"]["baseline_family"]].append(record_stats)

    overall = _summarize_stats(stats)
    cost_summary = {}
    cost_path = run_dir / "cost_summary.json"
    if cost_path.is_file():
        cost_summary = json.loads(cost_path.read_text(encoding="utf-8"))
        overall["estimated_cost_usd"] = float(cost_summary.get("estimated_cost_usd", overall["estimated_cost_usd"]))

    return {
        "version": 1,
        "gate": "gate8_main_comparison",
        "stage": "gate8u_mini_run_output_review",
        "status": "completed",
        "run_dir": run_dir.as_posix(),
        "run_record_count": len(records),
        "overall": overall,
        "by_baseline": {
            baseline: _summarize_stats(baseline_stats)
            for baseline, baseline_stats in sorted(by_baseline_records.items())
        },
        "recommendation": _recommendation(overall),
        "review_notes": [
            "summary_excludes_raw_model_answers_and_raw_provider_responses",
            "support_hit_rate_uses_hotpotqa_support_doc_overlap_with_retrieved_docs",
            "mini_run_is_not_a_paper_result",
        ],
    }


def write_yaml(path, payload):
    lines = []

    def emit(prefix, value):
        if isinstance(value, dict):
            for key, child in value.items():
                lines.append(f"{prefix}{key}:")
                emit(prefix + "  ", child)
        elif isinstance(value, list):
            if not value:
                lines.append(f"{prefix}[]")
            for item in value:
                lines.append(f"{prefix}- {item}")
        else:
            lines.append(f"{prefix}{value}")

    for key, value in payload.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            emit("  ", value)
        elif isinstance(value, list):
            lines.append(f"{key}:")
            emit("  ", value)
        else:
            lines.append(f"{key}: {value}")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")

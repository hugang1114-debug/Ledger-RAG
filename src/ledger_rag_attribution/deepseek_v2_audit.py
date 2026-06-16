import csv
import json
from collections import defaultdict
from pathlib import Path

from ledger_rag_attribution.deepseek_labeler import (
    JUDGE_PROMPT_VERSION,
    label_items,
    write_labeled_outputs,
)
from ledger_rag_smoke.deepseek_smoke import MODEL_ID, post_chat_completion


SEMANTIC_VERDICTS = (
    "entailed",
    "unsupported",
    "partially_supported",
    "contradictory",
    "insufficient_evidence",
)

STRUCTURAL_METRICS = (
    "claim_count_per_answer",
    "citation_count_per_answer",
    "claim_citation_coverage",
    "answer_length",
    "refusal_rate",
    "invalid_citation_rate",
    "citation_id_validity_rate",
    "span_replay_success_rate",
    "snapshot_replay_success_rate",
    "not_in_retrieved_evidence_rate",
    "malformed_citation_rate",
    "wrong_snapshot_hash_rate",
    "wrong_span_hash_rate",
)

SEMANTIC_METRICS = (
    "entailment_support_rate",
    "unsupported_citation_rate",
    "partially_supported_rate",
    "contradictory_rate",
    "insufficient_evidence_rate",
    "semantic_evaluation_skip_rate",
)


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _claims_by_id(record):
    return {
        str(claim.get("claim_id") or ""): str(claim.get("claim_text") or claim.get("text") or "")
        for claim in record.get("answer", {}).get("atomic_claims", [])
    }


def _span_text_by_citation_id(record):
    spans = {}
    for item in record.get("retrieved_evidence", []):
        if item.get("citation_id"):
            spans[str(item["citation_id"])] = str(item.get("text") or "")
    for item in record.get("ledger_spans", []):
        if item.get("citation_id"):
            spans[str(item["citation_id"])] = str(item.get("text") or "")
    return spans


def _baseline(record):
    return str(record.get("run_metadata", {}).get("baseline_family") or "")


def build_semantic_judge_items(records):
    items = []
    for record in records:
        dataset = str(record.get("input", {}).get("dataset_id") or "")
        question_id = str(record.get("input", {}).get("question_id") or "")
        baseline = _baseline(record)
        claims = _claims_by_id(record)
        spans = _span_text_by_citation_id(record)
        valid_index = 0
        for validation in record.get("citation_validation", []):
            if validation.get("structural_validity") != "valid":
                continue
            valid_index += 1
            claim_id = str(validation.get("claim_id") or "")
            citation_id = str(validation.get("citation_id") or "")
            items.append(
                {
                    "annotation_id": f"{dataset}__{question_id}__{baseline}__{claim_id}__{valid_index}",
                    "dataset": dataset,
                    "question_id": question_id,
                    "baseline": baseline,
                    "claim_id": claim_id,
                    "claim_text": claims.get(claim_id, ""),
                    "citation_id": citation_id,
                    "cited_span_text": spans.get(citation_id, ""),
                    "structural_validity": "valid",
                    "current_semantic_verdict": "",
                    "current_semantic_confidence": "",
                    "human_label": "",
                    "human_notes": "",
                }
            )
    return items


def _labeled_by_pair(labeled_items):
    return {
        (
            str(item.get("dataset") or ""),
            str(item.get("question_id") or ""),
            str(item.get("baseline") or ""),
            str(item.get("claim_id") or ""),
            str(item.get("citation_id") or ""),
        ): item
        for item in labeled_items
    }


def apply_deepseek_v2_semantic_support(
    records,
    *,
    api_key=None,
    base_url="https://api.deepseek.com",
    post_fn=post_chat_completion,
    timeout_seconds=60,
    dry_run=False,
):
    judge_items = build_semantic_judge_items(records)
    labeled_items = label_items(
        judge_items,
        api_key=api_key,
        base_url=base_url,
        post_fn=post_fn,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
    )
    labeled = _labeled_by_pair(labeled_items)
    updated = []
    for record in records:
        copied = dict(record)
        dataset = str(copied.get("input", {}).get("dataset_id") or "")
        question_id = str(copied.get("input", {}).get("question_id") or "")
        baseline = _baseline(copied)
        records_for_claims = []
        for validation in copied.get("citation_validation", []):
            claim_id = str(validation.get("claim_id") or "")
            citation_id = str(validation.get("citation_id") or "")
            if validation.get("structural_validity") != "valid":
                records_for_claims.append(
                    {
                        "claim_id": claim_id,
                        "citation_id": citation_id,
                        "status": "skipped",
                        "verdict": "insufficient_evidence",
                        "evidence_excerpt": "",
                        "rationale": f"structural validation failed: {validation.get('validation_error', 'unknown')}",
                        "confidence": 0.0,
                        "judge_model": MODEL_ID,
                        "judge_prompt_version": JUDGE_PROMPT_VERSION,
                    }
                )
                continue
            item = labeled.get((dataset, question_id, baseline, claim_id, citation_id), {})
            records_for_claims.append(
                {
                    "claim_id": claim_id,
                    "citation_id": citation_id,
                    "status": "evaluated" if item.get("deepseek_status") == "labeled" else item.get("deepseek_status", "error"),
                    "verdict": item.get("deepseek_label") or "insufficient_evidence",
                    "evidence_excerpt": str(item.get("cited_span_text") or "")[:240],
                    "rationale": item.get("deepseek_rationale") or item.get("deepseek_error") or "",
                    "confidence": item.get("deepseek_confidence") if item.get("deepseek_confidence") != "" else 0.0,
                    "judge_model": item.get("judge_model") or MODEL_ID,
                    "judge_prompt_version": item.get("judge_prompt_version") or JUDGE_PROMPT_VERSION,
                }
            )
        copied["semantic_support"] = {
            "status": "evaluated" if records_for_claims else "pending",
            "semantic_verifier": "deepseek_v4_pro_llm_judge",
            "judge_model": MODEL_ID,
            "judge_prompt_version": JUDGE_PROMPT_VERSION,
            "records": records_for_claims,
            "summary": summarize_semantic_records(records_for_claims),
            "note": "DeepSeek judge v2 machine labels; not human gold labels or paper-grade evidence.",
        }
        updated.append(copied)
    return updated


def _rate(numerator, denominator):
    return round(numerator / denominator, 6) if denominator else 0.0


def summarize_semantic_records(records):
    total = len(records)
    counts = defaultdict(int)
    for record in records:
        if record.get("status") == "skipped":
            counts["skipped"] += 1
            continue
        counts[str(record.get("verdict") or "")] += 1
    return {
        "semantic_evaluator_name": "deepseek_v4_pro_llm_judge",
        "judge_model": MODEL_ID,
        "judge_prompt_version": JUDGE_PROMPT_VERSION,
        "semantic_evaluation_count": total,
        "entailment_support_rate": _rate(counts["entailed"], total),
        "unsupported_citation_rate": _rate(counts["unsupported"], total),
        "partially_supported_rate": _rate(counts["partially_supported"], total),
        "contradictory_rate": _rate(counts["contradictory"], total),
        "insufficient_evidence_rate": _rate(counts["insufficient_evidence"], total),
        "semantic_evaluation_skip_rate": _rate(counts["skipped"], total),
    }


def aggregate_by_baseline(records):
    by_baseline = defaultdict(list)
    for record in records:
        by_baseline[_baseline(record)].append(record)
    return {baseline: _aggregate_records(rows) for baseline, rows in sorted(by_baseline.items())}


def _aggregate_records(records):
    validations = []
    semantic_records = []
    claim_count = 0
    cited_claim_ids = set()
    answer_length_total = 0
    refusal_count = 0
    for record in records:
        validations.extend(record.get("citation_validation", []))
        semantic_records.extend(record.get("semantic_support", {}).get("records", []))
        claims = record.get("answer", {}).get("atomic_claims", [])
        claim_count += len(claims)
        for validation in record.get("citation_validation", []):
            if validation.get("structural_validity") == "valid" and validation.get("claim_id"):
                cited_claim_ids.add((id(record), str(validation.get("claim_id"))))
        answer_length_total += len(str(record.get("answer", {}).get("global_answer") or ""))
        refusal_count += record.get("answer", {}).get("refusal_label") != "answered"
    total = len(validations)
    valid = sum(1 for item in validations if item.get("structural_validity") == "valid")
    invalid = total - valid
    semantic_summary = summarize_semantic_records(semantic_records)
    record_count = len(records)
    return {
        "run_record_count": record_count,
        "claim_citation_pair_count": total,
        "claim_count": claim_count,
        "citation_count": total,
        "claim_count_per_answer": _rate(claim_count, record_count),
        "citation_count_per_answer": _rate(total, record_count),
        "claim_citation_coverage": _rate(len(cited_claim_ids), claim_count),
        "answer_length": _rate(answer_length_total, record_count),
        "refusal_rate": _rate(refusal_count, record_count),
        "valid_citation_count": valid,
        "invalid_citation_count": invalid,
        "invalid_citation_rate": _rate(invalid, total),
        "citation_id_validity_rate": _rate(valid, total),
        "span_replay_success_rate": _rate(sum(1 for item in validations if item.get("span_replay_success") is True), total),
        "snapshot_replay_success_rate": _rate(sum(1 for item in validations if item.get("snapshot_replay_success") is True), total),
        "not_in_retrieved_evidence_rate": _rate(sum(1 for item in validations if item.get("validation_error") == "not_in_retrieved_evidence"), total),
        "malformed_citation_rate": _rate(sum(1 for item in validations if item.get("validation_error") == "malformed_citation_id"), total),
        "wrong_snapshot_hash_rate": _rate(sum(1 for item in validations if item.get("validation_error") == "wrong_snapshot_hash"), total),
        "wrong_span_hash_rate": _rate(sum(1 for item in validations if item.get("validation_error") == "wrong_span_hash"), total),
        **{key: semantic_summary[key] for key in SEMANTIC_METRICS},
    }


def write_baseline_metrics_csv(table, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["baseline", "run_record_count", "claim_citation_pair_count", "claim_count", "citation_count", *STRUCTURAL_METRICS, *SEMANTIC_METRICS]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for baseline, row in table.items():
            writer.writerow({"baseline": baseline, **{field: row.get(field, "") for field in fields if field != "baseline"}})


def write_baseline_table(table, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["baseline", "run_record_count", "claim_citation_pair_count", "claim_count", "citation_count", *STRUCTURAL_METRICS, *SEMANTIC_METRICS]
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for baseline, row in table.items():
        values = [baseline]
        for field in fields[1:]:
            values.append(str(row.get(field, "")))
        lines.append("| " + " | ".join(values) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def typical_failures(records, limit=12):
    failures = []
    for record in records:
        baseline = _baseline(record)
        claims = _claims_by_id(record)
        for semantic in record.get("semantic_support", {}).get("records", []):
            if semantic.get("verdict") in {"unsupported", "contradictory", "insufficient_evidence", "partially_supported"} or semantic.get("status") == "skipped":
                failures.append(
                    {
                        "baseline": baseline,
                        "question_id": record.get("input", {}).get("question_id"),
                        "claim_id": semantic.get("claim_id"),
                        "claim_text": claims.get(str(semantic.get("claim_id") or ""), ""),
                        "citation_id": semantic.get("citation_id"),
                        "status": semantic.get("status"),
                        "verdict": semantic.get("verdict"),
                        "rationale": semantic.get("rationale"),
                    }
                )
            if len(failures) >= limit:
                return failures
    return failures


def write_judge_items(items, *, jsonl_path, csv_path):
    write_labeled_outputs(items, jsonl_path=jsonl_path, csv_path=csv_path)

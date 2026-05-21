import csv
import json
from pathlib import Path

from ledger_rag_attribution.calibration_export import ALLOWED_HUMAN_LABELS
from ledger_rag_smoke.deepseek_smoke import MODEL_ID, post_chat_completion, response_content


JUDGE_PROMPT_VERSION = "deepseek_semantic_judge_v2"

DEEPSEEK_LABEL_FIELDS = (
    "deepseek_status",
    "judge_model",
    "judge_prompt_version",
    "deepseek_label",
    "deepseek_confidence",
    "deepseek_rationale",
    "deepseek_error",
)


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def _label_definitions():
    return "\n".join(
        [
            "- entailed: the cited span directly supports the full claim.",
            "- partially_supported: the cited span supports part of the claim but not all important details.",
            "- unsupported: the cited span does not support the claim.",
            "- contradictory: the cited span conflicts with the claim.",
            "- insufficient_evidence: the cited span lacks enough information to decide.",
        ]
    )


def build_label_request(item, model_id=MODEL_ID):
    user_content = (
        "Allowed labels:\n"
        f"{_label_definitions()}\n\n"
        "Strict judging rules:\n"
        "- Use only the cited span.\n"
        "- Do not use outside knowledge.\n"
        "- Entity overlap is not support.\n"
        "- Related evidence is not entailment.\n"
        "- Use contradictory only when the span explicitly conflicts with the claim.\n"
        "- For negative claims or evidence-absence claims, prefer insufficient_evidence unless the span explicitly proves the opposite.\n"
        "- If numerical, temporal, causal, or performance claims are not explicitly supported, do not label entailed.\n"
        "- If only part of the claim is supported, label partially_supported.\n\n"
        f"Dataset: {item.get('dataset', '')}\n"
        f"Question ID: {item.get('question_id', '')}\n"
        f"Baseline: {item.get('baseline', '')}\n"
        f"Annotation ID: {item.get('annotation_id', '')}\n"
        f"Citation ID: {item.get('citation_id', '')}\n\n"
        "Claim:\n"
        f"{item.get('claim_text', '')}\n\n"
        "Cited span:\n"
        f"{item.get('cited_span_text', '')}\n\n"
        "Return JSON with keys: label, confidence, rationale."
    )
    return {
        "model": model_id,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a conservative semantic support judge for claim-citation pairs. "
                    "Return only valid JSON. Use the given labels exactly. "
                    "Human labels are reserved for actual human review; your output is a machine judge label."
                ),
            },
            {"role": "user", "content": user_content},
        ],
        "temperature": 0,
        "max_tokens": 350,
        "stream": False,
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
    }


def _coerce_confidence(value):
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, confidence))


def normalize_label_response(response_payload):
    payload = json.loads(response_content(response_payload))
    label = str(payload.get("label") or "").strip()
    if label not in ALLOWED_HUMAN_LABELS:
        raise ValueError(f"unsupported DeepSeek label: {label}")
    return {
        "deepseek_label": label,
        "deepseek_confidence": _coerce_confidence(payload.get("confidence")),
        "deepseek_rationale": str(payload.get("rationale") or "").strip(),
    }


def _dry_run_label(item):
    return {
        **item,
        "deepseek_status": "dry_run",
        "judge_model": MODEL_ID,
        "judge_prompt_version": JUDGE_PROMPT_VERSION,
        "deepseek_label": "",
        "deepseek_confidence": "",
        "deepseek_rationale": "",
        "deepseek_error": "",
    }


def label_items(
    items,
    *,
    api_key=None,
    base_url="https://api.deepseek.com",
    post_fn=post_chat_completion,
    limit=None,
    timeout_seconds=60,
    dry_run=False,
):
    labeled = []
    selected = items[:limit] if limit is not None else items
    for item in selected:
        if dry_run:
            labeled.append(_dry_run_label(item))
            continue
        if not str(item.get("cited_span_text") or "").strip():
            labeled.append(
                {
                    **item,
                    "deepseek_status": "skipped",
                    "judge_model": MODEL_ID,
                    "judge_prompt_version": JUDGE_PROMPT_VERSION,
                    "deepseek_label": "",
                    "deepseek_confidence": "",
                    "deepseek_rationale": "",
                    "deepseek_error": "missing_cited_span_text",
                }
            )
            continue
        try:
            response_payload = post_fn(
                base_url,
                api_key,
                build_label_request(item),
                timeout_seconds,
            )
            normalized = normalize_label_response(response_payload)
            labeled.append(
                {
                    **item,
                    "deepseek_status": "labeled",
                    "judge_model": MODEL_ID,
                    "judge_prompt_version": JUDGE_PROMPT_VERSION,
                    **normalized,
                    "deepseek_error": "",
                }
            )
        except Exception as exc:  # pragma: no cover - exercised through real provider failures.
            labeled.append(
                {
                    **item,
                    "deepseek_status": "error",
                    "judge_model": MODEL_ID,
                    "judge_prompt_version": JUDGE_PROMPT_VERSION,
                    "deepseek_label": "",
                    "deepseek_confidence": "",
                    "deepseek_rationale": "",
                    "deepseek_error": str(exc),
                }
            )
    return labeled


def write_labeled_outputs(items, *, jsonl_path, csv_path):
    jsonl_path = Path(jsonl_path)
    csv_path = Path(csv_path)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in items),
        encoding="utf-8",
    )
    fieldnames = []
    for item in items:
        for field in item:
            if field not in fieldnames:
                fieldnames.append(field)
    for field in DEEPSEEK_LABEL_FIELDS:
        if field not in fieldnames:
            fieldnames.append(field)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow({field: item.get(field, "") for field in fieldnames})


def _label_distribution(rows):
    distribution = {label: 0 for label in ALLOWED_HUMAN_LABELS}
    for row in rows:
        label = str(row.get("deepseek_label") or "")
        distribution[label] = distribution.get(label, 0) + 1
    return distribution


def summarize_label_comparison(v1_rows, v2_rows):
    v1_by_id = {str(row.get("annotation_id") or ""): row for row in v1_rows}
    v2_by_id = {str(row.get("annotation_id") or ""): row for row in v2_rows}
    shared_ids = sorted(set(v1_by_id) & set(v2_by_id))
    confusion = {label: {other: 0 for other in ALLOWED_HUMAN_LABELS} for label in ALLOWED_HUMAN_LABELS}
    disagreements = []
    changed_from_contradictory = []
    changed_from_entailed = []
    for annotation_id in shared_ids:
        old = v1_by_id[annotation_id]
        new = v2_by_id[annotation_id]
        old_label = str(old.get("deepseek_label") or "")
        new_label = str(new.get("deepseek_label") or "")
        confusion.setdefault(old_label, {other: 0 for other in ALLOWED_HUMAN_LABELS})
        confusion[old_label][new_label] = confusion[old_label].get(new_label, 0) + 1
        if old_label != new_label:
            item = {
                "annotation_id": annotation_id,
                "v1_label": old_label,
                "v2_label": new_label,
                "claim_text": new.get("claim_text") or old.get("claim_text") or "",
                "cited_span_text": new.get("cited_span_text") or old.get("cited_span_text") or "",
                "v1_rationale": old.get("deepseek_rationale") or "",
                "v2_rationale": new.get("deepseek_rationale") or "",
            }
            disagreements.append(item)
            if old_label == "contradictory":
                changed_from_contradictory.append(item)
            if old_label == "entailed" and new_label in {"insufficient_evidence", "partially_supported", "unsupported"}:
                changed_from_entailed.append(item)
    total = len(shared_ids)
    disagreement_count = len(disagreements)
    return {
        "total_compared": total,
        "disagreement_count": disagreement_count,
        "disagreement_rate": disagreement_count / total if total else 0.0,
        "v1_label_distribution": _label_distribution([v1_by_id[item] for item in shared_ids]),
        "v2_label_distribution": _label_distribution([v2_by_id[item] for item in shared_ids]),
        "confusion_matrix": confusion,
        "changed_from_contradictory": changed_from_contradictory,
        "changed_from_entailed": changed_from_entailed,
        "disagreements": disagreements,
    }


def write_comparison_report(summary, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def export_manual_audit_subset(rows, target_size=50):
    priority = ("contradictory", "partially_supported", "unsupported", "insufficient_evidence", "entailed")
    by_label = {label: [] for label in priority}
    for row in rows:
        label = str(row.get("deepseek_label") or "")
        if label in by_label:
            by_label[label].append(row)
    subset = []
    for row in by_label["contradictory"]:
        if len(subset) < target_size:
            subset.append(row)
    for label in priority[1:]:
        for row in by_label[label]:
            if len(subset) >= target_size:
                break
            subset.append(row)
        if len(subset) >= target_size:
            break
    return subset

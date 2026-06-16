import csv
import json
from pathlib import Path

from ledger_rag_attribution.pointers import EvidenceSpan, build_citation_id, validate_citation, validation_record
from ledger_rag_attribution.semantic import semantic_support_records


ALLOWED_HUMAN_LABELS = (
    "entailed",
    "partially_supported",
    "unsupported",
    "contradictory",
    "insufficient_evidence",
)

REQUIRED_EXPORT_FIELDS = (
    "annotation_id",
    "dataset",
    "question_id",
    "baseline",
    "claim_id",
    "claim_text",
    "citation_id",
    "cited_span_text",
    "structural_validity",
    "current_semantic_verdict",
    "current_semantic_confidence",
    "human_label",
    "human_notes",
)


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def _claims_by_id(record):
    return {
        str(claim.get("claim_id") or ""): str(claim.get("claim_text") or claim.get("text") or "")
        for claim in record.get("answer", {}).get("atomic_claims", [])
    }


def _semantic_by_pair(record):
    pairs = {}
    for item in record.get("semantic_support", {}).get("records", []):
        key = (str(item.get("claim_id") or ""), str(item.get("citation_id") or ""))
        pairs[key] = item
    return pairs


def _span_from_evidence(dataset, evidence):
    return EvidenceSpan(
        dataset_id=str(evidence.get("dataset_id") or dataset),
        source_id=str(evidence.get("source_id") or evidence.get("source_doc_id") or evidence.get("evidence_id") or ""),
        snapshot_hash=str(evidence.get("snapshot_hash") or evidence.get("source_hash") or ""),
        span_id=str(evidence.get("span_id") or evidence.get("ledger_span_id") or evidence.get("evidence_id") or ""),
        text=str(evidence.get("text") or ""),
        span_hash=evidence.get("span_hash"),
        position=evidence.get("rank"),
    )


def _span_text_by_citation_id(record):
    dataset = str(record.get("input", {}).get("dataset_id") or record.get("_dataset_id") or "")
    spans = {}
    for item in record.get("retrieved_evidence", []):
        span = _span_from_evidence(dataset, item)
        citation_id = str(item.get("citation_id") or build_citation_id(span))
        spans[citation_id] = str(item.get("text") or "")
    for item in record.get("ledger_spans", []):
        span = _span_from_evidence(dataset, item)
        citation_id = str(item.get("citation_id") or build_citation_id(span))
        spans[citation_id] = str(item.get("text") or "")
    return spans


def _validation_records(record):
    existing = record.get("citation_validation")
    if existing:
        return existing
    dataset = str(record.get("input", {}).get("dataset_id") or record.get("_dataset_id") or "")
    spans = [_span_from_evidence(dataset, item) for item in record.get("retrieved_evidence", [])]
    if record.get("ledger_spans"):
        spans.extend(_span_from_evidence(dataset, item) for item in record.get("ledger_spans", []))
    pointer_by_legacy_id = {}
    retrieved_citation_ids = set()
    for item in record.get("retrieved_evidence", []):
        span = _span_from_evidence(dataset, item)
        citation_id = str(item.get("citation_id") or build_citation_id(span))
        retrieved_citation_ids.add(citation_id)
        for key in ("evidence_id", "ledger_span_id", "span_id"):
            if item.get(key):
                pointer_by_legacy_id[str(item[key])] = citation_id
    rows = []
    for citation in record.get("citations", []):
        raw = str(citation.get("citation_id") or citation.get("cited_evidence_id") or citation.get("evidence_id") or "")
        normalized = raw.strip().strip("`'\"")
        citation_id = pointer_by_legacy_id.get(normalized, normalized)
        result = validate_citation(citation_id, ledger_spans=spans, retrieved_citation_ids=retrieved_citation_ids)
        row = validation_record(result, claim_id=str(citation.get("claim_id") or ""))
        row["raw_citation_id"] = raw
        rows.append(row)
    return rows


def _semantic_by_pair_or_synthesized(record, validation_records, span_text_by_citation_id):
    existing = _semantic_by_pair(record)
    if existing:
        return existing
    synthesized = semantic_support_records(
        claims_by_id=_claims_by_id(record),
        validation_records=validation_records,
        span_text_by_citation_id=span_text_by_citation_id,
    )
    return {
        (str(item.get("claim_id") or ""), str(item.get("citation_id") or "")): item
        for item in synthesized
    }


def export_annotation_items(records, include_invalid=False):
    items = []
    for record in records:
        dataset = str(record.get("input", {}).get("dataset_id") or record.get("_dataset_id") or "")
        question_id = str(record.get("input", {}).get("question_id") or "")
        baseline = str(record.get("run_metadata", {}).get("baseline_family") or "")
        claims = _claims_by_id(record)
        spans = _span_text_by_citation_id(record)
        validations = _validation_records(record)
        semantic_by_pair = _semantic_by_pair_or_synthesized(record, validations, spans)
        for validation in validations:
            structural_validity = str(validation.get("structural_validity") or "")
            if structural_validity != "valid" and not include_invalid:
                continue
            claim_id = str(validation.get("claim_id") or "")
            citation_id = str(validation.get("citation_id") or "")
            semantic = semantic_by_pair.get((claim_id, citation_id), {})
            items.append(
                {
                    "annotation_id": f"calib_{len(items) + 1:06d}",
                    "dataset": dataset,
                    "question_id": question_id,
                    "baseline": baseline,
                    "claim_id": claim_id,
                    "claim_text": claims.get(claim_id, ""),
                    "citation_id": citation_id,
                    "cited_span_text": spans.get(citation_id, ""),
                    "structural_validity": structural_validity,
                    "current_semantic_verdict": semantic.get("verdict", ""),
                    "current_semantic_confidence": semantic.get("confidence", ""),
                    "human_label": "",
                    "human_notes": "",
                }
            )
    return items


def write_exports(items, *, jsonl_path, csv_path):
    jsonl_path = Path(jsonl_path)
    csv_path = Path(csv_path)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in items),
        encoding="utf-8",
    )
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(REQUIRED_EXPORT_FIELDS))
        writer.writeheader()
        for item in items:
            writer.writerow({field: item.get(field, "") for field in REQUIRED_EXPORT_FIELDS})

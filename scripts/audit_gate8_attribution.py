import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_attribution.pointers import EvidenceSpan, build_citation_id, validate_citation, validation_record
from ledger_rag_attribution.semantic import semantic_support_records, summarize_semantic_support


DEFAULT_RUNS = {
    "hotpotqa__old2": "artifacts/gate8/main_v1/runs/deepseek_v4_pro_50x2x3/hotpotqa/run_records.jsonl",
    "2wikimultihopqa__old2": "artifacts/gate8/main_v1/runs/deepseek_v4_pro_50x2x3/2wikimultihopqa/run_records.jsonl",
    "musique__old2": "artifacts/gate8/main_v1/runs/musique_topk16_50x2/musique/run_records.jsonl",
    "hotpotqa__new4": "artifacts/gate8/main_v1/runs/new4_hotpotqa_2wiki_50x4/hotpotqa/run_records.jsonl",
    "2wikimultihopqa__new4": "artifacts/gate8/main_v1/runs/new4_hotpotqa_2wiki_50x4/2wikimultihopqa/run_records.jsonl",
    "musique__new4": "artifacts/gate8/main_v1/runs/new4_musique_topk16_50x4/musique/run_records.jsonl",
}


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def safe_rate(numerator, denominator):
    return round(numerator / denominator, 6) if denominator else 0.0


def dataset_id_from_run_key(run_key):
    return run_key.split("__", 1)[0]


def _span_from_evidence(dataset_id, evidence):
    return EvidenceSpan(
        dataset_id=str(evidence.get("dataset_id") or dataset_id),
        source_id=str(evidence.get("source_id") or evidence.get("source_doc_id") or evidence.get("evidence_id") or ""),
        snapshot_hash=str(evidence.get("snapshot_hash") or evidence.get("source_hash") or ""),
        span_id=str(evidence.get("span_id") or evidence.get("ledger_span_id") or evidence.get("evidence_id") or ""),
        text=str(evidence.get("text") or ""),
        span_hash=evidence.get("span_hash"),
        position=evidence.get("rank"),
    )


def _span_from_ledger_row(dataset_id, row):
    return EvidenceSpan(
        dataset_id=str(row.get("dataset_id") or dataset_id),
        source_id=str(row.get("source_id") or row.get("source_doc_id") or row.get("evidence_id") or ""),
        snapshot_hash=str(row.get("snapshot_hash") or row.get("source_hash") or ""),
        span_id=str(row.get("span_id") or row.get("ledger_span_id") or row.get("evidence_id") or ""),
        text=str(row.get("text") or ""),
        span_hash=row.get("span_hash"),
        position=row.get("rank"),
    )


def _retrieved_pointer_maps(dataset_id, retrieved_evidence):
    pointer_by_legacy_id = {}
    retrieved_pointers = set()
    spans = []
    for evidence in retrieved_evidence:
        span = _span_from_evidence(dataset_id, evidence)
        pointer = evidence.get("citation_id") or build_citation_id(span)
        retrieved_pointers.add(pointer)
        spans.append(span)
        if evidence.get("evidence_id"):
            pointer_by_legacy_id[str(evidence["evidence_id"])] = pointer
        if evidence.get("ledger_span_id"):
            pointer_by_legacy_id[str(evidence["ledger_span_id"])] = pointer
    return pointer_by_legacy_id, retrieved_pointers, spans


def citation_validation_records(record):
    existing = record.get("citation_validation")
    if existing:
        return existing

    dataset_id = record.get("input", {}).get("dataset_id") or record.get("_dataset_id") or "unknown_dataset"
    pointer_by_legacy_id, retrieved_pointers, retrieved_spans = _retrieved_pointer_maps(dataset_id, record.get("retrieved_evidence", []))
    if record.get("ledger_spans"):
        ledger_spans = [_span_from_ledger_row(dataset_id, row) for row in record.get("ledger_spans", [])]
    else:
        ledger_spans = retrieved_spans

    validations = []
    for citation in record.get("citations", []):
        raw_citation_id = str(citation.get("citation_id") or citation.get("cited_evidence_id") or citation.get("evidence_id") or "")
        normalized = raw_citation_id.strip().strip("`'\"")
        citation_id = pointer_by_legacy_id.get(normalized, normalized)
        result = validate_citation(
            citation_id,
            ledger_spans=ledger_spans,
            retrieved_citation_ids=retrieved_pointers,
        )
        row = validation_record(result, claim_id=str(citation.get("claim_id") or ""))
        row["raw_citation_id"] = raw_citation_id
        validations.append(row)
    return validations


def _claims_by_id(record):
    return {
        claim.get("claim_id"): claim.get("claim_text") or claim.get("text") or ""
        for claim in record.get("answer", {}).get("atomic_claims", [])
    }


def _span_text_by_citation_id(record):
    dataset_id = record.get("input", {}).get("dataset_id") or record.get("_dataset_id") or "unknown_dataset"
    span_text = {}
    for evidence in record.get("retrieved_evidence", []):
        span = _span_from_evidence(dataset_id, evidence)
        citation_id = evidence.get("citation_id") or build_citation_id(span)
        span_text[citation_id] = evidence.get("text", "")
    for row in record.get("ledger_spans", []):
        span = _span_from_ledger_row(dataset_id, row)
        span_text[build_citation_id(span)] = row.get("text", "")
    return span_text


def semantic_support_record_rows(record):
    existing = record.get("semantic_support", {}).get("records")
    if existing:
        return existing
    return semantic_support_records(
        claims_by_id=_claims_by_id(record),
        validation_records=citation_validation_records(record),
        span_text_by_citation_id=_span_text_by_citation_id(record),
    )


def summarize(records):
    claim_count = 0
    citation_count = 0
    valid_citation_count = 0
    invalid_citation_count = 0
    malformed_citation_count = 0
    nonexistent_citation_count = 0
    not_retrieved_citation_count = 0
    wrong_snapshot_hash_count = 0
    wrong_span_hash_count = 0
    span_replay_success_count = 0
    snapshot_replay_success_count = 0
    cited_claim_count = 0
    refusal_count = 0
    semantic_records_all = []

    for record in records:
        claims = {
            claim["claim_id"]: claim
            for claim in record.get("answer", {}).get("atomic_claims", [])
        }
        validations = citation_validation_records(record)
        semantic_records_all.extend(semantic_support_record_rows(record))
        cited_claims = {item.get("claim_id") for item in validations if item.get("claim_id")}

        claim_count += len(claims)
        citation_count += len(validations)
        cited_claim_count += len(set(claims) & cited_claims)
        refusal_count += record.get("answer", {}).get("refusal_label") != "answered"
        for item in validations:
            is_valid = item.get("structural_validity") == "valid"
            valid_citation_count += is_valid
            invalid_citation_count += not is_valid
            malformed_citation_count += item.get("validation_error") == "malformed_citation_id"
            nonexistent_citation_count += item.get("validation_error") == "nonexistent_citation_id"
            not_retrieved_citation_count += item.get("validation_error") == "not_in_retrieved_evidence"
            wrong_snapshot_hash_count += item.get("validation_error") == "wrong_snapshot_hash"
            wrong_span_hash_count += item.get("validation_error") == "wrong_span_hash"
            span_replay_success_count += item.get("span_replay_success") is True
            snapshot_replay_success_count += item.get("snapshot_replay_success") is True

    semantic_summary = summarize_semantic_support(semantic_records_all)
    return {
        "record_count": len(records),
        "refusal_rate": safe_rate(refusal_count, len(records)),
        "claim_count": claim_count,
        "citation_count": citation_count,
        "valid_citation_count": valid_citation_count,
        "invalid_citation_count": invalid_citation_count,
        "claim_citation_coverage": safe_rate(cited_claim_count, claim_count),
        "invalid_citation_rate": safe_rate(invalid_citation_count, citation_count),
        "citation_id_validity_rate": safe_rate(valid_citation_count, citation_count),
        "span_replay_success_rate": safe_rate(span_replay_success_count, citation_count),
        "snapshot_replay_success_rate": safe_rate(snapshot_replay_success_count, citation_count),
        "not_in_retrieved_evidence_rate": safe_rate(not_retrieved_citation_count, citation_count),
        "malformed_citation_rate": safe_rate(malformed_citation_count, citation_count),
        "wrong_snapshot_hash_rate": safe_rate(wrong_snapshot_hash_count, citation_count),
        "wrong_span_hash_rate": safe_rate(wrong_span_hash_count, citation_count),
        "malformed_citation_count": malformed_citation_count,
        "nonexistent_citation_count": nonexistent_citation_count,
        "not_retrieved_citation_count": not_retrieved_citation_count,
        "wrong_snapshot_hash_count": wrong_snapshot_hash_count,
        "wrong_span_hash_count": wrong_span_hash_count,
        **semantic_summary,
    }


def write_yaml(path, payload):
    lines = []

    def emit(prefix, value):
        if isinstance(value, dict):
            for key, child in value.items():
                if isinstance(child, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    emit(prefix + "  ", child)
                else:
                    lines.append(f"{prefix}{key}: {child}")
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"{prefix}-")
                    emit(prefix + "  ", item)
                else:
                    lines.append(f"{prefix}- {item}")

    emit("", payload)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_summary(run_paths):
    records = []
    for run_key, path in run_paths.items():
        dataset_id = dataset_id_from_run_key(run_key)
        for record in read_jsonl(path):
            record["_dataset_id"] = dataset_id
            record["_run_key"] = run_key
            records.append(record)

    by_baseline = defaultdict(list)
    by_dataset = defaultdict(list)
    by_dataset_baseline = defaultdict(list)
    for record in records:
        dataset_id = record["_dataset_id"]
        baseline = record["run_metadata"]["baseline_family"]
        by_dataset[dataset_id].append(record)
        by_baseline[baseline].append(record)
        by_dataset_baseline[(dataset_id, baseline)].append(record)

    return {
        "version": 2,
        "stage": "gate8_migrated_structural_attribution_audit",
        "source": "corrected_main_v1_50x6x3",
        "api_calls_made_by_this_step": 0,
        "audit_method": "deterministic_citation_pointer_validation",
        "structural_citation_validation": {
            "status": "completed",
            "validator_name": "ledger_rag_attribution.pointers.validate_citation",
        },
        "replayability": {
            "status": "computed_from_snapshot_and_span_hash_fields",
        },
        "semantic_support": {
            "status": "evaluated",
            "semantic_verifier": "local_deterministic_claim_span_heuristic_v1",
            "note": "local deterministic heuristic; replaceable by future LLM judge or NLI model",
        },
        "diagnostics": {
            "lexical_support_rate": "not_computed",
            "note": "lexical overlap is diagnostic only and is not a core metric in this migrated audit",
        },
        "overall": summarize(records),
        "by_dataset": {
            dataset_id: summarize(dataset_records)
            for dataset_id, dataset_records in sorted(by_dataset.items())
        },
        "by_baseline": {
            baseline: summarize(baseline_records)
            for baseline, baseline_records in sorted(by_baseline.items())
        },
        "by_dataset_baseline": {
            f"{dataset_id}__{baseline}": summarize(group_records)
            for (dataset_id, baseline), group_records in sorted(by_dataset_baseline.items())
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Audit deterministic structural citation validity for Gate 8 run records.")
    parser.add_argument(
        "--run",
        action="append",
        default=[],
        metavar="DATASET_ID=PATH",
        help="Run records JSONL to audit. Can be passed multiple times. Defaults to corrected 50x6x3 artifacts.",
    )
    parser.add_argument(
        "--source-label",
        default="corrected_main_v1_50x6x3",
        help="Source label stored in the YAML summary.",
    )
    parser.add_argument(
        "--output",
        default="configs/gate8/main_v1_migrated_structural_attribution_audit.yaml",
        help="YAML summary output path. Defaults to a migrated path to preserve historical diagnostics.",
    )
    args = parser.parse_args()

    run_paths = {}
    if args.run:
        for item in args.run:
            if "=" not in item:
                raise SystemExit(f"--run must use DATASET_ID=PATH, got: {item}")
            dataset_id, path = item.split("=", 1)
            run_paths[dataset_id] = path
    else:
        run_paths = DEFAULT_RUNS

    summary = build_summary(run_paths)
    summary["source"] = args.source_label
    write_yaml(args.output, summary)
    print(f"structural_attribution_audit={args.output}")
    print(f"invalid_citation_rate={summary['overall']['invalid_citation_rate']}")
    print(f"citation_id_validity_rate={summary['overall']['citation_id_validity_rate']}")
    print(f"span_replay_success_rate={summary['overall']['span_replay_success_rate']}")
    print(f"snapshot_replay_success_rate={summary['overall']['snapshot_replay_success_rate']}")


if __name__ == "__main__":
    raise SystemExit(main())

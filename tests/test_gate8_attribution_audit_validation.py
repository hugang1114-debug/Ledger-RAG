import importlib.util
import json
from pathlib import Path

from ledger_rag_attribution.pointers import EvidenceSpan, build_citation_id


ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPT = ROOT / "scripts" / "audit_gate8_attribution.py"


def _load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_gate8_attribution", AUDIT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_audit_summary_includes_structural_validation_and_replay_metrics(tmp_path):
    audit = _load_audit_module()
    retrieved_span = EvidenceSpan("hotpotqa", "doc_yoruba", "snap123", "doc_yoruba", "The Ida is used by Yoruba people.")
    not_retrieved_span = EvidenceSpan("hotpotqa", "doc_other", "snap123", "doc_other", "Other evidence.")
    valid_pointer = build_citation_id(retrieved_span)
    not_retrieved_pointer = build_citation_id(not_retrieved_span)
    run_path = tmp_path / "run_records.jsonl"
    record = {
        "input": {"dataset_id": "hotpotqa"},
        "answer": {
            "refusal_label": "answered",
            "atomic_claims": [{"claim_id": "c1", "claim_text": "The Ida is used by Yoruba people."}],
        },
        "retrieved_evidence": [
            {
                "evidence_id": "doc_yoruba",
                "citation_id": valid_pointer,
                "source_doc_id": "doc_yoruba",
                "source_hash": "snap123",
                "ledger_span_id": "doc_yoruba",
                "text": retrieved_span.text,
            }
        ],
        "ledger_spans": [
            {
                "dataset_id": "hotpotqa",
                "source_id": "doc_yoruba",
                "snapshot_hash": "snap123",
                "span_id": "doc_yoruba",
                "text": retrieved_span.text,
            },
            {
                "dataset_id": "hotpotqa",
                "source_id": "doc_other",
                "snapshot_hash": "snap123",
                "span_id": "doc_other",
                "text": not_retrieved_span.text,
            },
        ],
        "citations": [
            {"claim_id": "c1", "cited_evidence_id": valid_pointer},
            {"claim_id": "c1", "cited_evidence_id": "bad"},
            {"claim_id": "c1", "cited_evidence_id": not_retrieved_pointer},
        ],
        "run_metadata": {"baseline_family": "ledger_validator"},
    }
    run_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    summary = audit.build_summary({"hotpotqa__test": str(run_path)})

    overall = summary["overall"]
    assert summary["stage"] == "gate8_migrated_structural_attribution_audit"
    assert summary["semantic_support"]["status"] == "evaluated"
    assert overall["citation_count"] == 3
    assert overall["valid_citation_count"] == 1
    assert overall["invalid_citation_rate"] == 0.666667
    assert overall["citation_id_validity_rate"] == 0.333333
    assert overall["not_in_retrieved_evidence_rate"] == 0.333333
    assert overall["malformed_citation_rate"] == 0.333333
    assert overall["span_replay_success_rate"] == 0.666667
    assert overall["snapshot_replay_success_rate"] == 0.666667
    assert overall["entailment_support_rate"] == 0.333333
    assert overall["unsupported_citation_rate"] == 0.0
    assert overall["partially_supported_rate"] == 0.0
    assert overall["contradictory_rate"] == 0.0
    assert overall["semantic_evaluation_skip_rate"] == 0.666667

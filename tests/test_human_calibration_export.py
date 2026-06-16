import csv
import json
import subprocess
import sys
from pathlib import Path

from ledger_rag_attribution.calibration_export import (
    ALLOWED_HUMAN_LABELS,
    REQUIRED_EXPORT_FIELDS,
    export_annotation_items,
    write_exports,
)
from ledger_rag_attribution.pointers import EvidenceSpan, build_citation_id


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "export_human_calibration_set.py"
DOC = ROOT / "docs" / "human-calibration-set.md"


def _record():
    span = EvidenceSpan("hotpotqa", "doc_yoruba", "snap123", "s1", "The Ida is used by Yoruba people.")
    citation_id = build_citation_id(span)
    return {
        "input": {"dataset_id": "hotpotqa", "question_id": "q1"},
        "run_metadata": {"baseline_family": "ledger_validator"},
        "answer": {
            "atomic_claims": [
                {"claim_id": "c1", "claim_text": "The Ida is used by Yoruba people."},
                {"claim_id": "c2", "claim_text": "Invalid citation should be filtered."},
            ]
        },
        "retrieved_evidence": [
            {
                "citation_id": citation_id,
                "text": span.text,
                "source_doc_id": "doc_yoruba",
                "source_hash": "snap123",
                "ledger_span_id": "s1",
            }
        ],
        "citation_validation": [
            {
                "claim_id": "c1",
                "citation_id": citation_id,
                "structural_validity": "valid",
                "validation_error": "none",
            },
            {
                "claim_id": "c2",
                "citation_id": "bad",
                "structural_validity": "invalid",
                "validation_error": "malformed_citation_id",
            },
        ],
        "semantic_support": {
            "records": [
                {
                    "claim_id": "c1",
                    "citation_id": citation_id,
                    "verdict": "entailed",
                    "confidence": 1.0,
                },
                {
                    "claim_id": "c2",
                    "citation_id": "bad",
                    "verdict": "insufficient_evidence",
                    "confidence": 0.0,
                },
            ]
        },
    }


def test_export_includes_required_fields_and_preserves_heuristic_not_gold():
    items = export_annotation_items([_record()])

    assert len(items) == 1
    assert set(REQUIRED_EXPORT_FIELDS) <= set(items[0])
    assert items[0]["annotation_id"] == "calib_000001"
    assert items[0]["current_semantic_verdict"] == "entailed"
    assert items[0]["current_semantic_confidence"] == 1.0
    assert items[0]["human_label"] == ""
    assert items[0]["human_notes"] == ""


def test_export_filters_structurally_invalid_by_default_and_can_include_them():
    default_items = export_annotation_items([_record()])
    all_items = export_annotation_items([_record()], include_invalid=True)

    assert [item["claim_id"] for item in default_items] == ["c1"]
    assert [item["claim_id"] for item in all_items] == ["c1", "c2"]
    assert all_items[1]["structural_validity"] == "invalid"


def test_export_synthesizes_validation_and_semantic_for_legacy_records():
    span = EvidenceSpan("hotpotqa", "doc_yoruba", "snap123", "s1", "The Ida is used by Yoruba people.")
    record = {
        "input": {"dataset_id": "hotpotqa", "question_id": "q1"},
        "run_metadata": {"baseline_family": "ledger_validator"},
        "answer": {"atomic_claims": [{"claim_id": "c1", "claim_text": "The Ida is used by Yoruba people."}]},
        "retrieved_evidence": [
            {
                "evidence_id": "doc_yoruba",
                "source_doc_id": "doc_yoruba",
                "source_hash": "snap123",
                "ledger_span_id": "s1",
                "text": span.text,
            }
        ],
        "citations": [{"claim_id": "c1", "cited_evidence_id": "doc_yoruba"}],
    }

    items = export_annotation_items([record])

    assert len(items) == 1
    assert items[0]["citation_id"] == build_citation_id(span)
    assert items[0]["cited_span_text"] == span.text
    assert items[0]["structural_validity"] == "valid"
    assert items[0]["current_semantic_verdict"] == "entailed"


def test_write_exports_creates_jsonl_and_csv(tmp_path):
    jsonl_path = tmp_path / "calibration.jsonl"
    csv_path = tmp_path / "calibration.csv"
    items = export_annotation_items([_record()])

    write_exports(items, jsonl_path=jsonl_path, csv_path=csv_path)

    jsonl_rows = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines()]
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert jsonl_rows[0]["annotation_id"] == "calib_000001"
    assert csv_rows[0]["annotation_id"] == "calib_000001"


def test_allowed_label_schema_is_documented():
    doc = DOC.read_text(encoding="utf-8")

    for label in ALLOWED_HUMAN_LABELS:
        assert f"`{label}`" in doc


def test_cli_exports_jsonl_and_csv(tmp_path):
    run_path = tmp_path / "run_records.jsonl"
    jsonl_path = tmp_path / "out.jsonl"
    csv_path = tmp_path / "out.csv"
    run_path.write_text(json.dumps(_record()) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--run",
            str(run_path),
            "--jsonl-output",
            str(jsonl_path),
            "--csv-output",
            str(csv_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "exported_examples=1" in result.stdout
    assert jsonl_path.is_file()
    assert csv_path.is_file()

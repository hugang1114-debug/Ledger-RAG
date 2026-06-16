import json
from pathlib import Path

from ledger_rag_attribution.deepseek_v2_audit import (
    aggregate_by_baseline,
    apply_deepseek_v2_semantic_support,
    build_semantic_judge_items,
    write_baseline_table,
)


def _record(structural_validity="valid", validation_error="none"):
    return {
        "input": {"dataset_id": "hotpotqa", "question_id": "q1"},
        "answer": {
            "global_answer": "The Ida is used by Yoruba people.",
            "refusal_label": "answered",
            "atomic_claims": [{"claim_id": "c1", "claim_text": "The Ida is used by Yoruba people."}],
        },
        "retrieved_evidence": [
            {
                "citation_id": "hotpotqa/doc/snap/span/hash",
                "text": "The Ida is used by Yoruba people.",
            }
        ],
        "citation_validation": [
            {
                "claim_id": "c1",
                "citation_id": "hotpotqa/doc/snap/span/hash",
                "structural_validity": structural_validity,
                "validation_error": validation_error,
                "source_exists": structural_validity == "valid",
                "snapshot_replay_success": structural_validity == "valid",
                "span_replay_success": structural_validity == "valid",
                "span_hash_match": structural_validity == "valid",
                "in_retrieved_evidence": structural_validity == "valid",
            }
        ],
        "run_metadata": {"baseline_family": "ledger_validator"},
    }


def test_build_semantic_judge_items_exports_only_structurally_valid_pairs():
    records = [_record(), _record(structural_validity="invalid", validation_error="malformed_citation_id")]

    items = build_semantic_judge_items(records)

    assert len(items) == 1
    assert items[0]["annotation_id"] == "hotpotqa__q1__ledger_validator__c1__1"
    assert items[0]["claim_text"] == "The Ida is used by Yoruba people."
    assert items[0]["cited_span_text"] == "The Ida is used by Yoruba people."
    assert items[0]["human_label"] == ""


def test_apply_deepseek_v2_semantic_support_keeps_invalid_pairs_skipped_and_records_judge_metadata():
    records = [_record(), _record(structural_validity="invalid", validation_error="malformed_citation_id")]

    def fake_post(_base_url, _api_key, _request_payload, _timeout_seconds):
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "label": "entailed",
                                "confidence": 0.99,
                                "rationale": "Direct support.",
                            }
                        )
                    }
                }
            ]
        }

    updated = apply_deepseek_v2_semantic_support(
        records,
        api_key="fake",
        base_url="https://api.deepseek.com",
        post_fn=fake_post,
    )

    valid_record = updated[0]["semantic_support"]["records"][0]
    invalid_record = updated[1]["semantic_support"]["records"][0]
    assert valid_record["verdict"] == "entailed"
    assert valid_record["judge_model"] == "deepseek-v4-pro"
    assert valid_record["judge_prompt_version"] == "deepseek_semantic_judge_v2"
    assert invalid_record["status"] == "skipped"
    assert invalid_record["rationale"] == "structural validation failed: malformed_citation_id"
    assert invalid_record["judge_prompt_version"] == "deepseek_semantic_judge_v2"


def test_aggregate_by_baseline_reports_structural_and_semantic_rates(tmp_path):
    record = _record()
    record["semantic_support"] = {
        "records": [
            {
                "claim_id": "c1",
                "citation_id": "hotpotqa/doc/snap/span/hash",
                "status": "evaluated",
                "verdict": "entailed",
            }
        ]
    }

    table = aggregate_by_baseline([record])

    row = table["ledger_validator"]
    assert row["run_record_count"] == 1
    assert row["claim_citation_pair_count"] == 1
    assert row["claim_count_per_answer"] == 1.0
    assert row["citation_count_per_answer"] == 1.0
    assert row["claim_citation_coverage"] == 1.0
    assert row["answer_length"] == 33.0
    assert row["refusal_rate"] == 0.0
    assert row["invalid_citation_rate"] == 0.0
    assert row["citation_id_validity_rate"] == 1.0
    assert row["entailment_support_rate"] == 1.0
    assert row["insufficient_evidence_rate"] == 0.0

    output = tmp_path / "table.md"
    write_baseline_table(table, output)
    assert "| baseline |" in output.read_text(encoding="utf-8")

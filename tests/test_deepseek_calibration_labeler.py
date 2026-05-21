import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from ledger_rag_attribution.deepseek_labeler import (
    DEEPSEEK_LABEL_FIELDS,
    JUDGE_PROMPT_VERSION,
    build_label_request,
    export_manual_audit_subset,
    label_items,
    normalize_label_response,
    summarize_label_comparison,
)


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "label_human_calibration_with_deepseek.py"


def _item():
    return {
        "annotation_id": "calib_000001",
        "dataset": "hotpotqa",
        "question_id": "q1",
        "baseline": "ledger_validator",
        "claim_id": "c1",
        "claim_text": "The Ida is used by Yoruba people.",
        "citation_id": "hotpotqa/doc/snap/span/hash",
        "cited_span_text": "The Ida is used by Yoruba people.",
        "structural_validity": "valid",
        "current_semantic_verdict": "entailed",
        "current_semantic_confidence": 1.0,
        "human_label": "",
        "human_notes": "",
    }


def test_build_label_request_uses_deepseek_json_judge_contract():
    request = build_label_request(_item())

    assert request["model"] == "deepseek-v4-pro"
    assert request["temperature"] == 0
    assert request["response_format"] == {"type": "json_object"}
    content = request["messages"][1]["content"]
    assert "entailed" in content
    assert "partially_supported" in content
    assert "The Ida is used by Yoruba people." in content
    assert "Return JSON" in content
    assert JUDGE_PROMPT_VERSION == "deepseek_semantic_judge_v2"
    assert "Entity overlap is not support" in content
    assert "Use contradictory only when the span explicitly conflicts with the claim" in content
    assert "For negative claims or evidence-absence claims, prefer insufficient_evidence" in content


def test_normalize_label_response_accepts_allowed_label_and_confidence():
    label = normalize_label_response(
        {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "label": "entailed",
                                "confidence": 0.91,
                                "rationale": "The cited span states the claim directly.",
                            }
                        )
                    }
                }
            ]
        }
    )

    assert label == {
        "deepseek_label": "entailed",
        "deepseek_confidence": 0.91,
        "deepseek_rationale": "The cited span states the claim directly.",
    }


def test_normalize_label_response_rejects_unknown_label():
    with pytest.raises(ValueError, match="unsupported DeepSeek label"):
        normalize_label_response({"choices": [{"message": {"content": '{"label": "maybe"}'}}]})


def test_label_items_adds_deepseek_fields_without_overwriting_human_label():
    rows = [_item() | {"human_label": "entailed"}]
    calls = []

    def fake_post(base_url, api_key, request_payload, timeout_seconds):
        calls.append((base_url, api_key, request_payload, timeout_seconds))
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "label": "entailed",
                                "confidence": 0.88,
                                "rationale": "Direct support.",
                            }
                        )
                    }
                }
            ]
        }

    labeled = label_items(rows, api_key="secret", base_url="https://api.deepseek.com", post_fn=fake_post)

    assert len(calls) == 1
    assert labeled[0]["human_label"] == "entailed"
    assert labeled[0]["deepseek_label"] == "entailed"
    assert labeled[0]["deepseek_confidence"] == 0.88
    assert labeled[0]["deepseek_status"] == "labeled"
    assert labeled[0]["judge_model"] == "deepseek-v4-pro"
    assert labeled[0]["judge_prompt_version"] == JUDGE_PROMPT_VERSION
    assert set(DEEPSEEK_LABEL_FIELDS) <= set(labeled[0])


def test_label_items_handles_malformed_judge_output_safely():
    def bad_post(base_url, api_key, request_payload, timeout_seconds):
        return {"choices": [{"message": {"content": '{"label": "entailed",'}}]}

    labeled = label_items([_item()], api_key="secret", base_url="https://api.deepseek.com", post_fn=bad_post)

    assert labeled[0]["deepseek_status"] == "error"
    assert labeled[0]["deepseek_label"] == ""
    assert labeled[0]["human_label"] == ""
    assert labeled[0]["judge_prompt_version"] == JUDGE_PROMPT_VERSION
    assert labeled[0]["deepseek_error"]


def test_dry_run_cli_writes_outputs_without_api_key(tmp_path):
    input_path = tmp_path / "calibration.jsonl"
    jsonl_output = tmp_path / "deepseek.jsonl"
    csv_output = tmp_path / "deepseek.csv"
    input_path.write_text(json.dumps(_item()) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--input",
            str(input_path),
            "--jsonl-output",
            str(jsonl_output),
            "--csv-output",
            str(csv_output),
            "--dry-run",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "labeled_examples=1" in result.stdout
    jsonl_rows = [json.loads(line) for line in jsonl_output.read_text(encoding="utf-8").splitlines()]
    with csv_output.open("r", encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert jsonl_rows[0]["deepseek_status"] == "dry_run"
    assert csv_rows[0]["deepseek_status"] == "dry_run"
    assert jsonl_rows[0]["human_label"] == ""
    assert jsonl_rows[0]["judge_prompt_version"] == JUDGE_PROMPT_VERSION


def test_summarize_label_comparison_reports_distribution_and_changes():
    v1 = [
        _item() | {"annotation_id": "a1", "deepseek_label": "contradictory"},
        _item() | {"annotation_id": "a2", "deepseek_label": "entailed"},
        _item() | {"annotation_id": "a3", "deepseek_label": "entailed"},
    ]
    v2 = [
        _item() | {"annotation_id": "a1", "deepseek_label": "insufficient_evidence"},
        _item() | {"annotation_id": "a2", "deepseek_label": "partially_supported"},
        _item() | {"annotation_id": "a3", "deepseek_label": "entailed"},
    ]

    summary = summarize_label_comparison(v1, v2)

    assert summary["total_compared"] == 3
    assert summary["disagreement_count"] == 2
    assert summary["disagreement_rate"] == 2 / 3
    assert summary["v1_label_distribution"]["entailed"] == 2
    assert summary["v2_label_distribution"]["partially_supported"] == 1
    assert summary["confusion_matrix"]["contradictory"]["insufficient_evidence"] == 1
    assert summary["changed_from_contradictory"][0]["annotation_id"] == "a1"
    assert summary["changed_from_entailed"][0]["annotation_id"] == "a2"


def test_export_manual_audit_subset_prioritizes_high_risk_labels():
    rows = []
    for index, label in enumerate(
        ["contradictory", "partially_supported", "unsupported", "insufficient_evidence", "entailed"],
        start=1,
    ):
        for offset in range(3):
            rows.append(_item() | {"annotation_id": f"a{index}{offset}", "deepseek_label": label})

    subset = export_manual_audit_subset(rows, target_size=8)

    labels = [item["deepseek_label"] for item in subset]
    assert labels.count("contradictory") == 3
    assert "partially_supported" in labels
    assert len(subset) == 8

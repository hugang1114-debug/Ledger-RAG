import json
import subprocess
import sys
from pathlib import Path

from ledger_rag_smoke.result_review import (
    REQUIRED_ARTIFACTS,
    review_smoke_artifacts,
    sha256_file,
    write_summary_yaml,
)


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "review_gate8p_smoke_result.py"


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_smoke_artifacts(base):
    base.mkdir(parents=True, exist_ok=True)
    request = {"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "question"}]}
    response = {"id": "r1", "model": "deepseek-v4-pro", "choices": [{"message": {"content": "{}"}}]}
    run_record = {
        "input": {"dataset_id": "gate7_offline", "split": "pilot", "question_id": "q_traceability"},
        "retrieved_evidence": [{"evidence_id": "span_1"}],
        "answer": {
            "global_answer": "Ledger-RAG stores source evidence as replayable ledger spans.",
            "atomic_claims": [{"claim_id": "c1", "claim_text": "Ledger-RAG stores source evidence as replayable ledger spans."}],
        },
        "citations": [{"claim_id": "c1", "cited_evidence_id": "span_1"}],
        "verdicts": [{"claim_id": "c1", "label": "not_checked"}],
        "run_metadata": {
            "run_id": "gate8p_deepseek_smoke_q_traceability",
            "baseline_family": "ledger_validator",
            "estimated_cost_usd": 0.00019,
        },
    }
    metric_record = {
        "metric_record": {"run_id": "gate8p_deepseek_smoke_q_traceability"},
        "retrieval": {},
        "answer_quality": {},
        "attribution": {},
        "system": {"cost_per_query_usd": 0.00019},
        "aggregation": {},
    }
    cost_estimate = {
        "provider": "deepseek",
        "model": "deepseek-v4-pro",
        "estimated_cost_usd": 0.00019,
        "usage": {"prompt_tokens": 208, "completion_tokens": 114, "total_tokens": 322},
    }
    _write_json(base / "request.json", request)
    _write_json(base / "response.json", response)
    _write_json(base / "run_record.json", run_record)
    _write_json(base / "metric_record.json", metric_record)
    _write_json(base / "cost_estimate.json", cost_estimate)


def test_sha256_file_is_stable(tmp_path):
    path = tmp_path / "a.txt"
    path.write_text("abc", encoding="utf-8")

    assert sha256_file(path) == sha256_file(path)
    assert len(sha256_file(path)) == 64


def test_review_smoke_artifacts_passes_and_records_hashes_without_raw_answer(tmp_path):
    _write_smoke_artifacts(tmp_path)

    summary = review_smoke_artifacts(tmp_path, budget_ceiling_usd=10)

    assert summary["review_status"] == "passed"
    assert summary["provider"] == "deepseek"
    assert summary["model"] == "deepseek-v4-pro"
    assert summary["run_id"] == "gate8p_deepseek_smoke_q_traceability"
    assert summary["question_id"] == "q_traceability"
    assert summary["estimated_cost_usd"] == 0.00019
    assert summary["within_budget"] is True
    assert summary["artifact_hashes"].keys() == set(REQUIRED_ARTIFACTS)
    assert summary["answer_present"] is True
    assert summary["claim_count"] == 1
    assert summary["citation_count"] == 1
    assert summary["secret_scan_passed"] is True
    assert summary["full_gate8_execution_authorized"] is False
    assert summary["blockers"] == []
    assert "Ledger-RAG stores source evidence" not in json.dumps(summary)


def test_review_fails_when_required_artifact_is_missing(tmp_path):
    _write_smoke_artifacts(tmp_path)
    (tmp_path / "response.json").unlink()

    summary = review_smoke_artifacts(tmp_path, budget_ceiling_usd=10)

    assert summary["review_status"] == "failed"
    assert "missing_artifact_response.json" in summary["blockers"]


def test_review_fails_when_cost_exceeds_budget(tmp_path):
    _write_smoke_artifacts(tmp_path)
    cost_path = tmp_path / "cost_estimate.json"
    cost = json.loads(cost_path.read_text(encoding="utf-8"))
    cost["estimated_cost_usd"] = 11
    _write_json(cost_path, cost)

    summary = review_smoke_artifacts(tmp_path, budget_ceiling_usd=10)

    assert summary["review_status"] == "failed"
    assert "estimated_cost_exceeds_budget" in summary["blockers"]


def test_write_summary_yaml_excludes_raw_response_content(tmp_path):
    _write_smoke_artifacts(tmp_path / "artifacts")
    summary = review_smoke_artifacts(tmp_path / "artifacts", budget_ceiling_usd=10)
    output = tmp_path / "summary.yaml"

    write_summary_yaml(output, summary)

    text = output.read_text(encoding="utf-8")
    assert "review_status: passed" in text
    assert "Ledger-RAG stores source evidence" not in text
    assert "response.json:" in text


def test_cli_writes_summary_and_require_pass_succeeds(tmp_path):
    artifacts = tmp_path / "artifacts"
    _write_smoke_artifacts(artifacts)
    summary_path = tmp_path / "summary.yaml"

    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--artifact-dir",
            str(artifacts),
            "--summary",
            str(summary_path),
            "--write-summary",
            "--require-pass",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["review_status"] == "passed"
    assert summary_path.is_file()

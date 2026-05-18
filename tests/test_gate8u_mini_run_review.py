import json
import subprocess
import sys
from pathlib import Path

from ledger_rag_main.mini_run_review import review_mini_run


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "review_gate8u_mini_run.py"


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _fixture(tmp_path):
    run_dir = tmp_path / "run"
    questions = tmp_path / "questions.jsonl"
    _write_jsonl(
        questions,
        [
            {
                "question_id": "q1",
                "answer": "Yoruba people",
                "support_evidence_refs": [{"source_doc_id": "support_doc"}],
            },
            {
                "question_id": "q2",
                "answer": "Scanian dialects",
                "support_evidence_refs": [{"source_doc_id": "missing_doc"}],
            },
        ],
    )
    _write_jsonl(
        run_dir / "run_records.jsonl",
        [
            {
                "input": {"question_id": "q1"},
                "answer": {"global_answer": "Yoruba people", "refusal_label": "answered", "atomic_claims": [{"claim_id": "c1"}]},
                "citations": [{"claim_id": "c1", "cited_evidence_id": "support_doc"}],
                "retrieved_evidence": [{"source_doc_id": "support_doc"}],
                "run_metadata": {"baseline_family": "vanilla_rag", "usage": {"prompt_tokens": 10, "completion_tokens": 5}, "estimated_cost_usd": 0.1},
            },
            {
                "input": {"question_id": "q2"},
                "answer": {"global_answer": "insufficient", "refusal_label": "insufficient_evidence", "atomic_claims": []},
                "citations": [],
                "retrieved_evidence": [{"source_doc_id": "wrong_doc"}],
                "run_metadata": {"baseline_family": "ledger_validator", "usage": {"prompt_tokens": 20, "completion_tokens": 6}, "estimated_cost_usd": 0.2},
            },
        ],
    )
    _write_json(run_dir / "cost_summary.json", {"estimated_cost_usd": 0.3})
    return run_dir, questions


def test_review_mini_run_reports_retrieval_refusal_citation_and_cost(tmp_path):
    run_dir, questions = _fixture(tmp_path)

    summary = review_mini_run(run_dir, questions)

    assert summary["run_record_count"] == 2
    assert summary["overall"]["support_hit_count"] == 1
    assert summary["overall"]["support_hit_rate"] == 0.5
    assert summary["overall"]["refusal_count"] == 1
    assert summary["overall"]["citation_count"] == 1
    assert summary["overall"]["estimated_cost_usd"] == 0.3
    assert summary["by_baseline"]["vanilla_rag"]["support_hit_rate"] == 1.0
    assert summary["by_baseline"]["ledger_validator"]["support_hit_rate"] == 0.0
    assert summary["recommendation"] == "fix_retrieval_before_scaling"


def test_cli_writes_summary_without_raw_answers(tmp_path):
    run_dir, questions = _fixture(tmp_path)
    output = tmp_path / "review.yaml"

    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--run-dir",
            str(run_dir),
            "--questions",
            str(questions),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    text = output.read_text(encoding="utf-8")
    assert "fix_retrieval_before_scaling" in text
    assert "Yoruba people" not in text

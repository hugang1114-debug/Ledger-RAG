import json
import subprocess
import sys
from pathlib import Path

from ledger_rag_smoke.deepseek_smoke import (
    build_chat_request,
    build_metric_record,
    build_run_record,
    estimate_cost_usd,
    extract_json_answer,
    load_env_file,
    run_smoke,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "gate7_offline" / "pilot.json"
CLI = ROOT / "scripts" / "run_gate8p_deepseek_smoke.py"


def test_build_chat_request_uses_deepseek_v4_pro_and_json_output():
    request = build_chat_request(
        question_text="What does Ledger-RAG store source evidence as?",
        evidence=[
            {
                "evidence_id": "span_1",
                "source_doc_id": "doc_ledger_arch",
                "text": "Ledger-RAG stores source evidence as replayable ledger spans.",
            }
        ],
        model_id="deepseek-v4-pro",
    )

    assert request["model"] == "deepseek-v4-pro"
    assert request["thinking"] == {"type": "disabled"}
    assert request["response_format"] == {"type": "json_object"}
    assert request["stream"] is False
    assert "span_1" in request["messages"][1]["content"]


def test_extract_json_answer_strips_markdown_fence():
    answer = extract_json_answer(
        '```json\n{"global_answer":"A","atomic_claims":[{"claim_id":"c1","claim_text":"A"}],"citations":[{"claim_id":"c1","cited_evidence_id":"e1"}]}\n```'
    )

    assert answer["global_answer"] == "A"
    assert answer["atomic_claims"][0]["claim_id"] == "c1"
    assert answer["citations"][0]["cited_evidence_id"] == "e1"


def test_estimate_cost_uses_deepseek_gate8_prices():
    assert estimate_cost_usd({"prompt_tokens": 1_000_000, "completion_tokens": 1_000_000}) == 1.305


def test_build_run_and_metric_records_have_required_sections():
    run_metadata = {
        "baseline_family": "ledger_validator",
        "run_id": "gate8p_deepseek_smoke_test",
        "code_version": "test",
        "config_version": "gate8p_deepseek_smoke_v1",
        "seed": 0,
        "started_at": "2026-05-17T00:00:00Z",
        "completed_at": "2026-05-17T00:00:01Z",
        "latency_ms": 1.0,
        "estimated_cost_usd": 0.001,
        "hardware": "local_cpu_remote_deepseek_api",
        "notes": "test",
    }
    answer = {
        "global_answer": "Ledger-RAG stores source evidence as replayable ledger spans.",
        "atomic_claims": [{"claim_id": "c1", "claim_text": "Ledger-RAG stores source evidence as replayable ledger spans."}],
        "citations": [{"claim_id": "c1", "cited_evidence_id": "span_1"}],
    }
    evidence = [{"rank": 1, "evidence_id": "span_1", "source_doc_id": "doc_ledger_arch", "source_uri": "fixture://doc", "text": "Ledger-RAG stores source evidence as replayable ledger spans.", "score": 1.0, "retriever_name": "offline_lexical", "ledger_span_id": "span_1", "source_hash": "abc", "replay_path": "fixture://doc#span=0"}]

    run_record = build_run_record(
        dataset_id="gate7_offline",
        split="pilot",
        question_id="q_traceability",
        question_text="What does Ledger-RAG store source evidence as?",
        corpus_snapshot_id="gate7_offline_v1",
        evidence=evidence,
        answer_payload=answer,
        verdicts=[],
        run_metadata=run_metadata,
    )
    metric_record = build_metric_record(run_record)

    assert {"input", "retrieved_evidence", "answer", "citations", "verdicts", "run_metadata"} <= set(run_record)
    assert {"metric_record", "retrieval", "answer_quality", "attribution", "system", "aggregation"} <= set(metric_record)


def test_run_smoke_writes_artifacts_with_fake_transport(tmp_path):
    def fake_transport(_base_url, _api_key, request_payload, _timeout_seconds):
        assert request_payload["model"] == "deepseek-v4-pro"
        return {
            "id": "fake-response",
            "model": "deepseek-v4-pro",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "global_answer": "Ledger-RAG stores source evidence as replayable ledger spans with stable identifiers and hashes.",
                                "atomic_claims": [
                                    {
                                        "claim_id": "c1",
                                        "claim_text": "Ledger-RAG stores source evidence as replayable ledger spans with stable identifiers and hashes.",
                                    }
                                ],
                                "citations": [{"claim_id": "c1", "cited_evidence_id": "span_fake"}],
                            }
                        )
                    }
                }
            ],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        }

    output = run_smoke(
        fixture_path=FIXTURE,
        output_path=tmp_path,
        api_key="fake-key",
        base_url="https://api.deepseek.com",
        question_id="q_traceability",
        transport=fake_transport,
    )

    for name in ("request.json", "response.json", "run_record.json", "metric_record.json", "cost_estimate.json"):
        assert (output / name).is_file()

    request = json.loads((output / "request.json").read_text(encoding="utf-8"))
    assert "Authorization" not in json.dumps(request)


def test_load_env_file_reads_local_key_without_exporting_secret(tmp_path):
    env = tmp_path / ".env.local"
    env.write_text("DEEPSEEK_API_KEY=secret-value\nDEEPSEEK_BASE_URL=https://api.deepseek.com\n", encoding="utf-8")

    values = load_env_file(env)

    assert values["DEEPSEEK_API_KEY"] == "secret-value"
    assert values["DEEPSEEK_BASE_URL"] == "https://api.deepseek.com"


def test_cli_dry_run_writes_no_network_artifacts(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--fixture",
            str(FIXTURE),
            "--output",
            str(tmp_path),
            "--question-id",
            "q_traceability",
            "--dry-run",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "request.json").is_file()
    assert not (tmp_path / "response.json").exists()

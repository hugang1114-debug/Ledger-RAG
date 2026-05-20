import json
import io
import subprocess
import sys
from pathlib import Path

import pytest

from ledger_rag_main.hotpotqa_mini_run import (
    _build_metric_record,
    _build_run_record,
    build_chat_request,
    load_questions,
    normalize_citation_id,
    rank_evidence,
    run_hotpotqa_mini_run,
)


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "run_gate8t_hotpotqa_mini_run.py"
BATCH_CLI = ROOT / "scripts" / "run_gate8_main_v1_batch.py"


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _fixture_root(tmp_path):
    root = tmp_path / "fixture"
    dataset = root / "datasets" / "source_snapshots" / "hotpotqa" / "dev_distractor"
    index = root / "datasets" / "retrieval_indexes" / "main_v1" / "hotpotqa" / "dev_distractor"
    corpus_rows = [
        {
            "dataset_id": "hotpotqa",
            "split": "dev_distractor",
            "question_id": "q1",
            "source_doc_id": "doc_yoruba",
            "source_uri": "fixture://doc_yoruba",
            "title": "Ida sword",
            "text": "The Ida is a sword used by the Yoruba people of West Africa.",
            "sentences": [{"sentence_id": "s1", "sentence_index": 0, "text": "The Ida is a sword used by the Yoruba people of West Africa."}],
            "source_hash": "hash_yoruba",
        },
        {
            "dataset_id": "hotpotqa",
            "split": "dev_distractor",
            "question_id": "q2",
            "source_doc_id": "doc_scanian",
            "source_uri": "fixture://doc_scanian",
            "title": "Scanian dialect",
            "text": "Spettekaka is called spiddekaga in Scanian dialects.",
            "sentences": [{"sentence_id": "s2", "sentence_index": 0, "text": "Spettekaka is called spiddekaga in Scanian dialects."}],
            "source_hash": "hash_scanian",
        },
    ]
    question_rows = [
        {
            "dataset_id": "hotpotqa",
            "split": "dev_distractor",
            "question_id": "q1",
            "question_text": "Who used the Ida sword?",
            "answer": "Yoruba people",
            "support_evidence_refs": [{"source_doc_id": "doc_yoruba", "sentence_id": "s1"}],
        },
        {
            "dataset_id": "hotpotqa",
            "split": "dev_distractor",
            "question_id": "q2",
            "question_text": "Which dialect says spiddekaga?",
            "answer": "Scanian dialects",
            "support_evidence_refs": [{"source_doc_id": "doc_scanian", "sentence_id": "s2"}],
        },
    ]
    documents = [
        {"internal_doc_id": 0, "source_doc_id": "doc_yoruba", "title": "Ida sword", "source_uri": "fixture://doc_yoruba", "token_count": 12},
        {"internal_doc_id": 1, "source_doc_id": "doc_scanian", "title": "Scanian dialect", "source_uri": "fixture://doc_scanian", "token_count": 8},
    ]
    postings = [
        {"token": "ida", "document_frequency": 1, "total_term_frequency": 1, "postings": [{"internal_doc_id": 0, "term_frequency": 1}]},
        {"token": "sword", "document_frequency": 1, "total_term_frequency": 1, "postings": [{"internal_doc_id": 0, "term_frequency": 1}]},
        {"token": "spiddekaga", "document_frequency": 1, "total_term_frequency": 1, "postings": [{"internal_doc_id": 1, "term_frequency": 1}]},
        {"token": "dialect", "document_frequency": 1, "total_term_frequency": 1, "postings": [{"internal_doc_id": 1, "term_frequency": 1}]},
    ]
    _write_jsonl(dataset / "processed" / "corpus.jsonl", corpus_rows)
    _write_jsonl(dataset / "processed" / "questions.jsonl", question_rows)
    _write_jsonl(index / "documents.jsonl", documents)
    _write_jsonl(index / "postings.jsonl", postings)
    _write_json(
        index / "index_manifest.json",
        {
            "dataset_id": "hotpotqa",
            "split": "dev_distractor",
            "source_snapshot_id": "hotpotqa_fixture_snapshot",
            "retriever_family": "lexical",
            "paths": {
                "documents": str(index / "documents.jsonl"),
                "postings": str(index / "postings.jsonl"),
                "index_manifest": str(index / "index_manifest.json"),
            },
        },
    )
    _write_json(
        root / "snapshots" / "main_v1" / "source_snapshots.json",
        {
            "gate": "gate8_main_comparison",
            "version": 1,
            "snapshots": [
                {
                    "dataset_id": "hotpotqa",
                    "dataset_name": "HotpotQA",
                    "dataset_path": str(dataset),
                    "split": "dev_distractor",
                    "source_snapshot_id": "hotpotqa_fixture_snapshot",
                    "retrieval_index_path": str(index / "index_manifest.json"),
                    "status": "ready",
                }
            ],
        },
    )
    return root


def test_load_questions_selects_deterministic_first_n(tmp_path):
    root = _fixture_root(tmp_path)
    questions = load_questions(root / "datasets" / "source_snapshots" / "hotpotqa" / "dev_distractor" / "processed" / "questions.jsonl", 1)

    assert [question["question_id"] for question in questions] == ["q1"]


def test_rank_evidence_returns_stable_index_backed_records(tmp_path):
    root = _fixture_root(tmp_path)
    manifest = root / "datasets" / "retrieval_indexes" / "main_v1" / "hotpotqa" / "dev_distractor" / "index_manifest.json"
    corpus = root / "datasets" / "source_snapshots" / "hotpotqa" / "dev_distractor" / "processed" / "corpus.jsonl"

    evidence = rank_evidence("Who used the Ida sword?", manifest, corpus, top_k=1)

    assert evidence[0]["source_doc_id"] == "doc_yoruba"
    assert evidence[0]["evidence_id"] == "doc_yoruba"
    assert evidence[0]["ledger_span_id"] == "doc_yoruba"


def test_rank_evidence_can_filter_to_hotpotqa_question_context(tmp_path):
    root = _fixture_root(tmp_path)
    manifest = root / "datasets" / "retrieval_indexes" / "main_v1" / "hotpotqa" / "dev_distractor" / "index_manifest.json"
    corpus = root / "datasets" / "source_snapshots" / "hotpotqa" / "dev_distractor" / "processed" / "corpus.jsonl"

    evidence = rank_evidence(
        "Which dialect says spiddekaga?",
        manifest,
        corpus,
        top_k=8,
        allowed_source_doc_ids=["doc_scanian"],
    )

    assert [item["source_doc_id"] for item in evidence] == ["doc_scanian"]


def test_runner_uses_question_context_filter_for_retrieval(tmp_path):
    root = _fixture_root(tmp_path)
    output = tmp_path / "out"

    def fake_transport(_base_url, _api_key, request_payload, _timeout_seconds):
        content = {
            "global_answer": "Scanian dialects" if "doc_scanian" in json.dumps(request_payload) else "Yoruba people",
            "atomic_claims": [{"claim_id": "c1", "text": "Answer from scoped context.", "citations": ["doc_scanian"]}],
            "citations": [{"claim_id": "c1", "cited_evidence_id": "doc_scanian"}],
            "refusal": False,
            "refusal_reason": "",
        }
        return {
            "choices": [{"message": {"content": json.dumps(content)}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }

    run_hotpotqa_mini_run(
        repo_root=root,
        output_path=output,
        sample_count=2,
        baselines=["vanilla_rag"],
        api_key="fake-key",
        base_url="https://api.deepseek.com",
        transport=fake_transport,
    )
    retrieval_records = [json.loads(line) for line in (output / "retrieval_records.jsonl").read_text(encoding="utf-8").splitlines()]

    assert [item["source_doc_id"] for item in retrieval_records[0]["evidence"]] == ["doc_yoruba"]
    assert [item["source_doc_id"] for item in retrieval_records[1]["evidence"]] == ["doc_scanian"]


def test_build_chat_request_includes_frozen_metadata_and_baseline_policy():
    request = build_chat_request(
        baseline_family="ledger_validator",
        question_text="Who used the Ida sword?",
        evidence=[{"evidence_id": "doc_yoruba", "ledger_span_id": "doc_yoruba", "title": "Ida sword", "text": "The Ida is used by Yoruba people."}],
        prompt_version="gate8l_ledger_validator_v1",
        max_output_tokens=512,
    )

    assert request["model"] == "deepseek-v4-pro"
    assert request["temperature"] == 0
    assert request["max_tokens"] == 512
    assert "ledger_validator" in request["messages"][0]["content"]
    assert "gate8l_ledger_validator_v1" in request["messages"][0]["content"]
    assert "valid_evidence_ids" in request["messages"][0]["content"]
    assert "valid_evidence_ids" in request["messages"][1]["content"]
    assert "ledger_span_id=doc_yoruba" in request["messages"][1]["content"]


def test_citation_id_normalization_is_conservative():
    assert normalize_citation_id(" `doc_yoruba` ") == "doc_yoruba"
    assert normalize_citation_id("'doc_yoruba'") == "doc_yoruba"
    assert normalize_citation_id('"doc_yoruba"') == "doc_yoruba"


def test_run_record_sanitizes_invalid_citations_and_records_diagnostics():
    question = {"question_id": "q1", "question_text": "Who used the Ida sword?", "answer": "Yoruba people"}
    evidence = [
        {
            "evidence_id": "doc_yoruba",
            "ledger_span_id": "doc_yoruba",
            "source_doc_id": "doc_yoruba",
            "text": "The Ida is a sword used by the Yoruba people of West Africa.",
        }
    ]
    answer_payload = {
        "global_answer": "Yoruba people",
        "atomic_claims": [
            {"claim_id": "c1", "text": "The Ida was used by Yoruba people."},
            {"claim_id": "c2", "text": "An invalid citation should be dropped."},
        ],
        "citations": [
            {"claim_id": "c1", "cited_evidence_id": " `doc_yoruba` "},
            {"claim_id": "c2", "cited_evidence_id": "not_a_real_evidence_id"},
        ],
        "refusal": False,
    }

    record = _build_run_record(
        "run1",
        "ledger_validator",
        question,
        evidence,
        answer_payload,
        {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        100,
        "prompt_v1",
        "snapshot_v1",
        "hotpotqa",
        "dev_distractor",
    )

    assert [citation["cited_evidence_id"] for citation in record["citations"]] == ["doc_yoruba"]
    assert record["citation_diagnostics"]["valid_citation_count"] == 1
    assert record["citation_diagnostics"]["invalid_citation_count"] == 1
    assert record["citation_diagnostics"]["uncited_claim_count"] == 1
    assert record["citation_diagnostics"]["invalid_citations"][0]["normalized_cited_evidence_id"] == "not_a_real_evidence_id"


def test_metric_record_uses_sanitized_citations_not_raw_invalid_citations():
    question = {"question_id": "q1", "question_text": "Who used the Ida sword?", "answer": "Yoruba people"}
    evidence = [
        {
            "evidence_id": "doc_yoruba",
            "ledger_span_id": "doc_yoruba",
            "source_doc_id": "doc_yoruba",
            "text": "The Ida is a sword used by the Yoruba people of West Africa.",
        }
    ]
    record = _build_run_record(
        "run1",
        "citation_only",
        question,
        evidence,
        {
            "global_answer": "Yoruba people",
            "atomic_claims": [{"claim_id": "c1", "text": "The Ida was used by Yoruba people."}],
            "citations": [{"claim_id": "c1", "cited_evidence_id": "unknown"}],
            "refusal": False,
        },
        {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        100,
        "prompt_v1",
        "snapshot_v1",
        "hotpotqa",
        "dev_distractor",
    )
    metric = _build_metric_record(record)

    assert record["citations"] == []
    assert metric["attribution"]["citation_count"] == 0
    assert metric["attribution"]["invalid_citation_count"] == 1
    assert metric["attribution"]["uncited_claim_count"] == 1


def test_runner_with_fake_transport_writes_required_artifacts(tmp_path):
    root = _fixture_root(tmp_path)
    output = tmp_path / "out"

    def fake_transport(_base_url, _api_key, request_payload, _timeout_seconds):
        content = {
            "global_answer": "Yoruba people",
            "atomic_claims": [{"claim_id": "c1", "text": "The Ida was used by Yoruba people.", "citations": ["doc_yoruba"]}],
            "citations": [{"claim_id": "c1", "cited_evidence_id": "doc_yoruba"}],
            "refusal": False,
            "refusal_reason": "",
        }
        return {
            "choices": [{"message": {"content": json.dumps(content)}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }

    summary = run_hotpotqa_mini_run(
        repo_root=root,
        output_path=output,
        sample_count=1,
        baselines=["vanilla_rag", "ledger_validator"],
        api_key="fake-key",
        base_url="https://api.deepseek.com",
        transport=fake_transport,
    )

    assert (output / "run_records.jsonl").is_file()
    assert (output / "metric_records.jsonl").is_file()
    assert (output / "retrieval_records.jsonl").is_file()
    assert (output / "request_manifest.jsonl").is_file()
    assert (output / "cost_summary.json").is_file()
    assert (output / "mini_run_summary.yaml").is_file()
    assert summary["success_count"] == 2
    assert summary["failure_count"] == 0
    assert summary["total_prompt_tokens"] == 200
    assert "fake-key" not in (output / "request_manifest.jsonl").read_text(encoding="utf-8")
    run_record = json.loads((output / "run_records.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert "citation_diagnostics" in run_record


def test_runner_retries_provider_until_configured_attempt_limit(tmp_path):
    root = _fixture_root(tmp_path)
    output = tmp_path / "out"
    attempts = {"count": 0}

    def flaky_transport(_base_url, _api_key, _request_payload, _timeout_seconds):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("temporary provider disconnect")
        content = {
            "global_answer": "Yoruba people",
            "atomic_claims": [{"claim_id": "c1", "text": "The Ida was used by Yoruba people."}],
            "citations": [{"claim_id": "c1", "cited_evidence_id": "doc_yoruba"}],
            "refusal": False,
            "refusal_reason": "",
        }
        return {
            "choices": [{"message": {"content": json.dumps(content)}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }

    summary = run_hotpotqa_mini_run(
        repo_root=root,
        output_path=output,
        sample_count=1,
        baselines=["vanilla_rag"],
        api_key="fake-key",
        base_url="https://api.deepseek.com",
        transport=flaky_transport,
        max_provider_attempts=3,
    )

    request_manifest = [json.loads(line) for line in (output / "request_manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    assert attempts["count"] == 3
    assert summary["success_count"] == 1
    assert summary["failure_count"] == 0
    assert request_manifest[0]["provider_attempt_count"] == 3
    assert request_manifest[0]["valid_evidence_ids"] == ["doc_yoruba"]


def test_runner_resume_from_skips_existing_run_records(tmp_path):
    root = _fixture_root(tmp_path)
    first_output = tmp_path / "first"
    resumed_output = tmp_path / "resumed"

    def first_transport(_base_url, _api_key, _request_payload, _timeout_seconds):
        content = {
            "global_answer": "Yoruba people",
            "atomic_claims": [{"claim_id": "c1", "text": "The Ida was used by Yoruba people."}],
            "citations": [{"claim_id": "c1", "cited_evidence_id": "doc_yoruba"}],
            "refusal": False,
            "refusal_reason": "",
        }
        return {
            "choices": [{"message": {"content": json.dumps(content)}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }

    run_hotpotqa_mini_run(
        repo_root=root,
        output_path=first_output,
        sample_count=1,
        baselines=["vanilla_rag"],
        api_key="fake-key",
        base_url="https://api.deepseek.com",
        transport=first_transport,
    )
    calls = []

    def resume_transport(_base_url, _api_key, request_payload, _timeout_seconds):
        calls.append(request_payload["messages"][0]["content"])
        content = {
            "global_answer": "Yoruba people",
            "atomic_claims": [{"claim_id": "c1", "text": "The Ida was used by Yoruba people."}],
            "citations": [{"claim_id": "c1", "cited_evidence_id": "doc_yoruba"}],
            "refusal": False,
            "refusal_reason": "",
        }
        return {
            "choices": [{"message": {"content": json.dumps(content)}}],
            "usage": {"prompt_tokens": 80, "completion_tokens": 40, "total_tokens": 120},
        }

    summary = run_hotpotqa_mini_run(
        repo_root=root,
        output_path=resumed_output,
        sample_count=1,
        baselines=["vanilla_rag", "ledger_validator"],
        api_key="fake-key",
        base_url="https://api.deepseek.com",
        transport=resume_transport,
        resume_from=first_output,
    )

    run_records = [json.loads(line) for line in (resumed_output / "run_records.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(calls) == 1
    assert "ledger_validator" in calls[0]
    assert summary["success_count"] == 2
    assert summary["resumed_record_count"] == 1
    assert summary["total_prompt_tokens"] == 180
    assert summary["total_completion_tokens"] == 90
    assert {record["run_metadata"]["baseline_family"] for record in run_records} == {"vanilla_rag", "ledger_validator"}


def test_runner_writes_progress_file_and_console_lines(tmp_path):
    root = _fixture_root(tmp_path)
    output = tmp_path / "out"
    progress_stream = io.StringIO()

    def fake_transport(_base_url, _api_key, _request_payload, _timeout_seconds):
        content = {
            "global_answer": "Yoruba people",
            "atomic_claims": [{"claim_id": "c1", "text": "The Ida was used by Yoruba people."}],
            "citations": [{"claim_id": "c1", "cited_evidence_id": "doc_yoruba"}],
            "refusal": False,
            "refusal_reason": "",
        }
        return {
            "choices": [{"message": {"content": json.dumps(content)}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }

    summary = run_hotpotqa_mini_run(
        repo_root=root,
        output_path=output,
        sample_count=1,
        baselines=["vanilla_rag", "ledger_validator"],
        api_key="fake-key",
        base_url="https://api.deepseek.com",
        transport=fake_transport,
        progress_path=output / "progress.json",
        progress_stream=progress_stream,
    )

    progress = json.loads((output / "progress.json").read_text(encoding="utf-8"))
    console_output = progress_stream.getvalue()
    assert summary["success_count"] == 2
    assert progress["dataset_id"] == "hotpotqa"
    assert progress["attempted_call_count"] == 2
    assert progress["success_count"] == 2
    assert progress["failure_count"] == 0
    assert progress["status"] == "completed"
    assert "[hotpotqa]" in console_output
    assert "ok=2" in console_output


def test_runner_accepts_retrieval_top_k_override(tmp_path):
    root = _fixture_root(tmp_path)
    output = tmp_path / "out"

    summary = run_hotpotqa_mini_run(
        repo_root=root,
        output_path=output,
        sample_count=1,
        baselines=["vanilla_rag"],
        api_key="fake-key",
        base_url="https://api.deepseek.com",
        dry_run=True,
        retrieval_top_k=16,
    )

    run_record = json.loads((output / "run_records.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert summary["max_evidence_items"] == 16
    assert run_record["input"]["retrieval_config"]["top_k"] == 1


def test_cli_dry_run_writes_no_raw_response(tmp_path):
    root = _fixture_root(tmp_path)
    output = tmp_path / "dry"
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--repo-root",
            str(root),
            "--sample-count",
            "1",
            "--baselines",
            "vanilla_rag",
            "ledger_validator",
            "--output",
            str(output),
            "--dry-run",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (output / "request_manifest.jsonl").is_file()
    assert not (output / "raw_responses.jsonl").exists()


def test_main_v1_batch_cli_dry_run_writes_batch_summary(tmp_path):
    root = _fixture_root(tmp_path)
    output = tmp_path / "batch"
    result = subprocess.run(
        [
            sys.executable,
            str(BATCH_CLI),
            "--repo-root",
            str(root),
            "--datasets",
            "hotpotqa",
            "--sample-count",
            "1",
            "--baselines",
            "vanilla_rag",
            "ledger_validator",
            "--output-root",
            str(output),
            "--dry-run",
            "--max-provider-attempts",
            "3",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads((output / "batch_summary.json").read_text(encoding="utf-8"))
    assert summary["dataset_count"] == 1
    assert summary["total_success_count"] == 2
    assert summary["total_failure_count"] == 0
    assert summary["max_provider_attempts"] == 3
    assert (output / "hotpotqa" / "run_records.jsonl").is_file()

import json
import subprocess
import sys
from pathlib import Path

from ledger_rag_pilot.generate import generate_answer
from ledger_rag_pilot.ingest import ingest_fixture, load_fixture
from ledger_rag_pilot.retrieve import retrieve
from ledger_rag_pilot.verify import verify_answer


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "gate7_offline" / "pilot.json"


def test_fixture_has_answerable_insufficient_and_distractor_cases():
    fixture = load_fixture(FIXTURE)

    case_types = {question["case_type"] for question in fixture["questions"]}
    has_distractor = any(question["distractor_doc_ids"] for question in fixture["questions"])

    assert "answerable" in case_types
    assert "insufficient" in case_types
    assert has_distractor


def test_ledger_span_hashes_are_deterministic():
    first = ingest_fixture(load_fixture(FIXTURE))
    second = ingest_fixture(load_fixture(FIXTURE))

    first_hashes = [span["span_hash"] for span in first["spans"]]
    second_hashes = [span["span_hash"] for span in second["spans"]]

    assert first_hashes == second_hashes
    assert len(set(first_hashes)) == len(first_hashes)


def test_retrieval_returns_expected_support_span_for_answerable_questions():
    fixture = load_fixture(FIXTURE)
    ledger = ingest_fixture(fixture)

    for question in fixture["questions"]:
        if question["case_type"] != "answerable":
            continue

        results = retrieve(question["question_text"], ledger["spans"], top_k=2)
        returned_doc_ids = {item["source_doc_id"] for item in results}

        assert set(question["support_doc_ids"]) & returned_doc_ids


def test_verifier_supports_answerable_claims_and_marks_insufficient_cases():
    fixture = load_fixture(FIXTURE)
    ledger = ingest_fixture(fixture)

    for question in fixture["questions"]:
        retrieval = retrieve(question["question_text"], ledger["spans"], top_k=2)
        answer = generate_answer(question, retrieval)
        verdicts = verify_answer(question, answer, retrieval)
        labels = {verdict["label"] for verdict in verdicts}

        if question["case_type"] == "answerable":
            assert labels == {"support"}
        else:
            assert labels == {"insufficient"}


def test_runner_writes_required_artifacts(tmp_path):
    output = tmp_path / "run"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_gate7_offline_pilot.py"),
            "--fixture",
            str(FIXTURE),
            "--output",
            str(output),
        ],
        check=True,
        cwd=ROOT,
    )

    expected_files = {
        "run_record.json",
        "metric_record.json",
        "ledger.jsonl",
        "retrieval.jsonl",
        "claims.jsonl",
        "verdicts.jsonl",
    }

    assert expected_files == {path.name for path in output.iterdir()}


def test_output_json_contains_required_contract_sections(tmp_path):
    output = tmp_path / "run"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_gate7_offline_pilot.py"),
            "--fixture",
            str(FIXTURE),
            "--output",
            str(output),
        ],
        check=True,
        cwd=ROOT,
    )

    run_record = json.loads((output / "run_record.json").read_text(encoding="utf-8"))
    metric_record = json.loads((output / "metric_record.json").read_text(encoding="utf-8"))

    assert {"input", "retrieved_evidence", "answer", "citations", "verdicts", "run_metadata"} <= set(run_record)
    assert {"metric_record", "retrieval", "answer_quality", "attribution", "system", "aggregation"} <= set(metric_record)

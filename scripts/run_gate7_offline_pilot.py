import argparse
import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_pilot.generate import generate_answer
from ledger_rag_pilot.ingest import ingest_fixture, load_fixture
from ledger_rag_pilot.metrics import compute_metric_record
from ledger_rag_pilot.retrieve import retrieve
from ledger_rag_pilot.verify import verify_answer


def write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def build_run_record(fixture, question_results, run_metadata):
    retrieved_evidence = []
    atomic_claims = []
    citations = []
    verdicts = []

    for item in question_results:
        question_id = item["question"]["question_id"]
        for evidence in item["retrieval"]:
            row = dict(evidence)
            row["question_id"] = question_id
            retrieved_evidence.append(row)
        for claim in item["answer"]["atomic_claims"]:
            row = dict(claim)
            row["question_id"] = question_id
            atomic_claims.append(row)
        for citation in item["answer"]["citations"]:
            row = dict(citation)
            row["question_id"] = question_id
            citations.append(row)
        for verdict in item["verdicts"]:
            row = dict(verdict)
            row["question_id"] = question_id
            verdicts.append(row)

    return {
        "input": {
            "dataset_id": fixture["dataset_id"],
            "split": fixture["split"],
            "question_count": len(fixture["questions"]),
            "question_ids": [question["question_id"] for question in fixture["questions"]],
            "corpus_snapshot_id": fixture["corpus_snapshot_id"],
            "retrieval_config": {
                "retriever_family": "offline_lexical",
                "top_k": 2,
                "reranker": "none",
                "evidence_budget": "2 spans per question",
            },
            "generation_config": {
                "model_id": "offline_rule_based",
                "prompt_version": "not_applicable",
                "answer_style": "fixture_expected_claims",
                "max_output_tokens": 0,
                "temperature": 0,
            },
        },
        "retrieved_evidence": retrieved_evidence,
        "answer": {
            "global_answer": "offline Gate 7 pilot batch",
            "refusal_label": "answered",
            "atomic_claims": atomic_claims,
        },
        "citations": citations,
        "verdicts": verdicts,
        "run_metadata": run_metadata,
    }


def run_pilot(fixture_path, output_path):
    started = time.perf_counter()
    fixture = load_fixture(fixture_path)
    ledger = ingest_fixture(fixture)
    question_results = []

    for question in fixture["questions"]:
        retrieval = retrieve(question["question_text"], ledger["spans"], top_k=2)
        answer = generate_answer(question, retrieval)
        verdicts = verify_answer(question, answer, retrieval)
        question_results.append(
            {
                "question": question,
                "retrieval": retrieval,
                "answer": answer,
                "verdicts": verdicts,
            }
        )

    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    run_metadata = {
        "baseline_family": "ledger_validator",
        "run_id": "gate7_offline_latest",
        "code_version": "working_tree",
        "config_version": "gate7_offline_v1",
        "seed": 0,
        "started_at": "not_recorded_for_deterministic_offline_pilot",
        "completed_at": "not_recorded_for_deterministic_offline_pilot",
        "latency_ms": latency_ms,
        "estimated_cost_usd": 0.0,
        "hardware": "local_cpu",
        "notes": "offline synthetic pilot; not a paper result",
    }

    output = Path(output_path)
    output.mkdir(parents=True, exist_ok=True)

    ledger_rows = ledger["documents"] + ledger["chunks"] + ledger["spans"]
    write_jsonl(output / "ledger.jsonl", ledger_rows)
    write_jsonl(
        output / "retrieval.jsonl",
        [
            {"question_id": item["question"]["question_id"], **evidence}
            for item in question_results
            for evidence in item["retrieval"]
        ],
    )
    write_jsonl(
        output / "claims.jsonl",
        [
            {"question_id": item["question"]["question_id"], **claim}
            for item in question_results
            for claim in item["answer"]["atomic_claims"]
        ],
    )
    write_jsonl(
        output / "verdicts.jsonl",
        [
            {"question_id": item["question"]["question_id"], **verdict}
            for item in question_results
            for verdict in item["verdicts"]
        ],
    )

    ledger_size_mb = round((output / "ledger.jsonl").stat().st_size / (1024 * 1024), 6)
    index_size_mb = ledger_size_mb
    run_record = build_run_record(fixture, question_results, run_metadata)
    metric_record = compute_metric_record(fixture, question_results, run_metadata, ledger_size_mb, index_size_mb)

    write_json(output / "run_record.json", run_record)
    write_json(output / "metric_record.json", metric_record)
    return output


def main():
    parser = argparse.ArgumentParser(description="Run the deterministic Gate 7 offline pilot.")
    parser.add_argument("--fixture", required=True, help="Path to the Gate 7 fixture JSON.")
    parser.add_argument("--output", required=True, help="Output artifact directory.")
    args = parser.parse_args()
    output = run_pilot(args.fixture, args.output)
    print(f"wrote_gate7_offline_pilot={output}")


if __name__ == "__main__":
    main()


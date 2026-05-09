import json
import subprocess
import sys
from pathlib import Path

from ledger_rag_snapshot.hotpotqa import (
    build_hotpotqa_snapshot_from_raw,
    load_hotpotqa_records,
    process_hotpotqa_records,
    update_hotpotqa_registry_record,
)
from ledger_rag_snapshot.registry import find_gate8_blockers, validate_registry


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "build_hotpotqa_source_snapshot.py"


def fixture_records():
    return [
        {
            "_id": "q1",
            "question": "Which city hosts the museum linked to the river?",
            "answer": "Riverton",
            "type": "bridge",
            "level": "easy",
            "supporting_facts": [["River Museum", 0], ["Riverton", 1]],
            "context": [
                ["River Museum", ["The River Museum is located in Riverton.", "It opened in 1999."]],
                ["Riverton", ["Riverton sits beside the North River.", "The city hosts the River Museum."]],
                ["Noise Page", ["This sentence is unrelated."]],
            ],
        },
        {
            "_id": "q2",
            "question": "What opened in 1999?",
            "answer": "The River Museum",
            "type": "comparison",
            "level": "medium",
            "supporting_facts": [["River Museum", 1]],
            "context": [
                ["River Museum", ["The River Museum is located in Riverton.", "It opened in 1999."]],
            ],
        },
    ]


def write_fixture_raw(path, records):
    path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def registry_payload():
    return {
        "version": 1,
        "gate": "gate8_main_comparison",
        "status": "readiness_in_progress",
        "snapshots": [
            {
                "dataset_id": "hotpotqa",
                "dataset_name": "HotpotQA",
                "decision": "main_v1",
                "split": "dev_distractor",
                "official_url": "https://hotpotqa.github.io/",
                "license_note": "unset",
                "source_snapshot_id": "unset",
                "dataset_path": "unset",
                "raw_data_hash": "unset",
                "processed_corpus_hash": "unset",
                "split_hash": "unset",
                "build_command_record": "unset",
                "retrieval_index_path": "unset",
                "storage_class": "unknown",
                "status": "pending",
                "notes": [],
            },
            {
                "dataset_id": "2wikimultihopqa",
                "dataset_name": "2WikiMultihopQA",
                "decision": "main_v1",
                "split": "dev",
                "official_url": "https://github.com/Alab-NII/2wikimultihop",
                "license_note": "unset",
                "source_snapshot_id": "unset",
                "dataset_path": "unset",
                "raw_data_hash": "unset",
                "processed_corpus_hash": "unset",
                "split_hash": "unset",
                "build_command_record": "unset",
                "retrieval_index_path": "unset",
                "storage_class": "unknown",
                "status": "pending",
                "notes": [],
            },
            {
                "dataset_id": "musique",
                "dataset_name": "MuSiQue",
                "decision": "main_v1",
                "split": "dev",
                "official_url": "https://github.com/StonyBrookNLP/musique",
                "license_note": "unset",
                "source_snapshot_id": "unset",
                "dataset_path": "unset",
                "raw_data_hash": "unset",
                "processed_corpus_hash": "unset",
                "split_hash": "unset",
                "build_command_record": "unset",
                "retrieval_index_path": "unset",
                "storage_class": "unknown",
                "status": "pending",
                "notes": [],
            },
        ],
    }


def test_process_hotpotqa_records_preserves_supporting_fact_refs():
    snapshot = process_hotpotqa_records(
        fixture_records(),
        split="dev_distractor",
        source_uri="official://hotpotqa/dev_distractor",
    )

    assert [row["question_id"] for row in snapshot["questions"]] == ["q1", "q2"]
    assert len(snapshot["corpus"]) == 4
    assert snapshot["questions"][0]["support_evidence_refs"] == [
        {
            "title": "River Museum",
            "sentence_index": 0,
            "source_doc_id": "hotpotqa_q1_doc_0_river_museum",
            "sentence_id": "hotpotqa_q1_doc_0_river_museum_sent_0",
        },
        {
            "title": "Riverton",
            "sentence_index": 1,
            "source_doc_id": "hotpotqa_q1_doc_1_riverton",
            "sentence_id": "hotpotqa_q1_doc_1_riverton_sent_1",
        },
    ]
    assert snapshot["split_manifest"]["question_ids"] == ["q1", "q2"]


def test_build_hotpotqa_snapshot_outputs_deterministic_files(tmp_path):
    raw_path = tmp_path / "raw.json"
    output_root = tmp_path / "snapshot"
    write_fixture_raw(raw_path, fixture_records())

    first = build_hotpotqa_snapshot_from_raw(
        raw_path=raw_path,
        output_root=output_root,
        split="dev_distractor",
        source_url="official://hotpotqa/dev_distractor",
        eval_script_path=None,
        command_record={"command": "fixture build"},
    )
    second = build_hotpotqa_snapshot_from_raw(
        raw_path=raw_path,
        output_root=output_root,
        split="dev_distractor",
        source_url="official://hotpotqa/dev_distractor",
        eval_script_path=None,
        command_record={"command": "fixture build"},
    )

    assert first["raw_data_hash"] == second["raw_data_hash"]
    assert first["processed_corpus_hash"] == second["processed_corpus_hash"]
    assert first["split_hash"] == second["split_hash"]
    assert first["source_snapshot_id"] == second["source_snapshot_id"]
    assert (output_root / "hotpotqa" / "dev_distractor" / "raw_manifest.json").exists()
    assert (output_root / "hotpotqa" / "dev_distractor" / "processed" / "corpus.jsonl").exists()
    assert (output_root / "hotpotqa" / "dev_distractor" / "processed" / "questions.jsonl").exists()
    assert (output_root / "hotpotqa" / "dev_distractor" / "processed" / "split_manifest.json").exists()
    assert (output_root / "hotpotqa" / "dev_distractor" / "snapshot_record.json").exists()


def test_registry_update_changes_only_hotpotqa_and_remains_gate8_blocked(tmp_path):
    raw_path = tmp_path / "raw.json"
    write_fixture_raw(raw_path, fixture_records())
    snapshot_record = build_hotpotqa_snapshot_from_raw(
        raw_path=raw_path,
        output_root=tmp_path / "snapshot",
        split="dev_distractor",
        source_url="official://hotpotqa/dev_distractor",
        eval_script_path=None,
        command_record={"command": "fixture build"},
    )
    registry = registry_payload()
    original_other_records = {
        record["dataset_id"]: dict(record)
        for record in registry["snapshots"]
        if record["dataset_id"] != "hotpotqa"
    }

    updated = update_hotpotqa_registry_record(registry, snapshot_record)
    hotpotqa = next(record for record in updated["snapshots"] if record["dataset_id"] == "hotpotqa")
    other_records = {
        record["dataset_id"]: record
        for record in updated["snapshots"]
        if record["dataset_id"] != "hotpotqa"
    }

    assert hotpotqa["status"] == "source_ready"
    assert hotpotqa["retrieval_index_path"] == "unset"
    assert hotpotqa["storage_class"] == "small"
    assert other_records == original_other_records
    assert validate_registry(updated) == []
    assert any(blocker["dataset_id"] == "hotpotqa" and blocker["field"] == "retrieval_index_path" for blocker in find_gate8_blockers(updated))


def test_cli_can_build_from_existing_raw_without_network(tmp_path):
    raw_path = tmp_path / "existing_raw.json"
    registry_path = tmp_path / "registry.json"
    output_root = tmp_path / "source_snapshots"
    write_fixture_raw(raw_path, fixture_records())
    registry_path.write_text(json.dumps(registry_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--registry",
            str(registry_path),
            "--output-root",
            str(output_root),
            "--split",
            "dev_distractor",
            "--existing-raw",
            str(raw_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    updated = json.loads(registry_path.read_text(encoding="utf-8"))
    hotpotqa = next(record for record in updated["snapshots"] if record["dataset_id"] == "hotpotqa")

    assert payload["status"] == "source_ready"
    assert hotpotqa["status"] == "source_ready"
    assert hotpotqa["source_snapshot_id"] == payload["source_snapshot_id"]

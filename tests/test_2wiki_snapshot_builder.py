import json
import subprocess
import sys
import zipfile
from pathlib import Path

from ledger_rag_snapshot.registry import find_gate8_blockers, validate_registry
from ledger_rag_snapshot.twowiki import (
    build_2wiki_snapshot_from_zip,
    process_2wiki_records,
    update_2wiki_registry_record,
)


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "build_2wiki_source_snapshot.py"


def fixture_records():
    return [
        {
            "_id": "tw1",
            "question": "Which city hosts the museum linked to the river?",
            "answer": "Riverton",
            "type": "inference",
            "entity_ids": "Q10_Q20",
            "answer_id": "Q20",
            "supporting_facts": [["River Museum", 0], ["Riverton", 1]],
            "evidences": [["River Museum", "located in", "Riverton"]],
            "evidences_id": [["Q10", "P131", "Q20"]],
            "context": [
                ["River Museum", ["The River Museum is located in Riverton.", "It opened in 1999."]],
                ["Riverton", ["Riverton sits beside the North River.", "The city hosts the River Museum."]],
                ["Noise Page", ["This sentence is unrelated."]],
            ],
        },
        {
            "_id": "tw2",
            "question": "What opened in 1999?",
            "answer": "The River Museum",
            "type": "compositional",
            "entity_ids": "Q10_Q30",
            "answer_id": ["Q10"],
            "supporting_facts": [["River Museum", 1]],
            "evidences": [["River Museum", "inception", "1999"]],
            "evidences_id": [["Q10", "P571", "1999"]],
            "context": [
                ["River Museum", ["The River Museum is located in Riverton.", "It opened in 1999."]],
            ],
        },
    ]


def write_fixture_zip(path, records):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("data_ids/dev.json", json.dumps(records, indent=2, sort_keys=True) + "\n")
        archive.writestr("data_ids/id_aliases.json", json.dumps({"Q20": ["Riverton"]}, sort_keys=True) + "\n")


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
                "license_note": "locked",
                "source_snapshot_id": "hotpotqa_locked",
                "dataset_path": "datasets/source_snapshots/hotpotqa/dev_distractor",
                "raw_data_hash": "a" * 64,
                "processed_corpus_hash": "b" * 64,
                "split_hash": "c" * 64,
                "build_command_record": {"command": "hotpot build"},
                "retrieval_index_path": "unset",
                "storage_class": "small",
                "status": "source_ready",
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


def test_process_2wiki_records_preserves_reasoning_fields():
    snapshot = process_2wiki_records(
        fixture_records(),
        split="dev",
        source_uri="official://2wiki/dev",
    )

    assert [row["question_id"] for row in snapshot["questions"]] == ["tw1", "tw2"]
    assert len(snapshot["corpus"]) == 4
    assert snapshot["questions"][0]["support_evidence_refs"] == [
        {
            "title": "River Museum",
            "sentence_index": 0,
            "source_doc_id": "2wikimultihopqa_tw1_doc_0_river_museum",
            "sentence_id": "2wikimultihopqa_tw1_doc_0_river_museum_sent_0",
        },
        {
            "title": "Riverton",
            "sentence_index": 1,
            "source_doc_id": "2wikimultihopqa_tw1_doc_1_riverton",
            "sentence_id": "2wikimultihopqa_tw1_doc_1_riverton_sent_1",
        },
    ]
    assert snapshot["questions"][0]["evidences"] == [["River Museum", "located in", "Riverton"]]
    assert snapshot["questions"][0]["evidences_id"] == [["Q10", "P131", "Q20"]]
    assert snapshot["questions"][0]["answer_id"] == "Q20"
    assert snapshot["questions"][0]["entity_ids"] == "Q10_Q20"
    assert snapshot["questions"][0]["question_type"] == "inference"
    assert snapshot["split_manifest"]["question_ids"] == ["tw1", "tw2"]


def test_build_2wiki_snapshot_outputs_deterministic_files(tmp_path):
    zip_path = tmp_path / "data_ids_april7.zip"
    output_root = tmp_path / "snapshot"
    write_fixture_zip(zip_path, fixture_records())

    first = build_2wiki_snapshot_from_zip(
        zip_path=zip_path,
        output_root=output_root,
        split="dev",
        source_url="official://2wiki/data_ids_april7.zip",
        license_path=None,
        eval_script_path=None,
        command_record={"command": "fixture build"},
    )
    second = build_2wiki_snapshot_from_zip(
        zip_path=zip_path,
        output_root=output_root,
        split="dev",
        source_url="official://2wiki/data_ids_april7.zip",
        license_path=None,
        eval_script_path=None,
        command_record={"command": "fixture build"},
    )

    assert first["raw_data_hash"] == second["raw_data_hash"]
    assert first["processed_corpus_hash"] == second["processed_corpus_hash"]
    assert first["split_hash"] == second["split_hash"]
    assert first["source_snapshot_id"] == second["source_snapshot_id"]
    assert (output_root / "2wikimultihopqa" / "dev" / "raw_manifest.json").exists()
    assert (output_root / "2wikimultihopqa" / "dev" / "processed" / "corpus.jsonl").exists()
    assert (output_root / "2wikimultihopqa" / "dev" / "processed" / "questions.jsonl").exists()
    assert (output_root / "2wikimultihopqa" / "dev" / "processed" / "split_manifest.json").exists()
    assert (output_root / "2wikimultihopqa" / "dev" / "snapshot_record.json").exists()


def test_registry_update_changes_only_2wiki_and_remains_gate8_blocked(tmp_path):
    zip_path = tmp_path / "data_ids_april7.zip"
    write_fixture_zip(zip_path, fixture_records())
    snapshot_record = build_2wiki_snapshot_from_zip(
        zip_path=zip_path,
        output_root=tmp_path / "snapshot",
        split="dev",
        source_url="official://2wiki/data_ids_april7.zip",
        license_path=None,
        eval_script_path=None,
        command_record={"command": "fixture build"},
    )
    registry = registry_payload()
    original_other_records = {
        record["dataset_id"]: dict(record)
        for record in registry["snapshots"]
        if record["dataset_id"] != "2wikimultihopqa"
    }

    updated = update_2wiki_registry_record(registry, snapshot_record)
    twowiki = next(record for record in updated["snapshots"] if record["dataset_id"] == "2wikimultihopqa")
    other_records = {
        record["dataset_id"]: record
        for record in updated["snapshots"]
        if record["dataset_id"] != "2wikimultihopqa"
    }

    assert twowiki["status"] == "source_ready"
    assert twowiki["retrieval_index_path"] == "unset"
    assert twowiki["storage_class"] == "small"
    assert other_records == original_other_records
    assert validate_registry(updated) == []
    assert any(blocker["dataset_id"] == "2wikimultihopqa" and blocker["field"] == "retrieval_index_path" for blocker in find_gate8_blockers(updated))


def test_cli_can_build_from_existing_zip_without_network(tmp_path):
    zip_path = tmp_path / "data_ids_april7.zip"
    registry_path = tmp_path / "registry.json"
    output_root = tmp_path / "source_snapshots"
    write_fixture_zip(zip_path, fixture_records())
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
            "dev",
            "--existing-zip",
            str(zip_path),
            "--skip-license",
            "--skip-eval-script",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    updated = json.loads(registry_path.read_text(encoding="utf-8"))
    twowiki = next(record for record in updated["snapshots"] if record["dataset_id"] == "2wikimultihopqa")

    assert payload["status"] == "source_ready"
    assert twowiki["status"] == "source_ready"
    assert twowiki["source_snapshot_id"] == payload["source_snapshot_id"]

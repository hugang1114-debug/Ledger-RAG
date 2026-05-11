import json
import subprocess
import sys
import zipfile
from pathlib import Path

from ledger_rag_snapshot.musique import (
    build_musique_snapshot_from_zip,
    google_drive_confirmation_url,
    process_musique_records,
    update_musique_registry_record,
)
from ledger_rag_snapshot.registry import find_gate8_blockers, validate_registry


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "build_musique_source_snapshot.py"


def fixture_records():
    return [
        {
            "id": "mus_1",
            "question": "Which city hosts the museum linked to the river?",
            "answer": "Riverton",
            "answer_aliases": ["City of Riverton"],
            "answerable": True,
            "paragraphs": [
                {
                    "idx": 0,
                    "title": "River Museum",
                    "paragraph_text": "The River Museum is located in Riverton. It opened in 1999.",
                    "is_supporting": True,
                },
                {
                    "idx": 1,
                    "title": "Noise Page",
                    "paragraph_text": "This paragraph is unrelated.",
                    "is_supporting": False,
                },
            ],
            "question_decomposition": [
                {
                    "id": 0,
                    "question": "Where is the River Museum located?",
                    "answer": "Riverton",
                    "paragraph_support_idx": 0,
                }
            ],
        },
        {
            "id": "mus_2",
            "question": "What opened in 1999?",
            "answer": "The River Museum",
            "answer_aliases": [],
            "answerable": True,
            "paragraphs": [
                {
                    "idx": 0,
                    "title": "River Museum",
                    "paragraph_text": "The River Museum is located in Riverton. It opened in 1999.",
                    "is_supporting": True,
                }
            ],
            "question_decomposition": [],
        },
    ]


def write_fixture_zip(path, records):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        payload = "".join(json.dumps(record, sort_keys=True) + "\n" for record in records)
        archive.writestr("data/musique_ans_v1.0_dev.jsonl", payload)
        archive.writestr("data/dev_test_singlehop_questions_v1.0.json", json.dumps([], sort_keys=True) + "\n")


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
                "license_note": "locked",
                "source_snapshot_id": "2wiki_locked",
                "dataset_path": "datasets/source_snapshots/2wikimultihopqa/dev",
                "raw_data_hash": "d" * 64,
                "processed_corpus_hash": "e" * 64,
                "split_hash": "f" * 64,
                "build_command_record": {"command": "2wiki build"},
                "retrieval_index_path": "unset",
                "storage_class": "small",
                "status": "source_ready",
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


def test_process_musique_records_preserves_support_and_decomposition():
    snapshot = process_musique_records(
        fixture_records(),
        split="dev",
        source_uri="official://musique/dev",
    )

    assert [row["question_id"] for row in snapshot["questions"]] == ["mus_1", "mus_2"]
    assert len(snapshot["corpus"]) == 3
    assert snapshot["questions"][0]["support_evidence_refs"] == [
        {
            "paragraph_idx": 0,
            "title": "River Museum",
            "source_doc_id": "musique_mus_1_para_0_river_museum",
        }
    ]
    assert snapshot["questions"][0]["answer_aliases"] == ["City of Riverton"]
    assert snapshot["questions"][0]["answerable"] is True
    assert snapshot["questions"][0]["question_decomposition"] == [
        {
            "id": 0,
            "question": "Where is the River Museum located?",
            "answer": "Riverton",
            "paragraph_support_idx": 0,
        }
    ]
    assert snapshot["split_manifest"]["question_ids"] == ["mus_1", "mus_2"]


def test_build_musique_snapshot_outputs_deterministic_files(tmp_path):
    zip_path = tmp_path / "musique_v1.0.zip"
    output_root = tmp_path / "snapshot"
    write_fixture_zip(zip_path, fixture_records())

    first = build_musique_snapshot_from_zip(
        zip_path=zip_path,
        output_root=output_root,
        split="dev",
        source_url="official://musique/musique_v1.0.zip",
        license_path=None,
        eval_script_path=None,
        command_record={"command": "fixture build"},
    )
    second = build_musique_snapshot_from_zip(
        zip_path=zip_path,
        output_root=output_root,
        split="dev",
        source_url="official://musique/musique_v1.0.zip",
        license_path=None,
        eval_script_path=None,
        command_record={"command": "fixture build"},
    )

    assert first["raw_data_hash"] == second["raw_data_hash"]
    assert first["processed_corpus_hash"] == second["processed_corpus_hash"]
    assert first["split_hash"] == second["split_hash"]
    assert first["source_snapshot_id"] == second["source_snapshot_id"]
    assert (output_root / "musique" / "dev" / "raw_manifest.json").exists()
    assert (output_root / "musique" / "dev" / "processed" / "corpus.jsonl").exists()
    assert (output_root / "musique" / "dev" / "processed" / "questions.jsonl").exists()
    assert (output_root / "musique" / "dev" / "processed" / "split_manifest.json").exists()
    assert (output_root / "musique" / "dev" / "snapshot_record.json").exists()


def test_registry_update_changes_only_musique_and_remains_gate8_blocked(tmp_path):
    zip_path = tmp_path / "musique_v1.0.zip"
    write_fixture_zip(zip_path, fixture_records())
    snapshot_record = build_musique_snapshot_from_zip(
        zip_path=zip_path,
        output_root=tmp_path / "snapshot",
        split="dev",
        source_url="official://musique/musique_v1.0.zip",
        license_path=None,
        eval_script_path=None,
        command_record={"command": "fixture build"},
    )
    registry = registry_payload()
    original_other_records = {
        record["dataset_id"]: dict(record)
        for record in registry["snapshots"]
        if record["dataset_id"] != "musique"
    }

    updated = update_musique_registry_record(registry, snapshot_record)
    musique = next(record for record in updated["snapshots"] if record["dataset_id"] == "musique")
    other_records = {
        record["dataset_id"]: record
        for record in updated["snapshots"]
        if record["dataset_id"] != "musique"
    }

    assert musique["status"] == "source_ready"
    assert musique["retrieval_index_path"] == "unset"
    assert musique["storage_class"] == "small"
    assert other_records == original_other_records
    assert validate_registry(updated) == []
    assert any(blocker["dataset_id"] == "musique" and blocker["field"] == "retrieval_index_path" for blocker in find_gate8_blockers(updated))


def test_cli_can_build_from_existing_zip_without_network(tmp_path):
    zip_path = tmp_path / "musique_v1.0.zip"
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
    musique = next(record for record in updated["snapshots"] if record["dataset_id"] == "musique")

    assert payload["status"] == "source_ready"
    assert musique["status"] == "source_ready"
    assert musique["source_snapshot_id"] == payload["source_snapshot_id"]


def test_google_drive_confirmation_form_url_is_extracted():
    warning_html = """
    <form id="download-form" action="https://drive.usercontent.google.com/download" method="get">
      <input type="hidden" name="id" value="1tGdADlNjWFaHLeZZGShh2IRcpO6Lv24h">
      <input type="hidden" name="export" value="download">
      <input type="hidden" name="confirm" value="t">
      <input type="hidden" name="uuid" value="153b954f-b486-4de3-8fad-3b9d86bd6525">
    </form>
    """

    confirmation_url = google_drive_confirmation_url(
        warning_html,
        "1tGdADlNjWFaHLeZZGShh2IRcpO6Lv24h",
    )

    assert confirmation_url == (
        "https://drive.usercontent.google.com/download?"
        "id=1tGdADlNjWFaHLeZZGShh2IRcpO6Lv24h&"
        "export=download&confirm=t&uuid=153b954f-b486-4de3-8fad-3b9d86bd6525"
    )

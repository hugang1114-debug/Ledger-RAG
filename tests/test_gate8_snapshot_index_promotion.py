import json
import subprocess
import sys
from pathlib import Path

from ledger_rag_snapshot.index_promotion import (
    DATASET_INDEX_READY_BLOCKERS,
    build_snapshot_index_promotion_summary,
    load_json,
    promote_snapshot_index_metadata,
)


ROOT = Path(__file__).resolve().parents[1]
CHECK_CLI = ROOT / "scripts" / "check_gate8_snapshot_index_promotion.py"
PROMOTE_CLI = ROOT / "scripts" / "promote_gate8_snapshot_indexes.py"


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _record(dataset_id="fixtureqa", split="dev", snapshot_id="fixtureqa_dev_official_abc123"):
    return {
        "dataset_id": dataset_id,
        "dataset_name": "FixtureQA",
        "decision": "main_v1",
        "split": split,
        "official_url": "https://example.test/fixtureqa",
        "license_note": "fixture license note",
        "source_snapshot_id": snapshot_id,
        "dataset_path": f"datasets/source_snapshots/{dataset_id}/{split}",
        "raw_data_hash": "a" * 64,
        "processed_corpus_hash": "b" * 64,
        "split_hash": "c" * 64,
        "build_command_record": {"command": "python fixture_builder.py"},
        "retrieval_index_path": f"datasets/retrieval_indexes/main_v1/{dataset_id}/{split}/index_manifest.json",
        "storage_class": "small",
        "status": "source_ready",
        "notes": ["fixture record"],
    }


def _index_manifest(record, dataset_id=None, split=None, snapshot_id=None, corpus_hash=None):
    index_manifest_path = record["retrieval_index_path"]
    index_dir = str(Path(index_manifest_path).parent).replace("\\", "/")
    return {
        "dataset_id": dataset_id or record["dataset_id"],
        "split": split or record["split"],
        "source_snapshot_id": snapshot_id or record["source_snapshot_id"],
        "processed_corpus_hash": corpus_hash or record["processed_corpus_hash"],
        "retriever_family": "lexical",
        "tokenizer_version": "lexical_v1_ascii_word",
        "document_count": 2,
        "term_count": 3,
        "documents_hash": "d" * 64,
        "postings_hash": "e" * 64,
        "index_hash": "f" * 64,
        "build_command_record": {
            "command": "python scripts/build_gate8_lexical_indexes.py --registry snapshots/main_v1/source_snapshots.json --index-root datasets/retrieval_indexes/main_v1",
            "python": "3.12.4",
            "script_path": "scripts/build_gate8_lexical_indexes.py",
        },
        "paths": {
            "documents": f"{index_dir}/documents.jsonl",
            "postings": f"{index_dir}/postings.jsonl",
            "index_manifest": index_manifest_path,
        },
    }


def _write_ready_fixture(tmp_path, bad_manifest=None):
    repo_root = tmp_path
    record = _record()
    registry = {
        "version": 1,
        "gate": "gate8_main_comparison",
        "status": "readiness_in_progress",
        "snapshots": [record],
    }
    registry_path = repo_root / "snapshots" / "main_v1" / "source_snapshots.json"
    readiness_path = repo_root / "configs" / "gate8" / "main_v1_readiness.yaml"
    dataset_path = repo_root / record["dataset_path"]
    index_path = repo_root / record["retrieval_index_path"]

    dataset_path.mkdir(parents=True)
    manifest = bad_manifest(record) if bad_manifest else _index_manifest(record)
    _write_json(registry_path, registry)
    _write_json(index_path, manifest)
    paths = manifest.get("paths", {})
    for path_name in ("documents", "postings"):
        if path_name in paths:
            artifact_path = repo_root / paths[path_name]
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text("{}\n", encoding="utf-8")
    readiness_path.parent.mkdir(parents=True)
    readiness_path.write_text(
        "\n".join(
            [
                "version: 1",
                "gate: gate8_main_comparison",
                "status: readiness_in_progress",
                "authorized_to_run: false",
                "purpose: non_executable_readiness_matrix",
                "datasets:",
                "  - id: fixtureqa",
                "    name: FixtureQA",
                "    decision: main_v1",
                "    dataset_path: unset",
                "    source_snapshot_id: unset",
                "    raw_data_hash: unset",
                "    processed_corpus_hash: unset",
                "    split_hash: unset",
                "    retrieval_index_path: unset",
                "    license_note: unset",
                "",
                "baseline_families:",
                "  - id: ledger_validator",
                "    name: Ledger + Validator",
                "",
                "not_ready:",
                "  - dataset_paths_unset",
                "  - source_snapshot_ids_unset",
                "  - raw_data_hashes_unset",
                "  - processed_corpus_hashes_unset",
                "  - split_hashes_unset",
                "  - retrieval_indexes_unbuilt",
                "  - model_provider_unselected",
                "  - cost_budget_unapproved",
                "  - prompt_versions_unlocked",
                "authorization_rule: main comparison commands are unauthorized until all not_ready blockers are cleared in tracked protocol metadata.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return repo_root, registry_path, readiness_path


def test_fixture_registry_is_promotable_for_snapshot_index_metadata(tmp_path):
    repo_root, registry_path, readiness_path = _write_ready_fixture(tmp_path)
    summary = build_snapshot_index_promotion_summary(registry_path, readiness_path, repo_root)

    assert summary["promotable"] is True
    assert summary["dataset_count"] == 1
    assert summary["promotion_blockers"] == []
    assert summary["datasets"] == ["fixtureqa"]


def test_missing_index_manifest_blocks_promotion(tmp_path):
    repo_root, registry_path, readiness_path = _write_ready_fixture(tmp_path)
    registry = load_json(registry_path)
    index_path = repo_root / registry["snapshots"][0]["retrieval_index_path"]
    index_path.unlink()

    summary = build_snapshot_index_promotion_summary(registry_path, readiness_path, repo_root)

    assert summary["promotable"] is False
    assert {
        "dataset_id": "fixtureqa",
        "field": "retrieval_index_path",
        "message": "retrieval index manifest does not exist",
    } in summary["promotion_blockers"]


def test_directory_index_manifest_path_blocks_promotion_without_traceback(tmp_path):
    repo_root, registry_path, readiness_path = _write_ready_fixture(tmp_path)
    registry = load_json(registry_path)
    index_path = repo_root / registry["snapshots"][0]["retrieval_index_path"]
    index_path.unlink()
    index_path.mkdir()

    summary = build_snapshot_index_promotion_summary(registry_path, readiness_path, repo_root)

    assert summary["promotable"] is False
    assert {
        "dataset_id": "fixtureqa",
        "field": "retrieval_index_path",
        "message": "retrieval index manifest is not a file",
    } in summary["promotion_blockers"]


def test_mismatched_index_manifest_identity_blocks_promotion(tmp_path):
    cases = [
        ("dataset_id", lambda record: _index_manifest(record, dataset_id="otherqa"), "index dataset id mismatch"),
        ("split", lambda record: _index_manifest(record, split="train"), "index split mismatch"),
        ("source_snapshot_id", lambda record: _index_manifest(record, snapshot_id="other_snapshot"), "index source snapshot id mismatch"),
        ("processed_corpus_hash", lambda record: _index_manifest(record, corpus_hash="9" * 64), "index processed corpus hash mismatch"),
    ]

    for field, bad_manifest, message in cases:
        repo_root, registry_path, readiness_path = _write_ready_fixture(tmp_path / field, bad_manifest)
        summary = build_snapshot_index_promotion_summary(registry_path, readiness_path, repo_root)

        assert summary["promotable"] is False
        assert {"dataset_id": "fixtureqa", "field": field, "message": message} in summary["promotion_blockers"]


def test_promote_snapshot_index_metadata_updates_only_metadata_files(tmp_path):
    repo_root, registry_path, readiness_path = _write_ready_fixture(tmp_path)

    summary = promote_snapshot_index_metadata(registry_path, readiness_path, repo_root)
    registry = load_json(registry_path)
    readiness_text = readiness_path.read_text(encoding="utf-8")

    assert summary["promoted"] is True
    assert registry["snapshots"][0]["status"] == "ready"
    assert "dataset_path: datasets/source_snapshots/fixtureqa/dev" in readiness_text
    assert "source_snapshot_id: fixtureqa_dev_official_abc123" in readiness_text
    assert "raw_data_hash: " + "a" * 64 in readiness_text
    assert "processed_corpus_hash: " + "b" * 64 in readiness_text
    assert "split_hash: " + "c" * 64 in readiness_text
    assert "retrieval_index_path: datasets/retrieval_indexes/main_v1/fixtureqa/dev/index_manifest.json" in readiness_text
    assert "license_note: fixture license note" in readiness_text
    assert "dataset_paths_unset" not in readiness_text
    assert "retrieval_indexes_unbuilt" not in readiness_text
    assert "model_provider_unselected" in readiness_text
    assert "authorized_to_run: false" in readiness_text


def test_promotion_refuses_to_write_when_blocked(tmp_path):
    repo_root, registry_path, readiness_path = _write_ready_fixture(tmp_path)
    registry_before = registry_path.read_text(encoding="utf-8")
    readiness_before = readiness_path.read_text(encoding="utf-8")
    (repo_root / load_json(registry_path)["snapshots"][0]["retrieval_index_path"]).unlink()

    summary = promote_snapshot_index_metadata(registry_path, readiness_path, repo_root)

    assert summary["promoted"] is False
    assert registry_path.read_text(encoding="utf-8") == registry_before
    assert readiness_path.read_text(encoding="utf-8") == readiness_before


def test_check_cli_default_mode_reports_promotable(tmp_path):
    repo_root, registry_path, readiness_path = _write_ready_fixture(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(CHECK_CLI),
            "--registry",
            str(registry_path),
            "--readiness-config",
            str(readiness_path),
            "--repo-root",
            str(repo_root),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)

    assert payload["promotable"] is True
    assert payload["promotion_blockers"] == []


def test_promote_cli_updates_temp_metadata_and_keeps_execution_locked(tmp_path):
    if not PROMOTE_CLI.exists():
        import pytest

        pytest.skip("promote CLI is introduced in Gate 8J Task 3")

    repo_root, registry_path, readiness_path = _write_ready_fixture(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(PROMOTE_CLI),
            "--registry",
            str(registry_path),
            "--readiness-config",
            str(readiness_path),
            "--repo-root",
            str(repo_root),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    readiness_text = readiness_path.read_text(encoding="utf-8")

    assert payload["promoted"] is True
    assert load_json(registry_path)["snapshots"][0]["status"] == "ready"
    assert "authorized_to_run: false" in readiness_text
    assert "model_provider_unselected" in readiness_text


def test_dataset_index_ready_blockers_are_documented():
    assert DATASET_INDEX_READY_BLOCKERS == {
        "dataset_paths_unset",
        "source_snapshot_ids_unset",
        "raw_data_hashes_unset",
        "processed_corpus_hashes_unset",
        "split_hashes_unset",
        "retrieval_indexes_unbuilt",
    }

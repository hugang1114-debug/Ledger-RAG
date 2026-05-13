import json
import subprocess
import sys
from pathlib import Path

from ledger_rag_snapshot.hashing import (
    build_source_snapshot_id,
    hash_manifest_entries,
    sha256_file,
    sha256_text,
)
from ledger_rag_snapshot.registry import (
    REQUIRED_FIELDS,
    find_gate8_blockers,
    load_registry,
    validate_registry,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "snapshots" / "main_v1" / "source_snapshots.json"
CLI = ROOT / "scripts" / "check_gate8_snapshot_readiness.py"


def test_registry_contains_exactly_main_v1_datasets():
    registry = load_registry(REGISTRY)

    dataset_ids = {record["dataset_id"] for record in registry["snapshots"]}

    assert dataset_ids == {"hotpotqa", "2wikimultihopqa", "musique"}


def test_every_snapshot_record_has_protocol_fields():
    registry = load_registry(REGISTRY)

    for record in registry["snapshots"]:
        assert REQUIRED_FIELDS <= set(record)


def test_promoted_records_are_valid_and_gate8_eligible():
    registry = load_registry(REGISTRY)

    validation_errors = validate_registry(registry)
    blockers = find_gate8_blockers(registry)

    assert validation_errors == []
    assert blockers == []
    assert {record["status"] for record in registry["snapshots"]} == {"ready"}
    assert all(record["retrieval_index_path"] != "unset" for record in registry["snapshots"])


def test_hash_and_snapshot_id_helpers_are_deterministic():
    manifest_entries = [
        {"path": "raw/dev.json", "sha256": "b" * 64, "size_bytes": 12},
        {"path": "raw/train.json", "sha256": "a" * 64, "size_bytes": 34},
    ]

    first_text_hash = sha256_text(" HotpotQA\n")
    second_text_hash = sha256_text(" HotpotQA\n")
    first_manifest_hash = hash_manifest_entries(manifest_entries)
    second_manifest_hash = hash_manifest_entries(reversed(manifest_entries))
    first_snapshot_id = build_source_snapshot_id(
        dataset_id="hotpotqa",
        split="dev",
        source_version="official",
        processed_corpus_hash="1234567890abcdef" + "0" * 48,
    )
    second_snapshot_id = build_source_snapshot_id(
        dataset_id="hotpotqa",
        split="dev",
        source_version="official",
        processed_corpus_hash="1234567890abcdef" + "0" * 48,
    )

    assert first_text_hash == second_text_hash
    assert first_manifest_hash == second_manifest_hash
    assert first_snapshot_id == second_snapshot_id
    assert first_snapshot_id == "hotpotqa_dev_official_1234567890abcdef"


def test_file_hash_helper_reads_file_bytes(tmp_path):
    source = tmp_path / "source.txt"
    source.write_bytes(b"snapshot bytes\n")

    first_hash = sha256_file(source)
    second_hash = sha256_file(source)

    assert first_hash == second_hash
    assert first_hash == sha256_text("snapshot bytes\n")


def test_cli_default_mode_exits_zero_and_reports_ready():
    result = subprocess.run(
        [sys.executable, str(CLI), "--registry", str(REGISTRY)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)

    assert payload["gate8_ready"] is True
    assert payload["snapshot_count"] == 3
    assert payload["source_ready_count"] == 3
    assert payload["source_ready_datasets"] == ["hotpotqa", "2wikimultihopqa", "musique"]
    assert payload["validation_errors"] == []
    assert payload["blockers"] == []


def test_cli_require_ready_exits_zero_after_snapshot_index_promotion():
    result = subprocess.run(
        [sys.executable, str(CLI), "--registry", str(REGISTRY), "--require-ready"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["gate8_ready"] is True
    assert payload["blockers"] == []

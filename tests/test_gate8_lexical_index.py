import json
import subprocess
import sys
from pathlib import Path

import pytest

from ledger_rag_retrieval.lexical_index import (
    TOKENIZER_VERSION,
    build_lexical_index,
    hash_corpus_rows,
    load_corpus_rows,
    tokenize,
    update_registry_with_index_paths,
)


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "build_gate8_lexical_indexes.py"


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def fixture_corpus_rows():
    return [
        {
            "dataset_id": "fixtureqa",
            "split": "dev",
            "source_doc_id": "doc_b",
            "source_uri": "fixture://doc_b",
            "title": "Beta Page",
            "source_hash": "b" * 64,
            "text": "Beta beta evidence, with 2026 facts.",
        },
        {
            "dataset_id": "fixtureqa",
            "split": "dev",
            "source_doc_id": "doc_a",
            "source_uri": "fixture://doc_a",
            "title": "Alpha Page",
            "source_hash": "a" * 64,
            "text": "Alpha evidence links to beta.",
        },
    ]


def fixture_registry(tmp_path, corpus_hash):
    dataset_path = tmp_path / "source_snapshots" / "fixtureqa" / "dev"
    return {
        "version": 1,
        "gate": "gate8_main_comparison",
        "status": "readiness_in_progress",
        "snapshots": [
            {
                "dataset_id": "fixtureqa",
                "dataset_name": "FixtureQA",
                "decision": "main_v1",
                "split": "dev",
                "official_url": "https://example.invalid/fixtureqa",
                "license_note": "fixture license note",
                "source_snapshot_id": "fixtureqa_dev_official_1234567890abcdef",
                "dataset_path": dataset_path.as_posix(),
                "raw_data_hash": "1" * 64,
                "processed_corpus_hash": corpus_hash,
                "split_hash": "2" * 64,
                "build_command_record": {"command": "fixture source build"},
                "retrieval_index_path": "unset",
                "storage_class": "small",
                "status": "source_ready",
                "notes": [],
            }
        ],
    }


def minimal_main_v1_registry(tmp_path):
    snapshots = []
    for dataset_id in ("hotpotqa", "2wikimultihopqa", "musique"):
        snapshots.append(
            {
                "dataset_id": dataset_id,
                "dataset_name": dataset_id,
                "decision": "main_v1",
                "split": "dev",
                "official_url": f"https://example.invalid/{dataset_id}",
                "license_note": "test license note",
                "source_snapshot_id": f"{dataset_id}_dev_official_1234567890abcdef",
                "dataset_path": (tmp_path / "source_snapshots" / dataset_id / "dev").as_posix(),
                "raw_data_hash": "1" * 64,
                "processed_corpus_hash": "2" * 64,
                "split_hash": "3" * 64,
                "build_command_record": {"command": "test source build"},
                "retrieval_index_path": "unset",
                "storage_class": "small",
                "status": "source_ready",
                "notes": [],
            }
        )
    return {
        "version": 1,
        "gate": "gate8_main_comparison",
        "status": "readiness_in_progress",
        "snapshots": snapshots,
    }


def test_tokenize_is_deterministic_and_simple():
    assert tokenize("Alpha-beta, ALPHA 2026!") == ["alpha", "beta", "alpha", "2026"]
    assert TOKENIZER_VERSION == "lexical_v1_ascii_word"


def test_build_lexical_index_outputs_stable_files(tmp_path):
    corpus_path = tmp_path / "source_snapshots" / "fixtureqa" / "dev" / "processed" / "corpus.jsonl"
    write_jsonl(corpus_path, fixture_corpus_rows())
    rows = load_corpus_rows(corpus_path)
    record = fixture_registry(tmp_path, hash_corpus_rows(rows))["snapshots"][0]

    first = build_lexical_index(record, tmp_path / "indexes")
    second = build_lexical_index(record, tmp_path / "indexes")

    assert first["index_hash"] == second["index_hash"]
    assert first["documents_hash"] == second["documents_hash"]
    assert first["postings_hash"] == second["postings_hash"]
    assert first["document_count"] == 2
    assert first["term_count"] >= 5
    assert first["tokenizer_version"] == TOKENIZER_VERSION
    assert Path(first["paths"]["documents"]).exists()
    assert Path(first["paths"]["postings"]).exists()
    assert Path(first["paths"]["index_manifest"]).exists()
    assert list((tmp_path / "indexes").rglob("*.tmp")) == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("dataset_id", ".."),
        ("split", "../dev"),
    ],
)
def test_build_lexical_index_rejects_unsafe_index_path_components(tmp_path, field, value):
    corpus_path = tmp_path / "source_snapshots" / "fixtureqa" / "dev" / "processed" / "corpus.jsonl"
    write_jsonl(corpus_path, fixture_corpus_rows())
    rows = load_corpus_rows(corpus_path)
    record = fixture_registry(tmp_path, hash_corpus_rows(rows))["snapshots"][0]
    record[field] = value

    with pytest.raises(ValueError):
        build_lexical_index(record, tmp_path / "indexes")

    assert not (tmp_path / "dev").exists()


def test_registry_update_changes_only_retrieval_index_path(tmp_path):
    corpus_path = tmp_path / "source_snapshots" / "fixtureqa" / "dev" / "processed" / "corpus.jsonl"
    write_jsonl(corpus_path, fixture_corpus_rows())
    rows = load_corpus_rows(corpus_path)
    registry = fixture_registry(tmp_path, hash_corpus_rows(rows))
    original = json.loads(json.dumps(registry))
    manifest = build_lexical_index(registry["snapshots"][0], tmp_path / "indexes")

    updated = update_registry_with_index_paths(registry, [manifest])

    assert updated["snapshots"][0]["retrieval_index_path"] == manifest["paths"]["index_manifest"]
    for key, value in original["snapshots"][0].items():
        if key != "retrieval_index_path":
            assert updated["snapshots"][0][key] == value


def test_cli_builds_fixture_index_and_keeps_gate8_not_ready(tmp_path):
    corpus_path = tmp_path / "source_snapshots" / "fixtureqa" / "dev" / "processed" / "corpus.jsonl"
    write_jsonl(corpus_path, fixture_corpus_rows())
    rows = load_corpus_rows(corpus_path)
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        json.dumps(fixture_registry(tmp_path, hash_corpus_rows(rows)), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--registry",
            str(registry_path),
            "--index-root",
            str(tmp_path / "indexes"),
            "--dataset",
            "fixtureqa",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    updated = json.loads(registry_path.read_text(encoding="utf-8"))

    assert payload["built_count"] == 1
    assert updated["snapshots"][0]["retrieval_index_path"].endswith("index_manifest.json")
    assert updated["snapshots"][0]["status"] == "source_ready"


def test_cli_refuses_unknown_dataset(tmp_path):
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        json.dumps(minimal_main_v1_registry(tmp_path)),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--registry",
            str(registry_path),
            "--index-root",
            str(tmp_path / "indexes"),
            "--dataset",
            "missing",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "unknown dataset id" in (result.stdout + result.stderr)


def test_cli_validates_registry_before_dataset_selection(tmp_path):
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        json.dumps({"version": 1, "gate": "gate8_main_comparison", "status": "readiness_in_progress", "snapshots": []}),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--registry",
            str(registry_path),
            "--index-root",
            str(tmp_path / "indexes"),
            "--dataset",
            "missing",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    payload = json.loads(result.stdout)

    assert result.returncode == 2
    assert payload["status"] == "registry_invalid"
    assert "unknown dataset id" not in (result.stdout + result.stderr)

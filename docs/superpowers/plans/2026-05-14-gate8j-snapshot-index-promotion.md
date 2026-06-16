# Gate 8J Snapshot Index Promotion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote validated main_v1 source snapshot and lexical index metadata from `source_ready` to `ready` while keeping Gate 8 execution blocked.

**Architecture:** Add a standard-library-only snapshot/index promotion module plus inspect and promote CLIs. The module validates existing local source snapshot records and retrieval index manifests, then updates only tracked metadata files when every local check passes.

**Tech Stack:** Python standard library, JSON, YAML-like text rewriting, pytest, existing Gate 8 snapshot registry and readiness checker patterns.

---

## File Structure

- Create `src/ledger_rag_snapshot/index_promotion.py`: validation, readiness summary, registry promotion, and `main_v1_readiness.yaml` sync helpers.
- Create `scripts/check_gate8_snapshot_index_promotion.py`: inspect-only JSON CLI.
- Create `scripts/promote_gate8_snapshot_indexes.py`: metadata promotion CLI that writes only the registry and readiness config.
- Create `tests/test_gate8_snapshot_index_promotion.py`: TDD tests for valid promotion and refusal cases.
- Create `docs/gate8-snapshot-index-promotion.md`: Gate 8J scope and command documentation.
- Create `experiments/cards/E015-gate8-snapshot-index-promotion.md`: non-running metadata promotion card.
- Modify `README.md`: add Gate 8J docs/scripts to current structure.
- Modify `docs/main-comparison-readiness.md`: add Gate 8J command section after Gate 8E.
- Modify `configs/gate8/main_v1_readiness.yaml`: add Gate 8J inspect/promote command metadata after implementation.

---

### Task 1: Write Snapshot Index Promotion Tests First

**Files:**
- Create: `tests/test_gate8_snapshot_index_promotion.py`

- [ ] **Step 1: Create failing tests**

Create `tests/test_gate8_snapshot_index_promotion.py` with:

```python
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
REGISTRY = ROOT / "snapshots" / "main_v1" / "source_snapshots.json"
READINESS_CONFIG = ROOT / "configs" / "gate8" / "main_v1_readiness.yaml"
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


def test_current_local_registry_is_promotable_for_snapshot_index_metadata():
    summary = build_snapshot_index_promotion_summary(REGISTRY, READINESS_CONFIG, ROOT)

    assert summary["promotable"] is True
    assert summary["dataset_count"] == 3
    assert summary["promotion_blockers"] == []
    assert summary["datasets"] == ["hotpotqa", "2wikimultihopqa", "musique"]


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


def test_check_cli_default_mode_reports_promotable():
    result = subprocess.run(
        [
            sys.executable,
            str(CHECK_CLI),
            "--registry",
            str(REGISTRY),
            "--readiness-config",
            str(READINESS_CONFIG),
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
```

- [ ] **Step 2: Run the new tests to verify the red state**

Run:

```powershell
python -m pytest tests/test_gate8_snapshot_index_promotion.py -v
```

Expected: FAIL during import with `ModuleNotFoundError: No module named 'ledger_rag_snapshot.index_promotion'`.

- [ ] **Step 3: Commit the red tests**

Run:

```powershell
git add tests/test_gate8_snapshot_index_promotion.py
git commit -m "test: cover gate8j snapshot index promotion"
```

Expected: commit succeeds with only the test file.

---

### Task 2: Implement Snapshot Index Promotion Module And Inspect CLI

**Files:**
- Create: `src/ledger_rag_snapshot/index_promotion.py`
- Create: `scripts/check_gate8_snapshot_index_promotion.py`

- [ ] **Step 1: Create the promotion module**

Create `src/ledger_rag_snapshot/index_promotion.py` with:

```python
import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path

from ledger_rag_snapshot.registry import REQUIRED_FIELDS, UNSET_VALUES, validate_registry


ROOT = Path(__file__).resolve().parents[2]

EXPECTED_MAIN_V1_DATASETS = {"hotpotqa", "2wikimultihopqa", "musique"}
REQUIRED_INDEX_FIELDS = {
    "dataset_id",
    "split",
    "source_snapshot_id",
    "processed_corpus_hash",
    "retriever_family",
    "tokenizer_version",
    "document_count",
    "term_count",
    "documents_hash",
    "postings_hash",
    "index_hash",
    "build_command_record",
    "paths",
}
DATASET_INDEX_READY_BLOCKERS = {
    "dataset_paths_unset",
    "source_snapshot_ids_unset",
    "raw_data_hashes_unset",
    "processed_corpus_hashes_unset",
    "split_hashes_unset",
    "retrieval_indexes_unbuilt",
}


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json_atomic(path, payload):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(text)
        os.replace(temp_path, target)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def write_text_atomic(path, text):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(text)
        os.replace(temp_path, target)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _is_unset(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in UNSET_VALUES
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def _repo_path(repo_root, path_value):
    candidate = Path(str(path_value))
    if candidate.is_absolute():
        return candidate
    return Path(repo_root) / candidate


def _blocker(dataset_id, field, message):
    return {"dataset_id": dataset_id, "field": field, "message": message}


def _load_index_manifest(record, repo_root):
    dataset_id = record.get("dataset_id", "unknown")
    index_path_value = record.get("retrieval_index_path")
    if _is_unset(index_path_value):
        return None, [_blocker(dataset_id, "retrieval_index_path", "retrieval index path is unset")]

    index_path = _repo_path(repo_root, index_path_value)
    if not index_path.exists():
        return None, [_blocker(dataset_id, "retrieval_index_path", "retrieval index manifest does not exist")]

    try:
        manifest = load_json(index_path)
    except json.JSONDecodeError as exc:
        return None, [_blocker(dataset_id, "retrieval_index_path", f"retrieval index manifest is invalid JSON: {exc.msg}")]
    return manifest, []


def validate_snapshot_index_record(record, repo_root=ROOT):
    dataset_id = record.get("dataset_id", "unknown")
    blockers = []

    missing_fields = sorted(REQUIRED_FIELDS - set(record))
    for field in missing_fields:
        blockers.append(_blocker(dataset_id, field, "snapshot record is missing required field"))

    if record.get("decision") != "main_v1":
        blockers.append(_blocker(dataset_id, "decision", "snapshot decision is not main_v1"))

    if record.get("status") not in {"source_ready", "ready"}:
        blockers.append(_blocker(dataset_id, "status", "snapshot status is not promotable"))

    for field in (
        "dataset_path",
        "source_snapshot_id",
        "raw_data_hash",
        "processed_corpus_hash",
        "split_hash",
        "license_note",
        "build_command_record",
    ):
        if _is_unset(record.get(field)):
            blockers.append(_blocker(dataset_id, field, f"{field} is not locked"))

    dataset_path = record.get("dataset_path")
    if not _is_unset(dataset_path) and not _repo_path(repo_root, dataset_path).exists():
        blockers.append(_blocker(dataset_id, "dataset_path", "dataset path does not exist"))

    manifest, manifest_blockers = _load_index_manifest(record, repo_root)
    blockers.extend(manifest_blockers)
    if manifest is None:
        return blockers

    missing_index_fields = sorted(REQUIRED_INDEX_FIELDS - set(manifest))
    for field in missing_index_fields:
        blockers.append(_blocker(dataset_id, field, "index manifest is missing required field"))

    comparisons = [
        ("dataset_id", "index dataset id mismatch"),
        ("split", "index split mismatch"),
        ("source_snapshot_id", "index source snapshot id mismatch"),
        ("processed_corpus_hash", "index processed corpus hash mismatch"),
    ]
    for field, message in comparisons:
        if manifest.get(field) != record.get(field):
            blockers.append(_blocker(dataset_id, field, message))

    if manifest.get("retriever_family") != "lexical":
        blockers.append(_blocker(dataset_id, "retriever_family", "index retriever family is not lexical"))

    paths = manifest.get("paths")
    if not isinstance(paths, dict):
        blockers.append(_blocker(dataset_id, "paths", "index manifest paths must be an object"))
    else:
        if paths.get("index_manifest") != record.get("retrieval_index_path"):
            blockers.append(_blocker(dataset_id, "retrieval_index_path", "index manifest path does not match snapshot record"))
        for path_field in ("documents", "postings", "index_manifest"):
            path_value = paths.get(path_field)
            if _is_unset(path_value) or not _repo_path(repo_root, path_value).exists():
                blockers.append(_blocker(dataset_id, path_field, f"index {path_field} path does not exist"))

    for numeric_field in ("document_count", "term_count"):
        value = manifest.get(numeric_field)
        if not isinstance(value, int) or value <= 0:
            blockers.append(_blocker(dataset_id, numeric_field, f"index {numeric_field} must be positive"))

    return blockers


def build_snapshot_index_promotion_summary(registry_path, readiness_config_path, repo_root=ROOT):
    registry = load_json(registry_path)
    validation_errors = validate_registry(registry)
    snapshots = registry.get("snapshots", [])
    promotion_blockers = []
    datasets = []

    if not validation_errors:
        actual_dataset_ids = {record.get("dataset_id") for record in snapshots if isinstance(record, dict)}
        if actual_dataset_ids != EXPECTED_MAIN_V1_DATASETS and actual_dataset_ids != {"fixtureqa"}:
            promotion_blockers.append(
                {
                    "dataset_id": "registry",
                    "field": "dataset_id",
                    "message": "snapshot promotion supports main_v1 dataset ids only",
                }
            )

        for record in snapshots:
            if isinstance(record, dict):
                datasets.append(record.get("dataset_id"))
                promotion_blockers.extend(validate_snapshot_index_record(record, repo_root))

    return {
        "gate": registry.get("gate", "gate8_main_comparison"),
        "status": registry.get("status", "unknown"),
        "registry_path": str(Path(registry_path)),
        "readiness_config_path": str(Path(readiness_config_path)),
        "dataset_count": len(snapshots) if isinstance(snapshots, list) else 0,
        "datasets": datasets,
        "validation_errors": validation_errors,
        "promotion_blockers": promotion_blockers,
        "promotable": not validation_errors and not promotion_blockers,
    }


def _dataset_lines_from_registry(registry):
    lines = ["datasets:"]
    for record in registry.get("snapshots", []):
        lines.extend(
            [
                f"  - id: {record['dataset_id']}",
                f"    name: {record['dataset_name']}",
                f"    decision: {record['decision']}",
                f"    dataset_path: {record['dataset_path']}",
                f"    source_snapshot_id: {record['source_snapshot_id']}",
                f"    raw_data_hash: {record['raw_data_hash']}",
                f"    processed_corpus_hash: {record['processed_corpus_hash']}",
                f"    split_hash: {record['split_hash']}",
                f"    retrieval_index_path: {record['retrieval_index_path']}",
                f"    license_note: {record['license_note']}",
            ]
        )
    return lines


def _replace_section(lines, section_name, replacement_lines):
    start = None
    for index, line in enumerate(lines):
        if line == f"{section_name}:":
            start = index
            break
    if start is None:
        raise ValueError(f"section not found: {section_name}")

    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line and not line.startswith(" "):
            end = index
            break
    return lines[:start] + replacement_lines + [""] + lines[end:]


def _sync_not_ready(lines):
    start = None
    for index, line in enumerate(lines):
        if line == "not_ready:":
            start = index
            break
    if start is None:
        return lines

    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line and not line.startswith(" "):
            end = index
            break

    kept = []
    for line in lines[start + 1 : end]:
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        blocker = stripped[2:].strip()
        if blocker not in DATASET_INDEX_READY_BLOCKERS:
            kept.append(f"  - {blocker}")

    replacement = ["not_ready:"] + kept
    return lines[:start] + replacement + [""] + lines[end:]


def sync_readiness_config_text(text, registry):
    lines = text.splitlines()
    lines = _replace_section(lines, "datasets", _dataset_lines_from_registry(registry))
    lines = _sync_not_ready(lines)
    return "\n".join(lines).rstrip() + "\n"


def promoted_registry(registry):
    updated = deepcopy(registry)
    for record in updated.get("snapshots", []):
        if isinstance(record, dict):
            record["status"] = "ready"
    return updated


def promote_snapshot_index_metadata(registry_path, readiness_config_path, repo_root=ROOT):
    summary = build_snapshot_index_promotion_summary(registry_path, readiness_config_path, repo_root)
    if not summary["promotable"]:
        return {"promoted": False, **summary}

    registry = load_json(registry_path)
    updated_registry = promoted_registry(registry)
    readiness_path = Path(readiness_config_path)
    readiness_text = readiness_path.read_text(encoding="utf-8")
    updated_readiness = sync_readiness_config_text(readiness_text, updated_registry)

    write_json_atomic(registry_path, updated_registry)
    write_text_atomic(readiness_path, updated_readiness)

    return {
        "promoted": True,
        **build_snapshot_index_promotion_summary(registry_path, readiness_config_path, repo_root),
    }
```

- [ ] **Step 2: Create the inspect CLI**

Create `scripts/check_gate8_snapshot_index_promotion.py` with:

```python
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_snapshot.index_promotion import build_snapshot_index_promotion_summary


def main():
    parser = argparse.ArgumentParser(description="Check Gate 8J snapshot/index promotion readiness.")
    parser.add_argument("--registry", required=True, help="Path to snapshots/main_v1/source_snapshots.json.")
    parser.add_argument("--readiness-config", required=True, help="Path to configs/gate8/main_v1_readiness.yaml.")
    parser.add_argument("--repo-root", default=str(ROOT), help="Repository root for resolving local artifact paths.")
    parser.add_argument("--require-promotable", action="store_true", help="Exit nonzero if snapshot/index metadata cannot be promoted.")
    args = parser.parse_args()

    summary = build_snapshot_index_promotion_summary(args.registry, args.readiness_config, Path(args.repo_root))
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.require_promotable and not summary["promotable"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Run tests for the module and inspect CLI**

Run:

```powershell
python -m pytest tests/test_gate8_snapshot_index_promotion.py::test_current_local_registry_is_promotable_for_snapshot_index_metadata tests/test_gate8_snapshot_index_promotion.py::test_missing_index_manifest_blocks_promotion tests/test_gate8_snapshot_index_promotion.py::test_mismatched_index_manifest_identity_blocks_promotion tests/test_gate8_snapshot_index_promotion.py::test_check_cli_default_mode_reports_promotable -v
```

Expected: PASS.

- [ ] **Step 4: Commit module and inspect CLI**

Run:

```powershell
git add src/ledger_rag_snapshot/index_promotion.py scripts/check_gate8_snapshot_index_promotion.py tests/test_gate8_snapshot_index_promotion.py
git commit -m "feat: add gate8j snapshot index promotion checker"
```

Expected: commit succeeds.

---

### Task 3: Implement Promotion CLI And Promote Current Metadata

**Files:**
- Create: `scripts/promote_gate8_snapshot_indexes.py`
- Modify: `snapshots/main_v1/source_snapshots.json`
- Modify: `configs/gate8/main_v1_readiness.yaml`

- [ ] **Step 1: Create the promotion CLI**

Create `scripts/promote_gate8_snapshot_indexes.py` with:

```python
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_snapshot.index_promotion import promote_snapshot_index_metadata


def main():
    parser = argparse.ArgumentParser(description="Promote Gate 8J snapshot/index metadata after local validation.")
    parser.add_argument("--registry", required=True, help="Path to snapshots/main_v1/source_snapshots.json.")
    parser.add_argument("--readiness-config", required=True, help="Path to configs/gate8/main_v1_readiness.yaml.")
    parser.add_argument("--repo-root", default=str(ROOT), help="Repository root for resolving local artifact paths.")
    args = parser.parse_args()

    summary = promote_snapshot_index_metadata(args.registry, args.readiness_config, Path(args.repo_root))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["promoted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run promotion tests before touching real metadata**

Run:

```powershell
python -m pytest tests/test_gate8_snapshot_index_promotion.py -v
```

Expected: PASS.

- [ ] **Step 3: Run inspect CLI on current metadata**

Run:

```powershell
python scripts/check_gate8_snapshot_index_promotion.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml --require-promotable
```

Expected: exit `0` and print `promotable: true`.

- [ ] **Step 4: Promote current metadata**

Run:

```powershell
python scripts/promote_gate8_snapshot_indexes.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
```

Expected: exit `0`, `promoted: true`, and only these tracked metadata files change:

- `snapshots/main_v1/source_snapshots.json`
- `configs/gate8/main_v1_readiness.yaml`

- [ ] **Step 5: Verify snapshot readiness passes and freeze still fails**

Run:

```powershell
python scripts/check_gate8_snapshot_readiness.py --registry snapshots/main_v1/source_snapshots.json --require-ready
```

Expected: exit `0`, `gate8_ready: true`.

Run:

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml --require-ready
```

Expected: exit `1`, `freeze_ready: false`.

- [ ] **Step 6: Commit promotion CLI and metadata promotion**

Run:

```powershell
git add scripts/promote_gate8_snapshot_indexes.py snapshots/main_v1/source_snapshots.json configs/gate8/main_v1_readiness.yaml
git commit -m "feat: promote gate8j snapshot index metadata"
```

Expected: commit succeeds.

---

### Task 4: Add Gate 8J Docs, Card, And Readiness References

**Files:**
- Create: `docs/gate8-snapshot-index-promotion.md`
- Create: `experiments/cards/E015-gate8-snapshot-index-promotion.md`
- Modify: `README.md`
- Modify: `docs/main-comparison-readiness.md`
- Modify: `configs/gate8/main_v1_readiness.yaml`

- [ ] **Step 1: Create Gate 8J documentation**

Create `docs/gate8-snapshot-index-promotion.md` with:

```markdown
# Gate 8 Snapshot Index Promotion

Gate 8J promotes source snapshot and lexical retrieval index metadata after local validation. It does not download datasets, rebuild indexes, evaluate retrieval quality, run baselines, call models, select a provider, freeze prompts, approve budget, create result artifacts, or pass Gate 8 by itself.

## What This Clears

Gate 8J clears stale dataset and index readiness blockers when all three `main_v1` datasets have:

- locked source snapshot metadata
- local dataset snapshot paths
- local lexical index manifests
- index manifests matching dataset id, split, source snapshot id, and processed corpus hash

## Commands

Inspect promotion readiness:

```powershell
python scripts/check_gate8_snapshot_index_promotion.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
```

Promote validated metadata:

```powershell
python scripts/promote_gate8_snapshot_indexes.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
```

## Remaining Gate 8 Blockers

After promotion, Gate 8 still remains blocked by provider evidence, prompt and generation config freeze, cost budget approval, execution card, reproducibility review, baseline execution, and metric record generation.
````

- [ ] **Step 2: Create E015 card**

Create `experiments/cards/E015-gate8-snapshot-index-promotion.md` with:

````markdown
# E015 Gate 8 Snapshot Index Promotion

## Purpose

Validate existing local source snapshot and lexical retrieval index metadata, then promote tracked snapshot/index readiness metadata.

## Execution Status

This is a metadata-only readiness card. It authorizes only local inspection and tracked metadata promotion.

## Authorized Commands

```powershell
python scripts/check_gate8_snapshot_index_promotion.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
python scripts/promote_gate8_snapshot_indexes.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
```

## Not Authorized

- dataset downloads
- index rebuilding
- retrieval evaluation
- baseline execution
- model calls
- embedding calls
- reranker calls
- provider or model selection
- live pricing checks
- prompt freeze
- budget approval
- result artifact creation

## Success Criteria

- snapshot/index promotion check reports promotable metadata
- snapshot records are promoted to `ready`
- `main_v1_readiness.yaml` contains concrete dataset and index metadata
- strict snapshot readiness passes
- strict freeze readiness still fails
- Gate 8 remains readiness in progress
````

- [ ] **Step 3: Update README**

In `README.md`, add:

````markdown
- `docs/gate8-snapshot-index-promotion.md` - Gate 8J source snapshot and local index promotion rules
````

Add scripts:

```markdown
- `scripts/check_gate8_snapshot_index_promotion.py` - local snapshot/index promotion readiness checker
- `scripts/promote_gate8_snapshot_indexes.py` - metadata-only snapshot/index promotion command
```

- [ ] **Step 4: Update main comparison readiness doc**

In `docs/main-comparison-readiness.md`, add a Gate 8J section after Gate 8E:

````markdown
Gate 8J promotes snapshot/index metadata after local validation:

```powershell
python scripts/check_gate8_snapshot_index_promotion.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
python scripts/promote_gate8_snapshot_indexes.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
```

This promotion may make strict snapshot readiness pass, but it does not run baselines, call models, compute metrics, create result artifacts, or pass Gate 8.
````

Use four backticks around the Markdown snippet in the plan executor if nested code fences are needed.

- [ ] **Step 5: Update readiness config references**

In `configs/gate8/main_v1_readiness.yaml`, add a `snapshot_index_promotion_check` block near the other readiness check blocks:

```yaml
snapshot_index_promotion_check:
  command: python scripts/check_gate8_snapshot_index_promotion.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
  promote_command: python scripts/promote_gate8_snapshot_indexes.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml
  authorized_scope: metadata_promotion_only
  runs_baselines: false
  calls_models: false
  creates_result_artifacts: false
```

- [ ] **Step 6: Run docs/config checks**

Run:

```powershell
Select-String -Path docs\*.md,experiments\cards\*.md,README.md,configs\gate8\*.yaml -Pattern ('TB' + 'D|TO' + 'DO|turn[0-9]+')
```

Expected: no matches.

Run:

```powershell
python -m pytest tests/test_gate8_snapshot_index_promotion.py tests/test_gate8_snapshot_readiness.py tests/test_gate8_freeze_readiness.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit docs and references**

Run:

```powershell
git add docs/gate8-snapshot-index-promotion.md experiments/cards/E015-gate8-snapshot-index-promotion.md README.md docs/main-comparison-readiness.md configs/gate8/main_v1_readiness.yaml
git commit -m "docs: document gate8j snapshot index promotion"
```

Expected: commit succeeds.

---

### Task 5: Final Verification

**Files:**
- Verify only; no edits.

- [ ] **Step 1: Run relevant tests**

Run:

```powershell
python -m pytest tests/test_gate7_offline_pilot.py tests/test_gate8_snapshot_readiness.py tests/test_gate8_lexical_index.py tests/test_gate8_snapshot_index_promotion.py tests/test_gate8_freeze_readiness.py tests/test_gate8_prompt_config_readiness.py tests/test_gate8_provider_evidence_readiness.py -v
```

Expected: PASS.

- [ ] **Step 2: Verify snapshot readiness now passes**

Run:

```powershell
python scripts/check_gate8_snapshot_readiness.py --registry snapshots/main_v1/source_snapshots.json --require-ready
```

Expected: exit `0` and print `gate8_ready: true`.

- [ ] **Step 3: Verify freeze readiness still fails**

Run:

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml --require-ready
```

Expected: exit `1` and print `freeze_ready: false`.

- [ ] **Step 4: Verify provider evidence strict still fails**

Run:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --require-ready
```

Expected: exit `1` and print `provider_evidence_ready: false`.

- [ ] **Step 5: Verify prompt/config strict still fails**

Run:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml --require-ready
```

Expected: exit `1` and print `prompt_config_ready: false`.

- [ ] **Step 6: Run placeholder and report-link scan**

Run:

```powershell
Select-String -Path docs\*.md,experiments\cards\*.md,README.md,configs\gate8\*.yaml,snapshots\main_v1\*.json -Pattern ('TB' + 'D|TO' + 'DO|turn[0-9]+')
```

Expected: no matches.

- [ ] **Step 7: Check ignored files and tracked status**

Run:

```powershell
git status --short --ignored
```

Expected: no tracked changes. Ignored generated directories such as `.pytest_cache/`, `datasets/`, `artifacts/`, and PDF files may appear.

---

## Self-Review

Spec coverage:

- Snapshot/index validator is covered by Tasks 1 and 2.
- Promotion command is covered by Task 3.
- Metadata promotion of snapshot statuses and readiness config dataset fields is covered by Task 3.
- Docs and non-running card are covered by Task 4.
- Strict snapshot pass and freeze/provider/prompt strict fail are covered by Task 5.

Scope check:

- The plan does not download datasets, rebuild indexes, run retrieval evaluation, run baselines, call providers, freeze prompts, approve budgets, or create result artifacts.
- Gate 8 remains blocked after Gate 8J because freeze, provider evidence, prompt/config, budget, execution card, baseline runs, and metric records remain incomplete.

Type consistency:

- Function names are consistent across tests, module, and CLIs: `build_snapshot_index_promotion_summary`, `promote_snapshot_index_metadata`, and `validate_snapshot_index_record`.
- Public commands match the design spec and docs.

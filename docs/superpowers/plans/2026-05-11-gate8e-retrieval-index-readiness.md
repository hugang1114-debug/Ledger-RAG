# Gate 8E Retrieval Index Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build deterministic local lexical retrieval index artifacts for HotpotQA, 2WikiMultihopQA, and MuSiQue, and record their index manifest paths without passing Gate 8.

**Architecture:** Add a small `ledger_rag_retrieval` package that reads locked source snapshot corpora, tokenizes text deterministically, writes `documents.jsonl`, `postings.jsonl`, and `index_manifest.json`, then updates only `retrieval_index_path` in the source snapshot registry. Generated index artifacts stay ignored under `datasets/retrieval_indexes/main_v1/`.

**Tech Stack:** Python standard library only, pytest, existing `ledger_rag_snapshot.hashing` and `ledger_rag_snapshot.registry` helpers.

---

## File Structure

- Create `src/ledger_rag_retrieval/__init__.py`: package marker and public exports.
- Create `src/ledger_rag_retrieval/lexical_index.py`: tokenizer, corpus loading, deterministic inverted index builder, manifest writer, registry update helper.
- Create `scripts/build_gate8_lexical_indexes.py`: CLI for all datasets or a single dataset.
- Create `tests/test_gate8_lexical_index.py`: fixture-driven tests for tokenization, deterministic output, registry safety, CLI behavior, and readiness semantics.
- Modify `tests/test_gate8_snapshot_readiness.py`: update assertions after real index paths are built.
- Modify `README.md`: document the Gate 8E builder.
- Modify `docs/main-comparison-readiness.md`: add Gate 8E command and clarify it does not pass Gate 8.
- Modify `docs/source-snapshot-protocol.md`: add retrieval index artifact rules.
- Modify `configs/gate8/main_v1_readiness.yaml`: add index build command and expected artifact root.
- Create `experiments/cards/E010-gate8-lexical-index-readiness.md`: authorize only local lexical index artifact construction.
- Modify `snapshots/main_v1/source_snapshots.json`: after running the CLI, set `retrieval_index_path` for HotpotQA, 2WikiMultihopQA, and MuSiQue. Keep `status: source_ready`.

---

### Task 1: Failing Tests For Lexical Index Readiness

**Files:**
- Create: `tests/test_gate8_lexical_index.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_gate8_lexical_index.py` with these tests:

```python
import json
import subprocess
import sys
from pathlib import Path
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

    assert result.returncode == 2
    assert "unknown dataset id" in result.stdout
```

- [ ] **Step 2: Run the new test file and confirm it fails for missing implementation**

Run:

```powershell
python -m pytest tests/test_gate8_lexical_index.py -v
```

Expected: collection fails with `ModuleNotFoundError: No module named 'ledger_rag_retrieval'`.

---

### Task 2: Lexical Index Module

**Files:**
- Create: `src/ledger_rag_retrieval/__init__.py`
- Create: `src/ledger_rag_retrieval/lexical_index.py`
- Test: `tests/test_gate8_lexical_index.py`

- [ ] **Step 1: Create package marker**

Create `src/ledger_rag_retrieval/__init__.py`:

```python
from ledger_rag_retrieval.lexical_index import (
    TOKENIZER_VERSION,
    build_lexical_index,
    hash_corpus_rows,
    load_corpus_rows,
    tokenize,
    update_registry_with_index_paths,
)


__all__ = [
    "TOKENIZER_VERSION",
    "build_lexical_index",
    "hash_corpus_rows",
    "load_corpus_rows",
    "tokenize",
    "update_registry_with_index_paths",
]
```

- [ ] **Step 2: Implement the lexical index module**

Create `src/ledger_rag_retrieval/lexical_index.py`:

```python
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from ledger_rag_snapshot.hashing import sha256_text
from ledger_rag_snapshot.registry import UNSET_VALUES


TOKENIZER_VERSION = "lexical_v1_ascii_word"
RETRIEVER_FAMILY = "lexical"
REQUIRED_SOURCE_FIELDS = ["dataset_id", "split", "dataset_path", "source_snapshot_id", "processed_corpus_hash", "status"]


def json_dumps(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    with Path(path).open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json_dumps(row) + "\n")


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def load_corpus_rows(corpus_path):
    rows = []
    with Path(corpus_path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def hash_corpus_rows(rows):
    payload = "".join(json_dumps(row) + "\n" for row in rows)
    return sha256_text(payload)


def hash_rows(rows):
    return sha256_text("".join(json_dumps(row) + "\n" for row in rows))


def is_unset(value):
    return value is None or (isinstance(value, str) and value.strip().lower() in UNSET_VALUES)


def validate_source_record(record):
    for field in REQUIRED_SOURCE_FIELDS:
        if field not in record:
            raise ValueError(f"{record.get('dataset_id', 'unknown')}: missing {field}")
        if field in {"dataset_path", "source_snapshot_id", "processed_corpus_hash"} and is_unset(record[field]):
            raise ValueError(f"{record.get('dataset_id', 'unknown')}: {field} is unset")
    if record["status"] != "source_ready":
        raise ValueError(f"{record['dataset_id']}: status must be source_ready")


def corpus_path_for_record(record):
    return Path(record["dataset_path"]) / "processed" / "corpus.jsonl"


def index_dir_for_record(record, index_root):
    return Path(index_root) / record["dataset_id"] / record["split"]


def build_documents_and_postings(rows):
    documents = []
    postings = defaultdict(list)

    for internal_doc_id, row in enumerate(sorted(rows, key=lambda item: str(item["source_doc_id"]))):
        text = row.get("text", "")
        tokens = tokenize(text)
        counts = Counter(tokens)
        documents.append(
            {
                "internal_doc_id": internal_doc_id,
                "source_doc_id": str(row["source_doc_id"]),
                "source_uri": row.get("source_uri", ""),
                "title": row.get("title", ""),
                "source_hash": row.get("source_hash"),
                "text_hash": sha256_text(text),
                "token_count": len(tokens),
            }
        )
        for token, term_frequency in sorted(counts.items()):
            postings[token].append({"internal_doc_id": internal_doc_id, "term_frequency": term_frequency})

    posting_rows = []
    for token in sorted(postings):
        token_postings = sorted(postings[token], key=lambda item: item["internal_doc_id"])
        posting_rows.append(
            {
                "token": token,
                "document_frequency": len(token_postings),
                "total_term_frequency": sum(item["term_frequency"] for item in token_postings),
                "postings": token_postings,
            }
        )
    return documents, posting_rows


def build_lexical_index(record, index_root):
    validate_source_record(record)
    corpus_path = corpus_path_for_record(record)
    if not corpus_path.exists():
        raise FileNotFoundError(f"{record['dataset_id']}: missing corpus file {corpus_path}")

    rows = load_corpus_rows(corpus_path)
    actual_corpus_hash = hash_corpus_rows(rows)
    if actual_corpus_hash != record["processed_corpus_hash"]:
        raise ValueError(f"{record['dataset_id']}: processed corpus hash mismatch")

    documents, posting_rows = build_documents_and_postings(rows)
    output_dir = index_dir_for_record(record, index_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    documents_path = output_dir / "documents.jsonl"
    postings_path = output_dir / "postings.jsonl"
    manifest_path = output_dir / "index_manifest.json"
    write_jsonl(documents_path, documents)
    write_jsonl(postings_path, posting_rows)

    documents_hash = hash_rows(documents)
    postings_hash = hash_rows(posting_rows)
    index_hash = sha256_text(json_dumps({"documents_hash": documents_hash, "postings_hash": postings_hash}))
    manifest = {
        "dataset_id": record["dataset_id"],
        "split": record["split"],
        "source_snapshot_id": record["source_snapshot_id"],
        "processed_corpus_hash": record["processed_corpus_hash"],
        "retriever_family": RETRIEVER_FAMILY,
        "tokenizer_version": TOKENIZER_VERSION,
        "document_count": len(documents),
        "term_count": len(posting_rows),
        "documents_hash": documents_hash,
        "postings_hash": postings_hash,
        "index_hash": index_hash,
        "build_command_record": {
            "command": "python scripts/build_gate8_lexical_indexes.py --registry snapshots/main_v1/source_snapshots.json --index-root datasets/retrieval_indexes/main_v1",
            "script_path": "scripts/build_gate8_lexical_indexes.py",
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        },
        "paths": {
            "documents": documents_path.as_posix(),
            "postings": postings_path.as_posix(),
            "index_manifest": manifest_path.as_posix(),
        },
    }
    write_json(manifest_path, manifest)
    return manifest


def update_registry_with_index_paths(registry, manifests):
    manifest_by_dataset = {manifest["dataset_id"]: manifest for manifest in manifests}
    updated = json.loads(json.dumps(registry))
    for record in updated.get("snapshots", []):
        manifest = manifest_by_dataset.get(record.get("dataset_id"))
        if manifest:
            record["retrieval_index_path"] = manifest["paths"]["index_manifest"]
    return updated
```

- [ ] **Step 3: Run module tests**

Run:

```powershell
python -m pytest tests/test_gate8_lexical_index.py::test_tokenize_is_deterministic_and_simple tests/test_gate8_lexical_index.py::test_build_lexical_index_outputs_stable_files tests/test_gate8_lexical_index.py::test_registry_update_changes_only_retrieval_index_path -v
```

Expected: all three tests pass.

- [ ] **Step 4: Commit module and tests**

Run:

```powershell
git add src/ledger_rag_retrieval/__init__.py src/ledger_rag_retrieval/lexical_index.py tests/test_gate8_lexical_index.py
git commit -m "feat: add lexical index builder"
```

---

### Task 3: Gate 8E CLI

**Files:**
- Create: `scripts/build_gate8_lexical_indexes.py`
- Modify: `tests/test_gate8_lexical_index.py`

- [ ] **Step 1: Implement the CLI**

Create `scripts/build_gate8_lexical_indexes.py`:

```python
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_retrieval.lexical_index import build_lexical_index, update_registry_with_index_paths
from ledger_rag_snapshot.registry import load_registry, validate_registry


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def selected_records(registry, dataset_id):
    snapshots = registry.get("snapshots", [])
    if dataset_id:
        matches = [record for record in snapshots if record.get("dataset_id") == dataset_id]
        if not matches:
            raise ValueError(f"unknown dataset id: {dataset_id}")
        return matches
    return snapshots


def main():
    parser = argparse.ArgumentParser(description="Build Gate 8E local lexical retrieval indexes.")
    parser.add_argument("--registry", required=True, help="Path to snapshots/main_v1/source_snapshots.json.")
    parser.add_argument("--index-root", required=True, help="Ignored local output root for retrieval index artifacts.")
    parser.add_argument("--dataset", help="Optional dataset id to build: hotpotqa, 2wikimultihopqa, or musique.")
    args = parser.parse_args()

    registry_path = Path(args.registry)
    try:
        registry = load_registry(registry_path)
        records = selected_records(registry, args.dataset)
        validation_errors = validate_registry(registry)
        allowed_fixture_case = args.dataset == "fixtureqa" and len(registry.get("snapshots", [])) == 1
        if validation_errors and not allowed_fixture_case:
            print(json.dumps({"status": "registry_invalid", "validation_errors": validation_errors}, indent=2, sort_keys=True))
            return 2
        manifests = [build_lexical_index(record, args.index_root) for record in records]
        updated = update_registry_with_index_paths(registry, manifests)
        write_json(registry_path, updated)
    except Exception as exc:
        print(json.dumps({"status": "index_build_failed", "error": str(exc)}, indent=2, sort_keys=True))
        return 2

    print(
        json.dumps(
            {
                "status": "index_ready",
                "built_count": len(manifests),
                "datasets": [manifest["dataset_id"] for manifest in manifests],
                "index_manifests": [manifest["paths"]["index_manifest"] for manifest in manifests],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run CLI tests**

Run:

```powershell
python -m pytest tests/test_gate8_lexical_index.py::test_cli_builds_fixture_index_and_keeps_gate8_not_ready tests/test_gate8_lexical_index.py::test_cli_refuses_unknown_dataset -v
```

Expected: both tests pass.

- [ ] **Step 3: Commit CLI**

Run:

```powershell
git add scripts/build_gate8_lexical_indexes.py tests/test_gate8_lexical_index.py
git commit -m "feat: add gate8 lexical index cli"
```

---

### Task 4: Docs, Config, And Experiment Card

**Files:**
- Modify: `README.md`
- Modify: `docs/main-comparison-readiness.md`
- Modify: `docs/source-snapshot-protocol.md`
- Modify: `configs/gate8/main_v1_readiness.yaml`
- Create: `experiments/cards/E010-gate8-lexical-index-readiness.md`

- [ ] **Step 1: Update README**

Add this bullet near the other Gate 8 scripts:

```markdown
- `scripts/build_gate8_lexical_indexes.py` - local deterministic lexical index builder for Gate 8E readiness
```

- [ ] **Step 2: Update main comparison readiness doc**

Add this section after the Gate 8D source snapshot section:

````markdown
Gate 8E builds local lexical retrieval index artifacts for all three source-ready datasets:

```powershell
python scripts/build_gate8_lexical_indexes.py --registry snapshots/main_v1/source_snapshots.json --index-root datasets/retrieval_indexes/main_v1
```

This command may set `retrieval_index_path` for HotpotQA, 2WikiMultihopQA, and MuSiQue, but it does not run retrieval evaluation, does not run baselines, and does not pass Gate 8.
````

- [ ] **Step 3: Update source snapshot protocol**

Add this section after the source builder list:

````markdown
The approved Gate 8E retrieval index builder is limited to local lexical index artifacts:

```powershell
python scripts/build_gate8_lexical_indexes.py --registry snapshots/main_v1/source_snapshots.json --index-root datasets/retrieval_indexes/main_v1
```

It reads locked `processed/corpus.jsonl` files, writes ignored index artifacts under `datasets/retrieval_indexes/main_v1/`, and updates only `retrieval_index_path` in the tracked registry.
````

- [ ] **Step 4: Update Gate 8 readiness config**

Add under `source_snapshot_builds` or a new `retrieval_index_builds` section:

```yaml
retrieval_index_builds:
  main_v1_lexical:
    command: python scripts/build_gate8_lexical_indexes.py --registry snapshots/main_v1/source_snapshots.json --index-root datasets/retrieval_indexes/main_v1
    authorized_scope: lexical_index_artifacts_only
    index_root: datasets/retrieval_indexes/main_v1
    retriever_family: lexical
    calls_models: false
    runs_baselines: false
    runs_retrieval_evaluation: false
```

- [ ] **Step 5: Add experiment card**

Create `experiments/cards/E010-gate8-lexical-index-readiness.md`:

````markdown
# E010 Gate 8 Lexical Index Readiness

## Purpose

Build deterministic local lexical retrieval index artifacts for the three `main_v1` source-ready datasets. This card authorizes index artifact construction only.

## Authorized Datasets

- HotpotQA dev distractor
- 2WikiMultihopQA dev
- MuSiQue answerable dev

## Authorized Command

```powershell
python scripts/build_gate8_lexical_indexes.py --registry snapshots/main_v1/source_snapshots.json --index-root datasets/retrieval_indexes/main_v1
```

## Expected Outputs

- ignored index artifacts under `datasets/retrieval_indexes/main_v1/`
- tracked `retrieval_index_path` updates in `snapshots/main_v1/source_snapshots.json`
- dataset `status` remains `source_ready`
- Gate 8 strict readiness remains blocked

## Failure Criteria

- model, embedding, reranker, or provider call is made
- retrieval evaluation is run
- baseline execution is run
- source snapshot hashes are changed
- dataset status is changed to `ready`
- generated index files are staged into git

## Cost Class

Local CPU and storage only. No model/API/provider cost is authorized.
````

- [ ] **Step 6: Run doc placeholder scan**

Run:

```powershell
Select-String -Path docs\*.md,docs\superpowers\*.md,docs\superpowers\*\*.md,experiments\cards\*.md,README.md,configs\gate8\*.yaml -Pattern 'TB[D]|TO[D]O|turn[0-9]+'
```

Expected: no output.

- [ ] **Step 7: Commit docs and card**

Run:

```powershell
git add README.md docs/main-comparison-readiness.md docs/source-snapshot-protocol.md configs/gate8/main_v1_readiness.yaml experiments/cards/E010-gate8-lexical-index-readiness.md
git commit -m "docs: document gate8e lexical index readiness"
```

---

### Task 5: Build Real Gate 8E Index Artifacts And Verify

**Files:**
- Modify: `snapshots/main_v1/source_snapshots.json`
- Modify: `tests/test_gate8_snapshot_readiness.py`

- [ ] **Step 1: Run the real index build**

Run:

```powershell
python scripts/build_gate8_lexical_indexes.py --registry snapshots/main_v1/source_snapshots.json --index-root datasets/retrieval_indexes/main_v1
```

Expected: JSON output with `status: index_ready`, `built_count: 3`, and datasets `hotpotqa`, `2wikimultihopqa`, and `musique`.

- [ ] **Step 2: Verify generated artifacts exist**

Run:

```powershell
Test-Path datasets\retrieval_indexes\main_v1\hotpotqa\dev_distractor\index_manifest.json
Test-Path datasets\retrieval_indexes\main_v1\2wikimultihopqa\dev\index_manifest.json
Test-Path datasets\retrieval_indexes\main_v1\musique\dev\index_manifest.json
```

Expected: three `True` lines.

- [ ] **Step 3: Update readiness test expectations**

In `tests/test_gate8_snapshot_readiness.py`, change `test_pending_records_are_valid_but_not_gate8_eligible` so it asserts status blockers remain rather than requiring a `retrieval_index_path` blocker:

```python
def test_pending_records_are_valid_but_not_gate8_eligible():
    registry = load_registry(REGISTRY)

    validation_errors = validate_registry(registry)
    blockers = find_gate8_blockers(registry)

    assert validation_errors == []
    assert blockers
    assert {record["status"] for record in registry["snapshots"]} <= {"pending", "source_ready"}
    assert all(record["retrieval_index_path"] != "unset" for record in registry["snapshots"])
    assert any(blocker["field"] == "status" for blocker in blockers)
```

- [ ] **Step 4: Run full verification**

Run:

```powershell
python -m pytest tests/test_gate7_offline_pilot.py tests/test_gate8_snapshot_readiness.py tests/test_hotpotqa_snapshot_builder.py tests/test_2wiki_snapshot_builder.py tests/test_musique_snapshot_builder.py tests/test_gate8_lexical_index.py -v
```

Expected: all tests pass.

Run:

```powershell
python scripts/check_gate8_snapshot_readiness.py --registry snapshots/main_v1/source_snapshots.json
```

Expected: `source_ready_count: 3`, no `retrieval_index_path` blockers, and `gate8_ready: false`.

Run:

```powershell
python scripts/check_gate8_snapshot_readiness.py --registry snapshots/main_v1/source_snapshots.json --require-ready; if ($LASTEXITCODE -ne 1) { Write-Error "expected strict readiness to exit 1 while status blockers remain"; exit 1 }; exit 0
```

Expected: command exits `0` because strict readiness returned `1`.

Run:

```powershell
Select-String -Path docs\*.md,docs\superpowers\*.md,docs\superpowers\*\*.md,experiments\cards\*.md,README.md,configs\gate8\*.yaml,snapshots\main_v1\*.json -Pattern 'TB[D]|TO[D]O|turn[0-9]+'
```

Expected: no output.

Run:

```powershell
git diff --check
git status --short --ignored
```

Expected: `git diff --check` exits `0`; generated files under `datasets/` are ignored.

- [ ] **Step 5: Commit registry and tests**

Run:

```powershell
git add snapshots/main_v1/source_snapshots.json tests/test_gate8_snapshot_readiness.py
git commit -m "feat: build gate8 lexical indexes"
```

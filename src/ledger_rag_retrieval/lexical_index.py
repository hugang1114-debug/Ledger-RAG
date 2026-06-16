import json
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path

from ledger_rag_snapshot.hashing import sha256_text
from ledger_rag_snapshot.registry import UNSET_VALUES


TOKENIZER_VERSION = "lexical_v1_ascii_word"
RETRIEVER_FAMILY = "lexical"
REQUIRED_SOURCE_FIELDS = {
    "dataset_id",
    "split",
    "dataset_path",
    "source_snapshot_id",
    "processed_corpus_hash",
    "status",
}
BUILD_COMMAND = (
    "python scripts/build_gate8_lexical_indexes.py "
    "--registry snapshots/main_v1/source_snapshots.json "
    "--index-root datasets/retrieval_indexes/main_v1"
)
WINDOWS_INVALID_PATH_CHARS = set('<>:"|?*')


def _canonical_json(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def atomic_write_json(path, payload):
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _atomic_write_text(path, text)


def atomic_write_jsonl(path, rows):
    text = "".join(_canonical_json(row) + "\n" for row in rows)
    _atomic_write_text(path, text)


def _atomic_write_text(path, text):
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


def tokenize(text):
    return re.findall(r"[a-z0-9]+", str(text).lower())


def load_corpus_rows(corpus_path):
    rows = []
    with Path(corpus_path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def hash_corpus_rows(rows):
    return _hash_jsonl_rows(rows)


def _hash_jsonl_rows(rows):
    return sha256_text("".join(_canonical_json(row) + "\n" for row in rows))


def _is_unset(value):
    return value is None or (isinstance(value, str) and value.strip().lower() in UNSET_VALUES)


def _validate_source_record(record):
    missing = sorted(REQUIRED_SOURCE_FIELDS - set(record))
    if missing:
        raise ValueError(f"{record.get('dataset_id', 'unknown')}: missing required fields: {', '.join(missing)}")

    if record["status"] != "source_ready":
        raise ValueError(f"{record['dataset_id']}: status must be source_ready")

    for field in ("dataset_path", "source_snapshot_id", "processed_corpus_hash"):
        if _is_unset(record[field]):
            raise ValueError(f"{record['dataset_id']}: {field} is unset")

    for field in ("dataset_id", "split"):
        _validate_safe_path_component(field, record[field])


def _validate_safe_path_component(field, value):
    component = str(value)
    path = Path(component)
    if (
        not component
        or component in {".", ".."}
        or path.drive
        or path.root
        or path.anchor
        or len(path.parts) != 1
        or "/" in component
        or "\\" in component
        or any(char in WINDOWS_INVALID_PATH_CHARS for char in component)
    ):
        raise ValueError(f"{field} must be a safe single relative path component")


def _corpus_path_for_record(record):
    return Path(record["dataset_path"]) / "processed" / "corpus.jsonl"


def _index_dir_for_record(record, index_root):
    return Path(index_root) / record["dataset_id"] / record["split"]


def _build_documents_and_postings(rows):
    documents = []
    postings = defaultdict(list)

    sorted_rows = sorted(rows, key=lambda row: str(row["source_doc_id"]))
    for internal_doc_id, row in enumerate(sorted_rows):
        text = row.get("text", "")
        tokens = tokenize(text)
        token_counts = Counter(tokens)
        documents.append(
            {
                "internal_doc_id": internal_doc_id,
                "source_doc_id": str(row["source_doc_id"]),
                "source_uri": row.get("source_uri", ""),
                "title": row.get("title", ""),
                "source_hash": row.get("source_hash"),
                "text_hash": sha256_text(str(text)),
                "token_count": len(tokens),
            }
        )

        for token, term_frequency in token_counts.items():
            postings[token].append(
                {
                    "internal_doc_id": internal_doc_id,
                    "term_frequency": term_frequency,
                }
            )

    posting_rows = []
    for token in sorted(postings):
        token_postings = sorted(postings[token], key=lambda posting: posting["internal_doc_id"])
        posting_rows.append(
            {
                "token": token,
                "document_frequency": len(token_postings),
                "total_term_frequency": sum(posting["term_frequency"] for posting in token_postings),
                "postings": token_postings,
            }
        )

    return documents, posting_rows


def build_lexical_index(record, index_root):
    _validate_source_record(record)

    corpus_path = _corpus_path_for_record(record)
    rows = load_corpus_rows(corpus_path)
    actual_corpus_hash = hash_corpus_rows(rows)
    if actual_corpus_hash != record["processed_corpus_hash"]:
        raise ValueError(f"{record['dataset_id']}: processed corpus hash mismatch")

    documents, posting_rows = _build_documents_and_postings(rows)
    index_dir = _index_dir_for_record(record, index_root)
    index_dir.mkdir(parents=True, exist_ok=True)

    documents_path = index_dir / "documents.jsonl"
    postings_path = index_dir / "postings.jsonl"
    manifest_path = index_dir / "index_manifest.json"

    documents_hash = _hash_jsonl_rows(documents)
    postings_hash = _hash_jsonl_rows(posting_rows)
    index_hash = sha256_text(
        _canonical_json(
            {
                "documents_hash": documents_hash,
                "postings_hash": postings_hash,
            }
        )
    )

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
            "command": BUILD_COMMAND,
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "script_path": "scripts/build_gate8_lexical_indexes.py",
        },
        "paths": {
            "documents": documents_path.as_posix(),
            "postings": postings_path.as_posix(),
            "index_manifest": manifest_path.as_posix(),
        },
    }

    atomic_write_jsonl(documents_path, documents)
    atomic_write_jsonl(postings_path, posting_rows)
    atomic_write_json(manifest_path, manifest)
    return manifest


def update_registry_with_index_paths(registry, manifests):
    manifest_by_dataset = {manifest["dataset_id"]: manifest for manifest in manifests}
    updated = deepcopy(registry)
    for record in updated.get("snapshots", []):
        manifest = manifest_by_dataset.get(record.get("dataset_id"))
        if manifest is not None:
            record["retrieval_index_path"] = manifest["paths"]["index_manifest"]
    return updated

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
    write_text_atomic(target, text)


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


def _registry_validation_errors(registry):
    errors = validate_registry(registry)
    snapshots = registry.get("snapshots", [])
    if not isinstance(snapshots, list):
        return errors

    actual_dataset_ids = {record.get("dataset_id") for record in snapshots if isinstance(record, dict)}
    if actual_dataset_ids == {"fixtureqa"}:
        return [
            error
            for error in errors
            if not (
                error.get("field") == "dataset_id"
                and error.get("message") == "registry must contain exactly the main_v1 dataset ids"
            )
        ]
    return errors


def _load_index_manifest(record, repo_root):
    dataset_id = record.get("dataset_id", "unknown")
    index_path_value = record.get("retrieval_index_path")
    if _is_unset(index_path_value):
        return None, [_blocker(dataset_id, "retrieval_index_path", "retrieval index path is unset")]

    index_path = _repo_path(repo_root, index_path_value)
    if not index_path.exists():
        return None, [_blocker(dataset_id, "retrieval_index_path", "retrieval index manifest does not exist")]
    if not index_path.is_file():
        return None, [_blocker(dataset_id, "retrieval_index_path", "retrieval index manifest is not a file")]

    try:
        return load_json(index_path), []
    except OSError:
        return None, [_blocker(dataset_id, "retrieval_index_path", "retrieval index manifest cannot be read")]
    except json.JSONDecodeError as exc:
        return None, [
            _blocker(dataset_id, "retrieval_index_path", f"retrieval index manifest is invalid JSON: {exc.msg}")
        ]


def validate_snapshot_index_record(record, repo_root=ROOT):
    dataset_id = record.get("dataset_id", "unknown")
    blockers = []

    for field in sorted(REQUIRED_FIELDS - set(record)):
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

    for field in sorted(REQUIRED_INDEX_FIELDS - set(manifest)):
        blockers.append(_blocker(dataset_id, field, "index manifest is missing required field"))

    comparisons = (
        ("dataset_id", "index dataset id mismatch"),
        ("split", "index split mismatch"),
        ("source_snapshot_id", "index source snapshot id mismatch"),
        ("processed_corpus_hash", "index processed corpus hash mismatch"),
    )
    for field, message in comparisons:
        if manifest.get(field) != record.get(field):
            blockers.append(_blocker(dataset_id, field, message))

    if manifest.get("retriever_family") != "lexical":
        blockers.append(_blocker(dataset_id, "retriever_family", "index retriever family is not lexical"))

    paths = manifest.get("paths")
    if not isinstance(paths, dict):
        blockers.append(_blocker(dataset_id, "paths", "index manifest paths must be an object"))
    else:
        for path_field in ("documents", "postings", "index_manifest"):
            path_value = paths.get(path_field)
            if _is_unset(path_value):
                blockers.append(_blocker(dataset_id, path_field, f"index {path_field} path is unset"))
            elif not _repo_path(repo_root, path_value).exists():
                blockers.append(_blocker(dataset_id, path_field, f"index {path_field} path does not exist"))
        if (
            not _is_unset(paths.get("index_manifest"))
            and str(paths.get("index_manifest")) != str(record.get("retrieval_index_path"))
        ):
            blockers.append(
                _blocker(
                    dataset_id,
                    "retrieval_index_path",
                    "index manifest path does not match snapshot record",
                )
            )

    for numeric_field in ("document_count", "term_count"):
        value = manifest.get(numeric_field)
        if not isinstance(value, int) or value <= 0:
            blockers.append(_blocker(dataset_id, numeric_field, f"index {numeric_field} must be positive"))

    return blockers


def build_snapshot_index_promotion_summary(registry_path, readiness_config_path, repo_root=ROOT):
    registry = load_json(registry_path)
    validation_errors = _registry_validation_errors(registry)
    snapshots = registry.get("snapshots", [])
    promotion_blockers = []
    datasets = []

    if not validation_errors and isinstance(snapshots, list):
        actual_dataset_ids = {record.get("dataset_id") for record in snapshots if isinstance(record, dict)}
        if actual_dataset_ids not in (EXPECTED_MAIN_V1_DATASETS, {"fixtureqa"}):
            promotion_blockers.append(
                _blocker("registry", "dataset_id", "snapshot promotion supports main_v1 dataset ids only")
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
        if lines[index] and not lines[index].startswith(" "):
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
        if lines[index] and not lines[index].startswith(" "):
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
    return lines[:start] + ["not_ready:"] + kept + [""] + lines[end:]


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
    updated_readiness = sync_readiness_config_text(readiness_path.read_text(encoding="utf-8"), updated_registry)

    write_json_atomic(registry_path, updated_registry)
    write_text_atomic(readiness_path, updated_readiness)

    return {
        "promoted": True,
        **build_snapshot_index_promotion_summary(registry_path, readiness_config_path, repo_root),
    }

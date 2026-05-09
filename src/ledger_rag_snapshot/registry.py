import json
from pathlib import Path


REQUIRED_FIELDS = {
    "dataset_id",
    "dataset_name",
    "decision",
    "split",
    "official_url",
    "license_note",
    "source_snapshot_id",
    "dataset_path",
    "raw_data_hash",
    "processed_corpus_hash",
    "split_hash",
    "build_command_record",
    "retrieval_index_path",
    "storage_class",
    "status",
    "notes",
}

READINESS_FIELDS = [
    "license_note",
    "source_snapshot_id",
    "dataset_path",
    "raw_data_hash",
    "processed_corpus_hash",
    "split_hash",
    "build_command_record",
    "retrieval_index_path",
]

EXPECTED_MAIN_V1_DATASETS = {"hotpotqa", "2wikimultihopqa", "musique"}
ALLOWED_STORAGE_CLASSES = {"small", "medium", "large", "unknown"}
ALLOWED_STATUSES = {"pending", "ready"}
UNSET_VALUES = {"", "unset", "not_recorded", "not_applicable_for_ready_check"}


def load_registry(path):
    registry_path = Path(path)
    with registry_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _is_unset(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in UNSET_VALUES
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def validate_registry(registry):
    errors = []
    snapshots = registry.get("snapshots")

    if not isinstance(snapshots, list):
        return [{"field": "snapshots", "message": "snapshots must be a list"}]

    seen_dataset_ids = set()
    for index, record in enumerate(snapshots):
        if not isinstance(record, dict):
            errors.append({"index": index, "field": "record", "message": "snapshot record must be an object"})
            continue

        missing = sorted(REQUIRED_FIELDS - set(record))
        for field in missing:
            errors.append({"index": index, "dataset_id": record.get("dataset_id"), "field": field, "message": "missing required field"})

        dataset_id = record.get("dataset_id")
        if dataset_id in seen_dataset_ids:
            errors.append({"index": index, "dataset_id": dataset_id, "field": "dataset_id", "message": "duplicate dataset id"})
        seen_dataset_ids.add(dataset_id)

        if record.get("storage_class") not in ALLOWED_STORAGE_CLASSES:
            errors.append({"index": index, "dataset_id": dataset_id, "field": "storage_class", "message": "invalid storage class"})

        if record.get("status") not in ALLOWED_STATUSES:
            errors.append({"index": index, "dataset_id": dataset_id, "field": "status", "message": "invalid status"})

        if "notes" in record and not isinstance(record["notes"], list):
            errors.append({"index": index, "dataset_id": dataset_id, "field": "notes", "message": "notes must be a list"})

    actual_dataset_ids = {record.get("dataset_id") for record in snapshots if isinstance(record, dict)}
    if actual_dataset_ids != EXPECTED_MAIN_V1_DATASETS:
        errors.append(
            {
                "field": "dataset_id",
                "message": "registry must contain exactly the main_v1 dataset ids",
                "expected": sorted(EXPECTED_MAIN_V1_DATASETS),
                "actual": sorted(item for item in actual_dataset_ids if item),
            }
        )

    return errors


def find_gate8_blockers(registry):
    blockers = []
    for record in registry.get("snapshots", []):
        dataset_id = record.get("dataset_id", "unknown")
        for field in READINESS_FIELDS:
            if _is_unset(record.get(field)):
                blockers.append(
                    {
                        "dataset_id": dataset_id,
                        "field": field,
                        "message": f"{field} is not locked",
                    }
                )
        if record.get("status") != "ready":
            blockers.append(
                {
                    "dataset_id": dataset_id,
                    "field": "status",
                    "message": "snapshot status is not ready",
                }
            )
    return blockers


def build_readiness_summary(registry, registry_path):
    validation_errors = validate_registry(registry)
    blockers = find_gate8_blockers(registry) if not validation_errors else []
    snapshots = registry.get("snapshots", [])

    return {
        "registry_path": str(Path(registry_path)),
        "gate": registry.get("gate", "gate8_main_comparison"),
        "status": registry.get("status", "unknown"),
        "snapshot_count": len(snapshots) if isinstance(snapshots, list) else 0,
        "datasets": [record.get("dataset_id") for record in snapshots if isinstance(record, dict)],
        "validation_errors": validation_errors,
        "blockers": blockers,
        "gate8_ready": not validation_errors and not blockers,
    }

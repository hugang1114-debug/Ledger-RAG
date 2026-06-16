import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_retrieval.lexical_index import build_lexical_index, update_registry_with_index_paths
from ledger_rag_snapshot.registry import load_registry, validate_registry


def write_json(path, payload):
    target = Path(path)
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


def is_allowed_fixture_registry(registry, dataset_id):
    snapshots = registry.get("snapshots")
    return (
        dataset_id == "fixtureqa"
        and isinstance(snapshots, list)
        and len(snapshots) == 1
        and isinstance(snapshots[0], dict)
        and snapshots[0].get("dataset_id") == "fixtureqa"
    )


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
        validation_errors = validate_registry(registry)
        if validation_errors and not is_allowed_fixture_registry(registry, args.dataset):
            print(
                json.dumps(
                    {"status": "registry_invalid", "validation_errors": validation_errors},
                    indent=2,
                    sort_keys=True,
                )
            )
            return 2

        records = selected_records(registry, args.dataset)
        manifests = [build_lexical_index(record, args.index_root) for record in records]
        updated = update_registry_with_index_paths(registry, manifests)
        write_json(registry_path, updated)
    except Exception as exc:
        print(
            json.dumps(
                {"status": "index_build_failed", "error": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
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

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_snapshot.registry import load_registry
from ledger_rag_snapshot.twowiki import (
    TWOWIKI_DATA_IDS_APRIL7_URL,
    TWOWIKI_EVAL_SCRIPT_URL,
    TWOWIKI_LICENSE_URL,
    OfficialSourceUnavailable,
    build_2wiki_snapshot_from_zip,
    download_official_file,
    update_2wiki_registry_record,
)


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build the 2WikiMultihopQA dev source snapshot.")
    parser.add_argument("--registry", required=True, help="Path to snapshots/main_v1/source_snapshots.json.")
    parser.add_argument("--output-root", required=True, help="Ignored local output root for source snapshot artifacts.")
    parser.add_argument("--split", default="dev", choices=["dev"])
    parser.add_argument("--existing-zip", help="Existing official data_ids_april7.zip path; used by tests and reruns.")
    parser.add_argument("--skip-license", action="store_true", help="Do not download the official repository LICENSE.")
    parser.add_argument("--skip-eval-script", action="store_true", help="Do not download the official v1.1 eval script.")
    args = parser.parse_args()

    output_root = Path(args.output_root)
    raw_dir = output_root / "2wikimultihopqa" / args.split / "raw"
    zip_path = Path(args.existing_zip) if args.existing_zip else raw_dir / "data_ids_april7.zip"
    license_path = None
    eval_script_path = None

    try:
        if not args.existing_zip and not zip_path.exists():
            download_official_file(TWOWIKI_DATA_IDS_APRIL7_URL, zip_path)
        if not args.skip_license:
            license_path = raw_dir / "LICENSE"
            if not license_path.exists():
                download_official_file(TWOWIKI_LICENSE_URL, license_path)
        if not args.skip_eval_script:
            eval_script_path = raw_dir / "2wikimultihop_evaluate_v1.1.py"
            if not eval_script_path.exists():
                download_official_file(TWOWIKI_EVAL_SCRIPT_URL, eval_script_path)
    except OfficialSourceUnavailable as exc:
        print(json.dumps({"status": "official_source_unavailable", "error": str(exc)}, indent=2, sort_keys=True))
        return 2

    command_record = {
        "command": "python scripts/build_2wiki_source_snapshot.py --registry snapshots/main_v1/source_snapshots.json --output-root datasets/source_snapshots --split dev",
        "script_path": "scripts/build_2wiki_source_snapshot.py",
        "source_url": TWOWIKI_DATA_IDS_APRIL7_URL,
        "license_url": TWOWIKI_LICENSE_URL if not args.skip_license else "not_downloaded",
        "eval_script_url": TWOWIKI_EVAL_SCRIPT_URL if not args.skip_eval_script else "not_downloaded",
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }
    snapshot_record = build_2wiki_snapshot_from_zip(
        zip_path=zip_path,
        output_root=output_root,
        split=args.split,
        source_url=TWOWIKI_DATA_IDS_APRIL7_URL,
        license_path=license_path,
        eval_script_path=eval_script_path,
        command_record=command_record,
    )

    registry_path = Path(args.registry)
    registry = load_registry(registry_path)
    updated_registry = update_2wiki_registry_record(registry, snapshot_record)
    write_json(registry_path, updated_registry)

    print(
        json.dumps(
            {
                "status": "source_ready",
                "dataset_id": "2wikimultihopqa",
                "source_snapshot_id": snapshot_record["source_snapshot_id"],
                "dataset_path": snapshot_record["dataset_path"],
                "raw_data_hash": snapshot_record["raw_data_hash"],
                "processed_corpus_hash": snapshot_record["processed_corpus_hash"],
                "split_hash": snapshot_record["split_hash"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

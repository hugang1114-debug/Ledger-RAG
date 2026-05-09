import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_snapshot.hotpotqa import (
    HOTPOTQA_DEV_DISTRACTOR_URL,
    HOTPOTQA_EVAL_SCRIPT_URL,
    OfficialSourceUnavailable,
    build_hotpotqa_snapshot_from_raw,
    download_official_file,
    update_hotpotqa_registry_record,
)
from ledger_rag_snapshot.registry import load_registry


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build the HotpotQA dev distractor source snapshot.")
    parser.add_argument("--registry", required=True, help="Path to snapshots/main_v1/source_snapshots.json.")
    parser.add_argument("--output-root", required=True, help="Ignored local output root for source snapshot artifacts.")
    parser.add_argument("--split", default="dev_distractor", choices=["dev_distractor"])
    parser.add_argument("--existing-raw", help="Existing official raw HotpotQA JSON path; used by tests and reruns.")
    parser.add_argument("--skip-eval-script", action="store_true", help="Do not download the official eval script.")
    args = parser.parse_args()

    output_root = Path(args.output_root)
    raw_dir = output_root / "hotpotqa" / args.split / "raw"
    raw_path = Path(args.existing_raw) if args.existing_raw else raw_dir / "hotpot_dev_distractor_v1.json"
    eval_script_path = None

    try:
        if not args.existing_raw and not raw_path.exists():
            download_official_file(HOTPOTQA_DEV_DISTRACTOR_URL, raw_path)
        if not args.skip_eval_script:
            eval_script_path = raw_dir / "hotpot_evaluate_v1.py"
            if not eval_script_path.exists():
                download_official_file(HOTPOTQA_EVAL_SCRIPT_URL, eval_script_path)
    except OfficialSourceUnavailable as exc:
        print(json.dumps({"status": "official_source_unavailable", "error": str(exc)}, indent=2, sort_keys=True))
        return 2

    command_record = {
        "command": "python scripts/build_hotpotqa_source_snapshot.py --registry snapshots/main_v1/source_snapshots.json --output-root datasets/source_snapshots --split dev_distractor",
        "script_path": "scripts/build_hotpotqa_source_snapshot.py",
        "source_url": HOTPOTQA_DEV_DISTRACTOR_URL,
        "eval_script_url": HOTPOTQA_EVAL_SCRIPT_URL if not args.skip_eval_script else "not_downloaded",
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }
    snapshot_record = build_hotpotqa_snapshot_from_raw(
        raw_path=raw_path,
        output_root=output_root,
        split=args.split,
        source_url=HOTPOTQA_DEV_DISTRACTOR_URL,
        eval_script_path=eval_script_path,
        command_record=command_record,
    )

    registry_path = Path(args.registry)
    registry = load_registry(registry_path)
    updated_registry = update_hotpotqa_registry_record(registry, snapshot_record)
    write_json(registry_path, updated_registry)

    print(
        json.dumps(
            {
                "status": "source_ready",
                "dataset_id": "hotpotqa",
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

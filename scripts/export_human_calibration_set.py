import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_attribution.calibration_export import export_annotation_items, read_jsonl, write_exports


def main():
    parser = argparse.ArgumentParser(description="Export claim-citation pairs for human semantic support calibration.")
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        metavar="PATH",
        help="Run-record JSONL file. Can be passed multiple times.",
    )
    parser.add_argument(
        "--jsonl-output",
        default="artifacts/calibration/human_claim_citation_calibration.jsonl",
        help="JSONL annotation output path.",
    )
    parser.add_argument(
        "--csv-output",
        default="artifacts/calibration/human_claim_citation_calibration.csv",
        help="CSV annotation output path.",
    )
    parser.add_argument(
        "--include-invalid",
        action="store_true",
        help="Include structurally invalid citation pairs for error analysis.",
    )
    args = parser.parse_args()

    records = []
    for run_path in args.run:
        records.extend(read_jsonl(run_path))
    items = export_annotation_items(records, include_invalid=args.include_invalid)
    write_exports(items, jsonl_path=args.jsonl_output, csv_path=args.csv_output)
    print(f"exported_examples={len(items)}")
    print(f"jsonl_output={args.jsonl_output}")
    print(f"csv_output={args.csv_output}")


if __name__ == "__main__":
    raise SystemExit(main())

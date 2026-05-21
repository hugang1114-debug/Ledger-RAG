import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_attribution.deepseek_labeler import export_manual_audit_subset, read_jsonl, write_labeled_outputs


def main():
    parser = argparse.ArgumentParser(description="Export high-risk machine-judge examples for manual audit.")
    parser.add_argument(
        "--input",
        default="artifacts/calibration/deepseek_judge_labels_v2.jsonl",
        help="Machine judge label JSONL.",
    )
    parser.add_argument(
        "--jsonl-output",
        default="artifacts/calibration/manual_audit_subset_v2.jsonl",
        help="Manual audit subset JSONL.",
    )
    parser.add_argument(
        "--csv-output",
        default="artifacts/calibration/manual_audit_subset_v2.csv",
        help="Manual audit subset CSV.",
    )
    parser.add_argument("--target-size", type=int, default=50, help="Target subset size.")
    args = parser.parse_args()

    subset = export_manual_audit_subset(read_jsonl(args.input), target_size=args.target_size)
    write_labeled_outputs(subset, jsonl_path=args.jsonl_output, csv_path=args.csv_output)
    print(f"exported_examples={len(subset)}")
    print(f"jsonl_output={args.jsonl_output}")
    print(f"csv_output={args.csv_output}")


if __name__ == "__main__":
    main()

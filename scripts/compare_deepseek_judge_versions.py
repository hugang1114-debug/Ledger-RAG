import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_attribution.deepseek_labeler import read_jsonl, summarize_label_comparison, write_comparison_report


def main():
    parser = argparse.ArgumentParser(description="Compare two DeepSeek judge label files.")
    parser.add_argument(
        "--v1",
        default="artifacts/calibration/deepseek_claim_citation_labels.jsonl",
        help="Previous DeepSeek judge JSONL.",
    )
    parser.add_argument(
        "--v2",
        default="artifacts/calibration/deepseek_judge_labels_v2.jsonl",
        help="New DeepSeek judge JSONL.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/calibration/deepseek_judge_v1_vs_v2_comparison.json",
        help="Comparison report JSON.",
    )
    args = parser.parse_args()

    summary = summarize_label_comparison(read_jsonl(args.v1), read_jsonl(args.v2))
    write_comparison_report(summary, args.output)
    print(f"total_compared={summary['total_compared']}")
    print(f"disagreement_count={summary['disagreement_count']}")
    print(f"disagreement_rate={summary['disagreement_rate']:.6f}")
    print(f"changed_from_contradictory={len(summary['changed_from_contradictory'])}")
    print(f"changed_from_entailed={len(summary['changed_from_entailed'])}")
    print(f"output={args.output}")


if __name__ == "__main__":
    main()

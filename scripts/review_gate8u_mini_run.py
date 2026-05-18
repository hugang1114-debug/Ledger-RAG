import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_main.mini_run_review import review_mini_run, write_yaml


def main():
    parser = argparse.ArgumentParser(description="Review Gate 8T mini-run outputs without raw answer leakage.")
    parser.add_argument("--run-dir", required=True, help="Gate 8T mini-run artifact directory.")
    parser.add_argument(
        "--questions",
        default="datasets/source_snapshots/hotpotqa/dev_distractor/processed/questions.jsonl",
        help="Processed HotpotQA questions JSONL.",
    )
    parser.add_argument("--output", required=True, help="Tracked-safe YAML summary output.")
    args = parser.parse_args()

    summary = review_mini_run(args.run_dir, args.questions)
    write_yaml(args.output, summary)
    print(f"gate8u_review={args.output}")
    print(f"recommendation={summary['recommendation']}")
    print(f"support_hit_rate={summary['overall']['support_hit_rate']}")
    print(f"refusal_rate={summary['overall']['refusal_rate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

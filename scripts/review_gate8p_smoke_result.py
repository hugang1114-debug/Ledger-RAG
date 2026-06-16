import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_smoke.result_review import review_smoke_artifacts, write_summary_yaml


def main():
    parser = argparse.ArgumentParser(description="Review Gate 8P DeepSeek smoke artifacts.")
    parser.add_argument("--artifact-dir", required=True, help="Directory containing Gate 8P smoke artifacts.")
    parser.add_argument("--summary", help="Tracked YAML summary path to write when --write-summary is set.")
    parser.add_argument("--budget-ceiling-usd", type=float, default=10.0)
    parser.add_argument("--write-summary", action="store_true")
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    summary = review_smoke_artifacts(args.artifact_dir, budget_ceiling_usd=args.budget_ceiling_usd)
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.write_summary:
        if not args.summary:
            raise SystemExit("--summary is required with --write-summary")
        write_summary_yaml(args.summary, summary)

    if args.require_pass and summary["review_status"] != "passed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

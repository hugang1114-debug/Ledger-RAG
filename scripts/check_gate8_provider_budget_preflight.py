import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_gate8.provider_budget_preflight import (
    build_provider_budget_preflight_summary,
    load_provider_budget_preflight_inputs,
)


def main():
    parser = argparse.ArgumentParser(description="Check Gate 8 provider/budget preflight readiness.")
    parser.add_argument("--provider-candidates", required=True, help="Path to provider_candidates.yaml.")
    parser.add_argument("--budget-preflight", required=True, help="Path to budget_preflight.yaml.")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit nonzero unless execution is authorized as well as preflight-valid.",
    )
    parser.add_argument(
        "--require-smoke-authorized",
        action="store_true",
        help="Exit nonzero unless the DeepSeek smoke run is authorized while main execution stays locked.",
    )
    args = parser.parse_args()

    inputs = load_provider_budget_preflight_inputs(args.provider_candidates, args.budget_preflight)
    summary = build_provider_budget_preflight_summary(inputs)
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.require_ready and not summary["execution_authorized"]:
        return 1
    if args.require_smoke_authorized and not summary["smoke_run_authorized"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

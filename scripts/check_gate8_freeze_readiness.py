import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_gate8.freeze_readiness import build_freeze_readiness_summary, load_freeze_inputs


def main():
    parser = argparse.ArgumentParser(description="Check Gate 8 freeze readiness.")
    parser.add_argument(
        "--freeze-config",
        required=True,
        help="Path to configs/gate8/freeze_readiness.yaml.",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit nonzero if Gate 8 freeze readiness is blocked.",
    )
    args = parser.parse_args()

    inputs = load_freeze_inputs(args.freeze_config)
    summary = build_freeze_readiness_summary(inputs)
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.require_ready and not summary["freeze_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

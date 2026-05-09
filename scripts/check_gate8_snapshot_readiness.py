import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_snapshot.registry import build_readiness_summary, load_registry


def main():
    parser = argparse.ArgumentParser(description="Check Gate 8 source snapshot registry readiness.")
    parser.add_argument("--registry", required=True, help="Path to source_snapshots.json.")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit nonzero if any snapshot is invalid or blocked from Gate 8 execution.",
    )
    args = parser.parse_args()

    registry = load_registry(args.registry)
    summary = build_readiness_summary(registry, args.registry)
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.require_ready and not summary["gate8_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

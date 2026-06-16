import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_gate8.provider_evidence_readiness import (
    build_provider_evidence_readiness_summary,
    load_provider_evidence_inputs,
)


def main():
    parser = argparse.ArgumentParser(description="Check Gate 8 provider evidence readiness.")
    parser.add_argument("--registry", required=True, help="Path to provider_evidence_registry.yaml.")
    parser.add_argument("--provider-decision", help="Optional path to provider_decision.yaml.")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit nonzero if Gate 8 provider evidence readiness is blocked.",
    )
    args = parser.parse_args()

    inputs = load_provider_evidence_inputs(args.registry, args.provider_decision)
    summary = build_provider_evidence_readiness_summary(inputs)
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.require_ready and not summary["provider_evidence_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

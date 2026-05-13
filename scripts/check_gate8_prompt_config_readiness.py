import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_gate8.prompt_config_readiness import (
    build_prompt_config_readiness_summary,
    load_prompt_config_inputs,
)


def main():
    parser = argparse.ArgumentParser(description="Check Gate 8 prompt/config registry readiness.")
    parser.add_argument("--prompt-registry", required=True, help="Path to prompt_registry.yaml.")
    parser.add_argument("--generation-config", required=True, help="Path to generation_config_registry.yaml.")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit nonzero if Gate 8 prompt/config readiness is blocked.",
    )
    args = parser.parse_args()

    inputs = load_prompt_config_inputs(args.prompt_registry, args.generation_config)
    summary = build_prompt_config_readiness_summary(inputs)
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.require_ready and not summary["prompt_config_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

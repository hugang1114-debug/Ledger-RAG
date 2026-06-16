import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_smoke.deepseek_smoke import resolve_deepseek_settings, run_smoke


def main():
    parser = argparse.ArgumentParser(description="Run the Gate 8P one-question DeepSeek smoke call.")
    parser.add_argument("--fixture", required=True, help="Path to fixture JSON.")
    parser.add_argument("--output", required=True, help="Ignored artifact output directory.")
    parser.add_argument("--question-id", default="q_traceability", help="Question id to run.")
    parser.add_argument("--env-file", default=".env.local", help="Local env file containing DEEPSEEK_API_KEY.")
    parser.add_argument("--dry-run", action="store_true", help="Write request.json without calling DeepSeek.")
    args = parser.parse_args()

    api_key, base_url = resolve_deepseek_settings(args.env_file)
    if not args.dry_run and not api_key:
        raise SystemExit("DEEPSEEK_API_KEY is required in the process environment or .env.local")

    output = run_smoke(
        fixture_path=args.fixture,
        output_path=args.output,
        api_key=api_key or "dry-run",
        base_url=base_url,
        question_id=args.question_id,
        dry_run=args.dry_run,
    )
    print(f"wrote_gate8p_deepseek_smoke={output}")


if __name__ == "__main__":
    raise SystemExit(main())

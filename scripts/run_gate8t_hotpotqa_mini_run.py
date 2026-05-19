import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_main.hotpotqa_mini_run import DEFAULT_BASELINES, run_hotpotqa_mini_run
from ledger_rag_smoke.deepseek_smoke import resolve_deepseek_settings


def main():
    parser = argparse.ArgumentParser(description="Run Gate 8T HotpotQA mini main run.")
    parser.add_argument("--repo-root", default=str(ROOT), help="Repository root.")
    parser.add_argument("--sample-count", type=int, default=10, help="Number of deterministic HotpotQA questions to run.")
    parser.add_argument("--baselines", nargs="+", default=list(DEFAULT_BASELINES), help="Baseline families to run.")
    parser.add_argument("--output", required=True, help="Ignored artifact output directory.")
    parser.add_argument("--env-file", default=".env.local", help="Local env file with DEEPSEEK_API_KEY.")
    parser.add_argument("--dry-run", action="store_true", help="Write request/artifact shape without DeepSeek calls.")
    parser.add_argument("--max-provider-attempts", type=int, default=2, help="Maximum attempts for each provider call.")
    parser.add_argument("--resume-from", default=None, help="Existing run artifact directory whose successful run_records should be reused.")
    parser.add_argument("--top-k", type=int, default=None, help="Override retrieval evidence budget.")
    args = parser.parse_args()

    api_key, base_url = resolve_deepseek_settings(args.env_file)
    if not args.dry_run and not api_key:
        raise SystemExit("DEEPSEEK_API_KEY is required in the process environment or .env.local")

    summary = run_hotpotqa_mini_run(
        repo_root=args.repo_root,
        output_path=args.output,
        sample_count=args.sample_count,
        baselines=args.baselines,
        api_key=api_key or "dry-run",
        base_url=base_url,
        dry_run=args.dry_run,
        max_provider_attempts=args.max_provider_attempts,
        resume_from=args.resume_from,
        progress_path=Path(args.output) / "progress.json",
        progress_stream=sys.stdout,
        retrieval_top_k=args.top_k,
    )
    print(f"gate8t_hotpotqa_mini_run={summary['artifact_path']}")
    print(f"success_count={summary['success_count']}")
    print(f"failure_count={summary['failure_count']}")
    print(f"estimated_cost_usd={summary['estimated_cost_usd']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

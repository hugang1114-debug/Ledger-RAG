import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_main.hotpotqa_mini_run import DEFAULT_BASELINES, run_hotpotqa_mini_run
from ledger_rag_smoke.deepseek_smoke import resolve_deepseek_settings


DEFAULT_DATASETS = ("hotpotqa", "2wikimultihopqa", "musique")


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Run a Gate 8 main_v1 batch across selected datasets.")
    parser.add_argument("--repo-root", default=str(ROOT), help="Repository root.")
    parser.add_argument("--datasets", nargs="+", default=list(DEFAULT_DATASETS), help="Dataset ids to run.")
    parser.add_argument("--sample-count", type=int, default=50, help="Deterministic question count per dataset.")
    parser.add_argument("--baselines", nargs="+", default=list(DEFAULT_BASELINES), help="Baseline families to run.")
    parser.add_argument("--output-root", required=True, help="Ignored artifact output root.")
    parser.add_argument("--env-file", default=".env.local", help="Local env file with DEEPSEEK_API_KEY.")
    parser.add_argument("--dry-run", action="store_true", help="Write artifact shape without DeepSeek calls.")
    parser.add_argument("--max-provider-attempts", type=int, default=3, help="Maximum attempts for each provider call.")
    parser.add_argument("--resume-root", default=None, help="Existing batch root whose dataset subdirectories should be reused.")
    args = parser.parse_args()

    api_key, base_url = resolve_deepseek_settings(args.env_file)
    if not args.dry_run and not api_key:
        raise SystemExit("DEEPSEEK_API_KEY is required in the process environment or .env.local")

    output_root = Path(args.output_root)
    summaries = []
    for dataset_id in args.datasets:
        resume_from = Path(args.resume_root) / dataset_id if args.resume_root else None
        summary = run_hotpotqa_mini_run(
            repo_root=args.repo_root,
            output_path=output_root / dataset_id,
            sample_count=args.sample_count,
            baselines=args.baselines,
            api_key=api_key or "dry-run",
            base_url=base_url,
            dry_run=args.dry_run,
            max_provider_attempts=args.max_provider_attempts,
            resume_from=resume_from,
            dataset_id=dataset_id,
            progress_path=output_root / dataset_id / "progress.json",
            progress_stream=sys.stdout,
        )
        summaries.append(summary)

    batch_summary = {
        "stage": "gate8_main_v1_batch",
        "dataset_count": len(summaries),
        "datasets": args.datasets,
        "baselines": args.baselines,
        "sample_count_per_dataset": args.sample_count,
        "dry_run": args.dry_run,
        "max_provider_attempts": args.max_provider_attempts,
        "total_success_count": sum(int(summary["success_count"]) for summary in summaries),
        "total_failure_count": sum(int(summary["failure_count"]) for summary in summaries),
        "total_estimated_cost_usd": round(sum(float(summary["estimated_cost_usd"]) for summary in summaries), 6),
        "dataset_summaries": summaries,
        "not_paper_result": args.dry_run,
    }
    _write_json(output_root / "batch_summary.json", batch_summary)
    print(f"gate8_main_v1_batch={output_root.as_posix()}")
    print(f"dataset_count={batch_summary['dataset_count']}")
    print(f"total_success_count={batch_summary['total_success_count']}")
    print(f"total_failure_count={batch_summary['total_failure_count']}")
    print(f"total_estimated_cost_usd={batch_summary['total_estimated_cost_usd']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

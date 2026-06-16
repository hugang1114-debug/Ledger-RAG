import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_attribution.deepseek_labeler import JUDGE_PROMPT_VERSION
from ledger_rag_attribution.deepseek_v2_audit import (
    aggregate_by_baseline,
    apply_deepseek_v2_semantic_support,
    build_semantic_judge_items,
    read_jsonl,
    typical_failures,
    write_baseline_metrics_csv,
    write_baseline_table,
    write_judge_items,
    write_json,
    write_jsonl,
)
from ledger_rag_main.hotpotqa_mini_run import run_hotpotqa_mini_run
from ledger_rag_smoke.deepseek_smoke import MODEL_ID, resolve_deepseek_settings


DEFAULT_OUTPUT = "artifacts/gate8_migrated/deepseek_v2_small_baseline_comparison"
DEFAULT_BASELINES = ("vanilla_rag", "citation_only", "ledger_only", "ledger_validator")


def main():
    parser = argparse.ArgumentParser(description="Run a small migrated attribution baseline comparison with DeepSeek judge v2.")
    parser.add_argument("--repo-root", default=str(ROOT), help="Repository root.")
    parser.add_argument("--dataset", default="hotpotqa", help="Dataset id. Default: hotpotqa.")
    parser.add_argument("--sample-count", type=int, default=50, help="Question count. Default: 50.")
    parser.add_argument("--question-offset", type=int, default=0, help="Zero-based question offset into the deterministic question list.")
    parser.add_argument("--baselines", nargs="+", default=list(DEFAULT_BASELINES), help="Baseline families.")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT, help="New output directory.")
    parser.add_argument("--env-file", default=".env.local", help="Local env file with DEEPSEEK_API_KEY.")
    parser.add_argument("--max-provider-attempts", type=int, default=2, help="Generation provider attempts.")
    parser.add_argument("--semantic-timeout-seconds", type=int, default=60, help="DeepSeek judge timeout per pair.")
    parser.add_argument("--top-k", type=int, default=None, help="Override retrieval evidence budget.")
    parser.add_argument("--dry-run", action="store_true", help="Write shapes without provider calls.")
    args = parser.parse_args()

    api_key, base_url = resolve_deepseek_settings(args.env_file)
    if not args.dry_run and not api_key:
        raise SystemExit("DEEPSEEK_API_KEY is required unless --dry-run is set.")

    output_root = Path(args.output_root)
    generation_dir = output_root / "generation"
    audit_dir = output_root / "attribution_audit"
    output_root.mkdir(parents=True, exist_ok=True)

    preflight = {
        "stage": "deepseek_v2_small_baseline_comparison_preflight",
        "diagnostic_only": True,
        "dataset": args.dataset,
        "split": "from source snapshot registry",
        "sample_count": args.sample_count,
        "question_offset": args.question_offset,
        "baselines": args.baselines,
        "judge_model": MODEL_ID,
        "judge_prompt_version": JUDGE_PROMPT_VERSION,
        "output_root": output_root.as_posix(),
        "generation_output": generation_dir.as_posix(),
        "audit_output": audit_dir.as_posix(),
        "historical_gate8_outputs_untouched": True,
    }
    write_json(output_root / "preflight.json", preflight)
    print(json.dumps(preflight, ensure_ascii=False, indent=2, sort_keys=True))

    run_summary = run_hotpotqa_mini_run(
        repo_root=args.repo_root,
        output_path=generation_dir,
        sample_count=args.sample_count,
        baselines=args.baselines,
        api_key=api_key or "dry-run",
        base_url=base_url,
        dry_run=args.dry_run,
        max_provider_attempts=args.max_provider_attempts,
        dataset_id=args.dataset,
        progress_path=generation_dir / "progress.json",
        progress_stream=sys.stdout,
        retrieval_top_k=args.top_k,
        question_offset=args.question_offset,
    )

    records = read_jsonl(generation_dir / "run_records.jsonl")
    judge_items = build_semantic_judge_items(records)
    write_judge_items(
        judge_items,
        jsonl_path=audit_dir / "semantic_judge_candidates.jsonl",
        csv_path=audit_dir / "semantic_judge_candidates.csv",
    )
    updated_records = apply_deepseek_v2_semantic_support(
        records,
        api_key=api_key or "dry-run",
        base_url=base_url,
        timeout_seconds=args.semantic_timeout_seconds,
        dry_run=args.dry_run,
    )
    write_jsonl(audit_dir / "run_records_with_deepseek_v2_semantic_support.jsonl", updated_records)

    table = aggregate_by_baseline(updated_records)
    write_json(audit_dir / "baseline_metrics.json", table)
    write_baseline_metrics_csv(table, audit_dir / "baseline_metrics.csv")
    write_baseline_table(table, audit_dir / "baseline_metrics.md")
    failures = typical_failures(updated_records)
    write_json(audit_dir / "typical_failures.json", failures)

    report = {
        "stage": "deepseek_v2_small_baseline_comparison",
        "diagnostic_only": True,
        "not_paper_grade_evidence": True,
        "dataset": args.dataset,
        "sample_count": args.sample_count,
        "question_offset": args.question_offset,
        "baselines": args.baselines,
        "generation_summary": run_summary,
        "run_record_count": len(updated_records),
        "claim_citation_pair_count": sum(len(record.get("citation_validation", [])) for record in updated_records),
        "semantic_judge_pair_count": len(judge_items),
        "judge_model": MODEL_ID,
        "judge_prompt_version": JUDGE_PROMPT_VERSION,
        "baseline_metrics": table,
        "typical_failures": failures,
        "outputs": {
            "preflight": (output_root / "preflight.json").as_posix(),
            "generation_run_records": (generation_dir / "run_records.jsonl").as_posix(),
            "audit_run_records": (audit_dir / "run_records_with_deepseek_v2_semantic_support.jsonl").as_posix(),
            "baseline_metrics_json": (audit_dir / "baseline_metrics.json").as_posix(),
            "baseline_metrics_csv": (audit_dir / "baseline_metrics.csv").as_posix(),
            "baseline_metrics_md": (audit_dir / "baseline_metrics.md").as_posix(),
            "typical_failures": (audit_dir / "typical_failures.json").as_posix(),
        },
    }
    write_json(output_root / "diagnostic_report.json", report)
    print(f"output_root={output_root.as_posix()}")
    print(f"run_record_count={report['run_record_count']}")
    print(f"claim_citation_pair_count={report['claim_citation_pair_count']}")
    print(f"semantic_judge_pair_count={report['semantic_judge_pair_count']}")
    print(f"diagnostic_report={(output_root / 'diagnostic_report.json').as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_attribution.deepseek_labeler import JUDGE_PROMPT_VERSION
from ledger_rag_attribution.deepseek_v2_audit import (
    aggregate_by_baseline,
    read_jsonl,
    typical_failures,
    write_baseline_metrics_csv,
    write_baseline_table,
    write_json,
    write_jsonl,
)
from ledger_rag_smoke.deepseek_smoke import MODEL_ID


DEFAULT_SHARD_A = "artifacts/gate8_migrated/deepseek_v2_small_baseline_comparison"
DEFAULT_SHARD_B = "artifacts/gate8_migrated/deepseek_v2_small_baseline_comparison_shard_26_50"
DEFAULT_OUTPUT = "artifacts/gate8_migrated/deepseek_v2_small_baseline_comparison_merged_1_50"


def _audit_records_path(root):
    return Path(root) / "attribution_audit" / "run_records_with_deepseek_v2_semantic_support.jsonl"


def main():
    parser = argparse.ArgumentParser(description="Merge DeepSeek v2 small baseline comparison shards.")
    parser.add_argument("--shard", action="append", default=[], help="Shard output root. Can be passed multiple times.")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT, help="Merged output root.")
    args = parser.parse_args()

    shard_roots = [Path(item) for item in (args.shard or [DEFAULT_SHARD_A, DEFAULT_SHARD_B])]
    output_root = Path(args.output_root)
    audit_dir = output_root / "attribution_audit"
    records = []
    for shard_root in shard_roots:
        records.extend(read_jsonl(_audit_records_path(shard_root)))

    write_jsonl(audit_dir / "run_records_with_deepseek_v2_semantic_support.jsonl", records)
    table = aggregate_by_baseline(records)
    write_json(audit_dir / "baseline_metrics.json", table)
    write_baseline_metrics_csv(table, audit_dir / "baseline_metrics.csv")
    write_baseline_table(table, audit_dir / "baseline_metrics.md")
    failures = typical_failures(records)
    write_json(audit_dir / "typical_failures.json", failures)
    report = {
        "stage": "deepseek_v2_small_baseline_comparison_merged",
        "diagnostic_only": True,
        "not_paper_grade_evidence": True,
        "dataset": "hotpotqa",
        "sample_count": 50,
        "question_shards": ["1-25", "26-50"],
        "shard_roots": [path.as_posix() for path in shard_roots],
        "run_record_count": len(records),
        "claim_citation_pair_count": sum(len(record.get("citation_validation", [])) for record in records),
        "semantic_judge_pair_count": sum(
            1
            for record in records
            for item in record.get("semantic_support", {}).get("records", [])
            if item.get("status") == "evaluated"
        ),
        "judge_model": MODEL_ID,
        "judge_prompt_version": JUDGE_PROMPT_VERSION,
        "baseline_metrics": table,
        "typical_failures": failures,
        "outputs": {
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


if __name__ == "__main__":
    raise SystemExit(main())

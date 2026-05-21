import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_attribution.deepseek_labeler import JUDGE_PROMPT_VERSION, label_items, read_jsonl, write_labeled_outputs
from ledger_rag_smoke.deepseek_smoke import MODEL_ID, resolve_deepseek_settings


def main():
    parser = argparse.ArgumentParser(
        description="Label claim-citation calibration candidates with the DeepSeek-V4-Pro machine judge."
    )
    parser.add_argument(
        "--input",
        default="artifacts/calibration/claim_citation_calibration_candidates.jsonl",
        help="Input calibration candidates JSONL from export_human_calibration_set.py.",
    )
    parser.add_argument(
        "--jsonl-output",
        default="artifacts/calibration/deepseek_judge_labels_v2.jsonl",
        help="Output JSONL with machine judge fields.",
    )
    parser.add_argument(
        "--csv-output",
        default="artifacts/calibration/llm_judge_semantic_labels_v2.csv",
        help="Output CSV with machine judge fields.",
    )
    parser.add_argument("--env-file", default=".env.local", help="Environment file containing DEEPSEEK_API_KEY.")
    parser.add_argument("--limit", type=int, default=None, help="Optional maximum number of examples to label.")
    parser.add_argument("--timeout-seconds", type=int, default=60, help="DeepSeek HTTP timeout per example.")
    parser.add_argument("--dry-run", action="store_true", help="Write output shape without calling DeepSeek.")
    args = parser.parse_args()

    items = read_jsonl(args.input)
    api_key, base_url = resolve_deepseek_settings(args.env_file)
    if not args.dry_run and not api_key:
        raise SystemExit("DEEPSEEK_API_KEY is required unless --dry-run is set.")

    labeled = label_items(
        items,
        api_key=api_key,
        base_url=base_url,
        limit=args.limit,
        timeout_seconds=args.timeout_seconds,
        dry_run=args.dry_run,
    )
    write_labeled_outputs(labeled, jsonl_path=args.jsonl_output, csv_path=args.csv_output)
    print(f"model={MODEL_ID}")
    print(f"judge_prompt_version={JUDGE_PROMPT_VERSION}")
    print(f"input_examples={len(items)}")
    print(f"labeled_examples={len(labeled)}")
    print(f"jsonl_output={args.jsonl_output}")
    print(f"csv_output={args.csv_output}")
    print("note=DeepSeek labels are machine judge labels, not human gold labels.")


if __name__ == "__main__":
    main()

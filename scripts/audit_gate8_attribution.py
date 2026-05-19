import argparse
import json
from collections import defaultdict
from pathlib import Path


DEFAULT_RUNS = {
    "hotpotqa": "artifacts/gate8/main_v1/runs/deepseek_v4_pro_50x2x3/hotpotqa/run_records.jsonl",
    "2wikimultihopqa": "artifacts/gate8/main_v1/runs/deepseek_v4_pro_50x2x3/2wikimultihopqa/run_records.jsonl",
    "musique": "artifacts/gate8/main_v1/runs/musique_topk16_50x2/musique/run_records.jsonl",
}


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def safe_rate(numerator, denominator):
    return round(numerator / denominator, 6) if denominator else 0.0


def summarize(records):
    claim_count = 0
    citation_count = 0
    cited_claim_count = 0
    invalid_citation_count = 0
    invalid_citation_record_count = 0
    refusal_count = 0

    for record in records:
        claims = {claim["claim_id"] for claim in record.get("answer", {}).get("atomic_claims", [])}
        citations = record.get("citations", [])
        evidence_ids = {evidence["evidence_id"] for evidence in record.get("retrieved_evidence", [])}
        cited_claims = {citation.get("claim_id") for citation in citations if citation.get("claim_id")}
        invalid_citations = [
            citation
            for citation in citations
            if citation.get("cited_evidence_id") not in evidence_ids
        ]

        claim_count += len(claims)
        citation_count += len(citations)
        cited_claim_count += len(claims & cited_claims)
        invalid_citation_count += len(invalid_citations)
        invalid_citation_record_count += bool(invalid_citations)
        refusal_count += record.get("answer", {}).get("refusal_label") != "answered"

    return {
        "record_count": len(records),
        "refusal_rate": safe_rate(refusal_count, len(records)),
        "claim_count": claim_count,
        "citation_count": citation_count,
        "claim_to_citation_rate": safe_rate(citation_count, claim_count),
        "claim_citation_coverage": safe_rate(cited_claim_count, claim_count),
        "invalid_citation_count": invalid_citation_count,
        "invalid_citation_record_count": invalid_citation_record_count,
        "invalid_citation_rate": safe_rate(invalid_citation_count, citation_count),
    }


def write_yaml(path, payload):
    lines = []

    def emit(prefix, value):
        if isinstance(value, dict):
            for key, child in value.items():
                if isinstance(child, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    emit(prefix + "  ", child)
                else:
                    lines.append(f"{prefix}{key}: {child}")
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"{prefix}-")
                    emit(prefix + "  ", item)
                else:
                    lines.append(f"{prefix}- {item}")

    emit("", payload)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_summary(run_paths):
    records = []
    for dataset_id, path in run_paths.items():
        for record in read_jsonl(path):
            record["_dataset_id"] = dataset_id
            records.append(record)

    by_baseline = defaultdict(list)
    by_dataset = defaultdict(list)
    by_dataset_baseline = defaultdict(list)
    for record in records:
        dataset_id = record["_dataset_id"]
        baseline = record["run_metadata"]["baseline_family"]
        by_dataset[dataset_id].append(record)
        by_baseline[baseline].append(record)
        by_dataset_baseline[(dataset_id, baseline)].append(record)

    return {
        "version": 1,
        "stage": "gate8_attribution_audit",
        "source": "corrected_main_v1_50x2x3",
        "overall": summarize(records),
        "by_dataset": {
            dataset_id: summarize(dataset_records)
            for dataset_id, dataset_records in sorted(by_dataset.items())
        },
        "by_baseline": {
            baseline: summarize(baseline_records)
            for baseline, baseline_records in sorted(by_baseline.items())
        },
        "by_dataset_baseline": {
            f"{dataset_id}__{baseline}": summarize(group_records)
            for (dataset_id, baseline), group_records in sorted(by_dataset_baseline.items())
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Audit structural attribution metrics for Gate 8 run records.")
    parser.add_argument(
        "--output",
        default="configs/gate8/main_v1_corrected_attribution_audit.yaml",
        help="YAML summary output path.",
    )
    args = parser.parse_args()

    summary = build_summary(DEFAULT_RUNS)
    write_yaml(args.output, summary)
    print(f"attribution_audit={args.output}")
    print(f"invalid_citation_rate={summary['overall']['invalid_citation_rate']}")
    print(f"claim_citation_coverage={summary['overall']['claim_citation_coverage']}")


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


DEFAULT_RUNS = {
    "hotpotqa__old2": "artifacts/gate8/main_v1/runs/deepseek_v4_pro_50x2x3/hotpotqa/run_records.jsonl",
    "2wikimultihopqa__old2": "artifacts/gate8/main_v1/runs/deepseek_v4_pro_50x2x3/2wikimultihopqa/run_records.jsonl",
    "musique__old2": "artifacts/gate8/main_v1/runs/musique_topk16_50x2/musique/run_records.jsonl",
    "hotpotqa__new4": "artifacts/gate8/main_v1/runs/new4_hotpotqa_2wiki_50x4/hotpotqa/run_records.jsonl",
    "2wikimultihopqa__new4": "artifacts/gate8/main_v1/runs/new4_hotpotqa_2wiki_50x4/2wikimultihopqa/run_records.jsonl",
    "musique__new4": "artifacts/gate8/main_v1/runs/new4_musique_topk16_50x4/musique/run_records.jsonl",
}

STOPWORDS = {
    "about",
    "after",
    "also",
    "before",
    "being",
    "between",
    "could",
    "from",
    "have",
    "into",
    "only",
    "other",
    "that",
    "their",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "under",
    "were",
    "when",
    "where",
    "which",
    "while",
    "with",
    "would",
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


def dataset_id_from_run_key(run_key):
    return run_key.split("__", 1)[0]


def tokens(text):
    return {
        token
        for token in re.findall(r"[a-z0-9]+", str(text).lower())
        if len(token) > 3 and token not in STOPWORDS
    }


def citation_evidence_text(citation, evidence_by_id):
    evidence_id = citation.get("cited_evidence_id")
    evidence = evidence_by_id.get(evidence_id, {})
    return evidence.get("text", "")


def claim_support_score(claim_text, citations, evidence_by_id):
    claim_tokens = tokens(claim_text)
    if not claim_tokens:
        return 0.0
    evidence_tokens = set()
    for citation in citations:
        evidence_tokens |= tokens(citation_evidence_text(citation, evidence_by_id))
    return safe_rate(len(claim_tokens & evidence_tokens), len(claim_tokens))


def summarize(records):
    claim_count = 0
    citation_count = 0
    cited_claim_count = 0
    invalid_citation_count = 0
    invalid_citation_record_count = 0
    refusal_count = 0
    lexically_supported_claim_count = 0
    weakly_supported_claim_count = 0
    uncited_claim_count = 0
    claim_support_scores = []
    answered_claim_count = 0
    dropped_invalid_citation_count = 0

    for record in records:
        claims = {
            claim["claim_id"]: claim
            for claim in record.get("answer", {}).get("atomic_claims", [])
        }
        citations = record.get("citations", [])
        evidence_ids = {evidence["evidence_id"] for evidence in record.get("retrieved_evidence", [])}
        evidence_by_id = {
            evidence["evidence_id"]: evidence
            for evidence in record.get("retrieved_evidence", [])
        }
        citations_by_claim = defaultdict(list)
        for citation in citations:
            citations_by_claim[citation.get("claim_id")].append(citation)
        cited_claims = {citation.get("claim_id") for citation in citations if citation.get("claim_id")}
        invalid_citations = [
            citation
            for citation in citations
            if citation.get("cited_evidence_id") not in evidence_ids
        ]
        diagnostics = record.get("citation_diagnostics", {})
        dropped_invalid_citation_count += int(diagnostics.get("invalid_citation_count") or 0)

        claim_count += len(claims)
        citation_count += len(citations)
        cited_claim_count += len(set(claims) & cited_claims)
        invalid_citation_count += len(invalid_citations)
        invalid_citation_record_count += bool(invalid_citations)
        is_refusal = record.get("answer", {}).get("refusal_label") != "answered"
        refusal_count += is_refusal
        for claim_id, claim in claims.items():
            claim_citations = citations_by_claim.get(claim_id, [])
            if not claim_citations:
                uncited_claim_count += 1
                continue
            score = claim_support_score(claim.get("claim_text", ""), claim_citations, evidence_by_id)
            claim_support_scores.append(score)
            if score >= 0.5:
                lexically_supported_claim_count += 1
            else:
                weakly_supported_claim_count += 1
            if not is_refusal:
                answered_claim_count += 1

    return {
        "record_count": len(records),
        "refusal_rate": safe_rate(refusal_count, len(records)),
        "claim_count": claim_count,
        "citation_count": citation_count,
        "claim_to_citation_rate": safe_rate(citation_count, claim_count),
        "claim_citation_coverage": safe_rate(cited_claim_count, claim_count),
        "post_sanitizer_claim_coverage": safe_rate(cited_claim_count, claim_count),
        "invalid_citation_count": invalid_citation_count,
        "invalid_citation_record_count": invalid_citation_record_count,
        "invalid_citation_rate": safe_rate(invalid_citation_count, citation_count),
        "dropped_invalid_citation_count": dropped_invalid_citation_count,
        "uncited_claim_count": uncited_claim_count,
        "lexically_supported_claim_count": lexically_supported_claim_count,
        "weakly_supported_claim_count": weakly_supported_claim_count,
        "lexical_support_rate": safe_rate(lexically_supported_claim_count, cited_claim_count),
        "weak_support_rate": safe_rate(weakly_supported_claim_count, cited_claim_count),
        "mean_claim_support_score": round(
            sum(claim_support_scores) / len(claim_support_scores), 6
        )
        if claim_support_scores
        else 0.0,
        "answered_claim_count": answered_claim_count,
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
    for run_key, path in run_paths.items():
        dataset_id = dataset_id_from_run_key(run_key)
        for record in read_jsonl(path):
            record["_dataset_id"] = dataset_id
            record["_run_key"] = run_key
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
        "stage": "gate8_claim_to_citation_faithfulness_audit",
        "source": "corrected_main_v1_50x6x3",
        "api_calls_made_by_this_step": 0,
        "audit_method": "lexical_claim_keyword_overlap_with_cited_evidence",
        "lexical_support_threshold": 0.5,
        "methodology_note": "This is a conservative no-API heuristic audit. It can flag weak citations, but it is not a semantic entailment verifier.",
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
        "--run",
        action="append",
        default=[],
        metavar="DATASET_ID=PATH",
        help="Run records JSONL to audit. Can be passed multiple times. Defaults to corrected 50x6x3 artifacts.",
    )
    parser.add_argument(
        "--source-label",
        default="corrected_main_v1_50x6x3",
        help="Source label stored in the YAML summary.",
    )
    parser.add_argument(
        "--output",
        default="configs/gate8/main_v1_corrected_50x6x3_claim_citation_audit.yaml",
        help="YAML summary output path.",
    )
    args = parser.parse_args()

    run_paths = {}
    if args.run:
        for item in args.run:
            if "=" not in item:
                raise SystemExit(f"--run must use DATASET_ID=PATH, got: {item}")
            dataset_id, path = item.split("=", 1)
            run_paths[dataset_id] = path
    else:
        run_paths = DEFAULT_RUNS

    summary = build_summary(run_paths)
    summary["source"] = args.source_label
    write_yaml(args.output, summary)
    print(f"claim_citation_audit={args.output}")
    print(f"invalid_citation_rate={summary['overall']['invalid_citation_rate']}")
    print(f"claim_citation_coverage={summary['overall']['claim_citation_coverage']}")
    print(f"lexical_support_rate={summary['overall']['lexical_support_rate']}")


if __name__ == "__main__":
    raise SystemExit(main())

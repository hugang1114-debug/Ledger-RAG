import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from ledger_rag_pilot.ingest import ingest_fixture, load_fixture
from ledger_rag_pilot.retrieve import retrieve


MODEL_ID = "deepseek-v4-pro"
INPUT_USD_PER_1M_TOKENS = 0.435
OUTPUT_USD_PER_1M_TOKENS = 0.87


def load_env_file(path):
    values = {}
    path = Path(path)
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def resolve_deepseek_settings(env_path=".env.local"):
    env_values = load_env_file(env_path)
    api_key = os.environ.get("DEEPSEEK_API_KEY") or env_values.get("DEEPSEEK_API_KEY")
    base_url = os.environ.get("DEEPSEEK_BASE_URL") or env_values.get("DEEPSEEK_BASE_URL") or "https://api.deepseek.com"
    return api_key, base_url.rstrip("/")


def build_chat_request(question_text, evidence, model_id=MODEL_ID):
    evidence_lines = []
    for item in evidence:
        evidence_lines.append(
            f"- evidence_id={item['evidence_id']} source_doc_id={item['source_doc_id']} text={item['text']}"
        )
    user_content = (
        "Question:\n"
        f"{question_text}\n\n"
        "Evidence spans:\n"
        + "\n".join(evidence_lines)
        + "\n\nReturn only JSON with keys: global_answer, atomic_claims, citations. "
        "Each atomic claim must have claim_id and claim_text. Each citation must have claim_id and cited_evidence_id."
    )
    return {
        "model": model_id,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are running a Ledger-RAG smoke test. Answer only from the provided evidence. "
                    "If the evidence is insufficient, set global_answer to INSUFFICIENT_EVIDENCE and use empty atomic_claims and citations."
                ),
            },
            {"role": "user", "content": user_content},
        ],
        "temperature": 0,
        "max_tokens": 300,
        "stream": False,
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
    }


def post_chat_completion(base_url, api_key, request_payload, timeout_seconds=60):
    body = json.dumps(request_payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API HTTP {exc.code}: {error_body}") from exc


def _strip_markdown_fence(text):
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def extract_json_answer(content):
    return json.loads(_strip_markdown_fence(content))


def response_content(response_payload):
    choices = response_payload.get("choices") or []
    if not choices:
        raise ValueError("DeepSeek response has no choices")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not content:
        raise ValueError("DeepSeek response choice has no message content")
    return content


def estimate_cost_usd(usage):
    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    cost = (prompt_tokens / 1_000_000 * INPUT_USD_PER_1M_TOKENS) + (
        completion_tokens / 1_000_000 * OUTPUT_USD_PER_1M_TOKENS
    )
    return round(cost, 6)


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_claims(answer_payload):
    claims = []
    for index, claim in enumerate(answer_payload.get("atomic_claims", []), start=1):
        claims.append(
            {
                "claim_id": str(claim.get("claim_id") or f"c{index}"),
                "claim_text": str(claim.get("claim_text") or ""),
                "answer_order": index,
                "confidence": None,
            }
        )
    return claims


def _normalize_citations(answer_payload, evidence):
    evidence_by_id = {item["evidence_id"]: item for item in evidence}
    citations = []
    for citation in answer_payload.get("citations", []):
        evidence_id = str(citation.get("cited_evidence_id") or "")
        evidence_item = evidence_by_id.get(evidence_id, {})
        citations.append(
            {
                "claim_id": str(citation.get("claim_id") or ""),
                "cited_evidence_id": evidence_id,
                "cited_ledger_span_id": evidence_item.get("ledger_span_id"),
                "citation_role": "primary",
                "citation_source": "model_output",
                "source_doc_id": evidence_item.get("source_doc_id"),
            }
        )
    return citations


def _build_verdicts(claims, citations):
    cited_claim_ids = {citation["claim_id"] for citation in citations}
    verdicts = []
    for claim in claims:
        label = "not_checked" if claim["claim_id"] in cited_claim_ids else "insufficient"
        verdicts.append(
            {
                "claim_id": claim["claim_id"],
                "verifier_enabled": False,
                "label": label,
                "score": None,
                "verifier_name": None,
                "rationale": "Gate 8P smoke run records provider output shape only; semantic verification is not executed.",
            }
        )
    return verdicts


def build_run_record(
    dataset_id,
    split,
    question_id,
    question_text,
    corpus_snapshot_id,
    evidence,
    answer_payload,
    verdicts,
    run_metadata,
):
    claims = _normalize_claims(answer_payload)
    citations = _normalize_citations(answer_payload, evidence)
    refusal_label = "insufficient_evidence" if answer_payload.get("global_answer") == "INSUFFICIENT_EVIDENCE" else "answered"
    return {
        "input": {
            "dataset_id": dataset_id,
            "split": split,
            "question_id": question_id,
            "question_text": question_text,
            "corpus_snapshot_id": corpus_snapshot_id,
            "retrieval_config": {
                "retriever_family": "offline_lexical",
                "top_k": len(evidence),
                "reranker": "none",
                "evidence_budget": f"{len(evidence)} fixture spans",
            },
            "generation_config": {
                "model_id": MODEL_ID,
                "prompt_version": "gate8p_deepseek_smoke_v1",
                "answer_style": "json_claims_with_citations",
                "max_output_tokens": 300,
                "temperature": 0,
            },
        },
        "retrieved_evidence": evidence,
        "answer": {
            "global_answer": str(answer_payload.get("global_answer") or ""),
            "refusal_label": refusal_label,
            "atomic_claims": claims,
        },
        "citations": citations,
        "verdicts": verdicts if verdicts else _build_verdicts(claims, citations),
        "run_metadata": run_metadata,
    }


def build_metric_record(run_record):
    claims = run_record["answer"]["atomic_claims"]
    citations = run_record["citations"]
    verdicts = run_record["verdicts"]
    supported = sum(1 for verdict in verdicts if verdict["label"] in {"support", "not_checked"})
    unsupported = sum(1 for verdict in verdicts if verdict["label"] in {"refute", "insufficient"})
    run_metadata = run_record["run_metadata"]
    return {
        "metric_record": {
            "run_id": run_metadata["run_id"],
            "dataset_id": run_record["input"]["dataset_id"],
            "baseline_family": run_metadata["baseline_family"],
            "split": run_record["input"]["split"],
            "question_count": 1,
            "refusal_count": 1 if run_record["answer"]["refusal_label"] != "answered" else 0,
            "refusal_rate": 1.0 if run_record["answer"]["refusal_label"] != "answered" else 0.0,
        },
        "retrieval": {
            "recall_at_k": "not_available",
            "precision_at_k": "not_available",
            "mrr": "not_available",
            "ndcg": "not_available",
            "k": len(run_record["retrieved_evidence"]),
            "oracle_retrieval": False,
            "missing_reason": "Gate 8P smoke run does not score retrieval quality.",
        },
        "answer_quality": {
            "exact_match": "not_applicable",
            "f1": "not_applicable",
            "rouge_l": "not_applicable",
            "claim_level_correctness": "not_available",
            "factscore": "not_available",
            "missing_reason": "Gate 8P smoke run validates provider output shape only.",
        },
        "attribution": {
            "citation_precision": "not_applicable",
            "citation_recall": "not_applicable",
            "support_rate": supported / max(len(verdicts), 1),
            "unsupported_claim_rate": unsupported / max(len(verdicts), 1),
            "overclaim_rate": "not_available",
            "claim_to_span_mapping_completeness": len(citations) / max(len(claims), 1),
            "span_replay_success": 1.0 if citations else "not_applicable",
            "verifier_name": None,
            "missing_reason": "Semantic verifier is disabled in smoke run.",
        },
        "system": {
            "p50_latency_ms": run_metadata["latency_ms"],
            "p95_latency_ms": run_metadata["latency_ms"],
            "cost_per_query_usd": run_metadata["estimated_cost_usd"],
            "peak_memory_mb": "not_available",
            "index_size_mb": "not_applicable",
            "ledger_size_mb": "not_applicable",
            "missing_reason": None,
        },
        "aggregation": {
            "aggregation_level": "question",
            "macro_average": False,
            "confidence_interval_method": "none",
            "includes_refusals_in_denominator": True,
            "notes": "Gate 8P one-question DeepSeek smoke run; not a paper result.",
        },
    }


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _find_question(fixture, question_id):
    for question in fixture["questions"]:
        if question["question_id"] == question_id:
            return question
    raise ValueError(f"question_id not found in fixture: {question_id}")


def run_smoke(
    fixture_path,
    output_path,
    api_key,
    base_url,
    question_id,
    transport=post_chat_completion,
    dry_run=False,
):
    fixture = load_fixture(fixture_path)
    ledger = ingest_fixture(fixture)
    question = _find_question(fixture, question_id)
    evidence = retrieve(question["question_text"], ledger["spans"], top_k=2)
    request_payload = build_chat_request(question["question_text"], evidence)

    output = Path(output_path)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "request.json", request_payload)

    if dry_run:
        return output

    started_at = _utc_now()
    started = time.perf_counter()
    response_payload = transport(base_url, api_key, request_payload, 60)
    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    completed_at = _utc_now()
    answer_payload = extract_json_answer(response_content(response_payload))
    estimated_cost = estimate_cost_usd(response_payload.get("usage", {}))

    run_id = f"gate8p_deepseek_smoke_{question_id}"
    run_metadata = {
        "baseline_family": "ledger_validator",
        "run_id": run_id,
        "code_version": "working_tree",
        "config_version": "gate8p_deepseek_smoke_v1",
        "seed": 0,
        "started_at": started_at,
        "completed_at": completed_at,
        "latency_ms": latency_ms,
        "estimated_cost_usd": estimated_cost,
        "hardware": "local_cpu_remote_deepseek_api",
        "notes": "one-question DeepSeek smoke run; not a paper result",
    }
    run_record = build_run_record(
        dataset_id=fixture["dataset_id"],
        split=fixture["split"],
        question_id=question["question_id"],
        question_text=question["question_text"],
        corpus_snapshot_id=fixture["corpus_snapshot_id"],
        evidence=evidence,
        answer_payload=answer_payload,
        verdicts=[],
        run_metadata=run_metadata,
    )
    metric_record = build_metric_record(run_record)
    cost_estimate = {
        "provider": "deepseek",
        "model": MODEL_ID,
        "pricing_source": "https://api-docs.deepseek.com/quick_start/pricing",
        "input_usd_per_1m_tokens": INPUT_USD_PER_1M_TOKENS,
        "output_usd_per_1m_tokens": OUTPUT_USD_PER_1M_TOKENS,
        "usage": response_payload.get("usage", {}),
        "estimated_cost_usd": estimated_cost,
        "notes": "Estimated from response usage and Gate 8O checked prices; recheck official pricing before future runs.",
    }

    write_json(output / "response.json", response_payload)
    write_json(output / "run_record.json", run_record)
    write_json(output / "metric_record.json", metric_record)
    write_json(output / "cost_estimate.json", cost_estimate)
    return output

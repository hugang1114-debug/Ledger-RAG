import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from ledger_rag_retrieval.lexical_index import tokenize
from ledger_rag_smoke.deepseek_smoke import (
    INPUT_USD_PER_1M_TOKENS,
    MODEL_ID,
    OUTPUT_USD_PER_1M_TOKENS,
    estimate_cost_usd,
    extract_json_answer,
    post_chat_completion,
    response_content,
)


DEFAULT_REGISTRY = Path("snapshots/main_v1/source_snapshots.json")
DEFAULT_SAMPLE_COUNT = 10
DEFAULT_BASELINES = ("vanilla_rag", "ledger_validator")
DEFAULT_TOP_K = 8
DEFAULT_MAX_OUTPUT_TOKENS = 2048
DEFAULT_PROVIDER_ATTEMPTS = 2
PRICING_SOURCE = "https://api-docs.deepseek.com/quick_start/pricing"


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_dumps(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _write_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("".join(_json_dumps(row) + "\n" for row in rows), encoding="utf-8")


def _write_yaml(path, payload):
    lines = []
    for key, value in payload.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _emit_progress(progress_path, progress_stream, progress):
    if progress_path:
        _write_json(progress_path, progress)
    if progress_stream:
        line = (
            f"[{progress['dataset_id']}] {progress['question_index']}/{progress['question_count']} q "
            f"| baseline={progress['baseline_family']} "
            f"| ok={progress['success_count']} fail={progress['failure_count']} skipped={progress['skipped_count']} "
            f"| cost=${progress['estimated_cost_usd']:.6f} | status={progress['status']}"
        )
        progress_stream.write(line + "\n")
        progress_stream.flush()


def _read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def load_questions(path, sample_count):
    rows = _read_jsonl(path)
    return rows[: int(sample_count)]


def _resolve_repo_path(repo_root, value):
    path = Path(value)
    if path.is_absolute():
        return path
    return Path(repo_root) / path


def _load_snapshot_record(repo_root, dataset_id, registry_path=DEFAULT_REGISTRY):
    registry = json.loads(_resolve_repo_path(repo_root, registry_path).read_text(encoding="utf-8"))
    for record in registry.get("snapshots", []):
        if record.get("dataset_id") == dataset_id:
            return record
    raise ValueError(f"{dataset_id} snapshot record not found")


def _load_hotpotqa_record(repo_root, registry_path=DEFAULT_REGISTRY):
    return _load_snapshot_record(repo_root, "hotpotqa", registry_path=registry_path)


def _load_prompt_versions(repo_root):
    prompt_registry = _resolve_repo_path(repo_root, "configs/gate8/prompt_registry.yaml")
    versions = {}
    current = None
    if not prompt_registry.is_file():
        return versions
    for raw_line in prompt_registry.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("- baseline_family:"):
            current = stripped.split(":", 1)[1].strip()
            versions[current] = "unset"
        elif current and stripped.startswith("prompt_version:"):
            versions[current] = stripped.split(":", 1)[1].strip()
    return versions


def _load_generation_constraints(repo_root):
    generation_registry = _resolve_repo_path(repo_root, "configs/gate8/generation_config_registry.yaml")
    defaults = {"max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS, "temperature": 0, "max_evidence_items": DEFAULT_TOP_K}
    if not generation_registry.is_file():
        return defaults
    in_constraints = False
    for raw_line in generation_registry.read_text(encoding="utf-8").splitlines():
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()
        if stripped == "shared_constraints:":
            in_constraints = True
            continue
        if in_constraints and indent == 0:
            break
        if in_constraints and ":" in stripped:
            key, value = stripped.split(":", 1)
            value = value.strip()
            if value.isdigit():
                defaults[key.strip()] = int(value)
            else:
                defaults[key.strip()] = value
    return defaults


def _load_index(index_manifest_path):
    manifest = json.loads(Path(index_manifest_path).read_text(encoding="utf-8"))
    documents = _read_jsonl(manifest["paths"]["documents"])
    postings = _read_jsonl(manifest["paths"]["postings"])
    postings_by_token = {row["token"]: row["postings"] for row in postings}
    document_by_internal_id = {int(row["internal_doc_id"]): row for row in documents}
    return manifest, document_by_internal_id, postings_by_token


def _load_corpus(corpus_path):
    return {row["source_doc_id"]: row for row in _read_jsonl(corpus_path)}


def rank_evidence(question_text, index_manifest_path, corpus_path, top_k=DEFAULT_TOP_K, allowed_source_doc_ids=None):
    manifest, document_by_internal_id, postings_by_token = _load_index(index_manifest_path)
    corpus_by_source_doc_id = _load_corpus(corpus_path)
    allowed_source_doc_ids = set(allowed_source_doc_ids or [])
    scores = defaultdict(float)
    for token in tokenize(question_text):
        for posting in postings_by_token.get(token, []):
            internal_doc_id = int(posting["internal_doc_id"])
            source_doc_id = document_by_internal_id[internal_doc_id]["source_doc_id"]
            if allowed_source_doc_ids and source_doc_id not in allowed_source_doc_ids:
                continue
            scores[internal_doc_id] += float(posting.get("term_frequency", 0))

    ranked_ids = sorted(scores, key=lambda doc_id: (-scores[doc_id], str(document_by_internal_id[doc_id]["source_doc_id"])))
    if allowed_source_doc_ids:
        scored_source_doc_ids = {document_by_internal_id[doc_id]["source_doc_id"] for doc_id in ranked_ids}
        for internal_doc_id, document in document_by_internal_id.items():
            source_doc_id = document["source_doc_id"]
            if source_doc_id in allowed_source_doc_ids and source_doc_id not in scored_source_doc_ids:
                ranked_ids.append(internal_doc_id)
    evidence = []
    for rank, internal_doc_id in enumerate(ranked_ids[: int(top_k)], start=1):
        document = document_by_internal_id[internal_doc_id]
        corpus_row = corpus_by_source_doc_id[document["source_doc_id"]]
        evidence.append(
            {
                "rank": rank,
                "score": scores[internal_doc_id],
                "evidence_id": corpus_row["source_doc_id"],
                "ledger_span_id": corpus_row["source_doc_id"],
                "source_doc_id": corpus_row["source_doc_id"],
                "source_uri": corpus_row.get("source_uri", ""),
                "title": corpus_row.get("title", ""),
                "text": corpus_row.get("text", ""),
                "source_hash": corpus_row.get("source_hash"),
                "retriever_family": manifest.get("retriever_family", "lexical"),
            }
        )
    return evidence


def build_chat_request(baseline_family, question_text, evidence, prompt_version, max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS):
    evidence_lines = []
    for item in evidence:
        evidence_lines.append(
            " ".join(
                [
                    f"evidence_id={item['evidence_id']}",
                    f"ledger_span_id={item['ledger_span_id']}",
                    f"title={item.get('title', '')}",
                    f"text={item.get('text', '')}",
                ]
            )
        )
    if baseline_family == "ledger_validator":
        baseline_policy = (
            "This is the ledger_validator baseline. Cite evidence ids as ledger span ids. "
            "Every factual atomic claim should include citations to provided evidence."
        )
    elif baseline_family == "vanilla_rag":
        baseline_policy = (
            "This is the vanilla_rag baseline. Answer from provided evidence only. "
            "Citations are optional but should be included when clear."
        )
    else:
        raise ValueError(f"unsupported baseline_family: {baseline_family}")

    return {
        "model": MODEL_ID,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"Gate 8T HotpotQA mini run. baseline_family={baseline_family}. "
                    f"prompt_version={prompt_version}. {baseline_policy} "
                    "Return only JSON with keys: global_answer, atomic_claims, citations, refusal, refusal_reason. "
                    "atomic_claims entries must include claim_id and text. citations entries must include claim_id and cited_evidence_id. "
                    "If evidence is insufficient, set refusal true."
                ),
            },
            {
                "role": "user",
                "content": "Question:\n"
                + question_text
                + "\n\nEvidence:\n"
                + "\n".join(f"- {line}" for line in evidence_lines),
            },
        ],
        "temperature": 0,
        "max_tokens": int(max_output_tokens),
        "stream": False,
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
    }


def _normalize_claims(answer_payload):
    claims = []
    for index, claim in enumerate(answer_payload.get("atomic_claims") or [], start=1):
        claims.append(
            {
                "claim_id": str(claim.get("claim_id") or f"c{index}"),
                "claim_text": str(claim.get("text") or claim.get("claim_text") or ""),
                "answer_order": index,
            }
        )
    return claims


def _normalize_citations(answer_payload, evidence):
    evidence_ids = {item["evidence_id"]: item for item in evidence}
    citations = []
    for citation in answer_payload.get("citations") or []:
        cited_id = str(citation.get("cited_evidence_id") or citation.get("evidence_id") or "")
        evidence_item = evidence_ids.get(cited_id, {})
        citations.append(
            {
                "claim_id": str(citation.get("claim_id") or ""),
                "cited_evidence_id": cited_id,
                "cited_ledger_span_id": evidence_item.get("ledger_span_id"),
                "source_doc_id": evidence_item.get("source_doc_id"),
                "citation_source": "model_output",
            }
        )
    return citations


def _build_run_record(run_id, baseline_family, question, evidence, answer_payload, usage, latency_ms, prompt_version, source_snapshot_id, dataset_id, split):
    claims = _normalize_claims(answer_payload)
    citations = _normalize_citations(answer_payload, evidence)
    return {
        "input": {
            "dataset_id": dataset_id,
            "split": split,
            "question_id": question["question_id"],
            "question_text": question["question_text"],
            "corpus_snapshot_id": source_snapshot_id,
            "retrieval_config": {"retriever_family": "lexical", "top_k": len(evidence), "reranker": "none"},
            "generation_config": {
                "model_id": MODEL_ID,
                "prompt_version": prompt_version,
                "temperature": 0,
                "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
            },
        },
        "retrieved_evidence": evidence,
        "answer": {
            "global_answer": str(answer_payload.get("global_answer") or ""),
            "refusal_label": "insufficient_evidence" if answer_payload.get("refusal") is True else "answered",
            "atomic_claims": claims,
            "reference_answer": question.get("answer"),
        },
        "citations": citations,
        "verdicts": [
            {
                "claim_id": claim["claim_id"],
                "verifier_enabled": baseline_family == "ledger_validator",
                "label": "not_checked" if citations else "insufficient",
                "score": None,
                "rationale": "Gate 8T mini run uses provider output shape checks; semantic verifier is not yet a paper-grade verifier.",
            }
            for claim in claims
        ],
        "run_metadata": {
            "run_id": run_id,
            "baseline_family": baseline_family,
            "model": MODEL_ID,
            "usage": usage,
            "latency_ms": latency_ms,
            "estimated_cost_usd": estimate_cost_usd(usage),
            "code_version": "working_tree",
            "config_version": "gate8s_main_prompt_config_freeze",
        },
    }


def _build_metric_record(run_record):
    claims = run_record["answer"]["atomic_claims"]
    citations = run_record["citations"]
    cited_claim_ids = {citation["claim_id"] for citation in citations}
    return {
        "metric_record": {
            "run_id": run_record["run_metadata"]["run_id"],
            "dataset_id": run_record["input"]["dataset_id"],
            "baseline_family": run_record["run_metadata"]["baseline_family"],
            "question_count": 1,
            "refusal_count": 1 if run_record["answer"]["refusal_label"] != "answered" else 0,
        },
        "retrieval": {"k": len(run_record["retrieved_evidence"]), "retriever_family": "lexical"},
        "answer_quality": {"reference_answer": run_record["answer"]["reference_answer"], "exact_match": "not_scored"},
        "attribution": {
            "claim_to_span_mapping_completeness": len(cited_claim_ids) / max(len(claims), 1),
            "citation_count": len(citations),
        },
        "system": {
            "latency_ms": run_record["run_metadata"]["latency_ms"],
            "cost_per_query_usd": run_record["run_metadata"]["estimated_cost_usd"],
        },
        "aggregation": {"aggregation_level": "question", "notes": "Gate 8T mini run; not a paper result."},
    }


def _dry_answer(evidence):
    if not evidence:
        return {"global_answer": "INSUFFICIENT_EVIDENCE", "atomic_claims": [], "citations": [], "refusal": True, "refusal_reason": "no evidence"}
    first = evidence[0]
    return {
        "global_answer": "DRY_RUN_NO_MODEL_CALL",
        "atomic_claims": [{"claim_id": "c1", "text": "Dry run request shape was generated."}],
        "citations": [{"claim_id": "c1", "cited_evidence_id": first["evidence_id"]}],
        "refusal": False,
        "refusal_reason": "",
    }


def _call_with_retry(base_url, api_key, request_payload, transport, max_attempts=DEFAULT_PROVIDER_ATTEMPTS):
    last_error = None
    for attempt in range(1, int(max_attempts) + 1):
        try:
            return transport(base_url, api_key, request_payload, 90), attempt
        except Exception as exc:  # pragma: no cover - exercised through integration failures.
            last_error = exc
            time.sleep(1)
    raise last_error


def _load_resume_records(resume_from):
    if not resume_from:
        return [], []
    resume_path = Path(resume_from)
    run_records_path = resume_path / "run_records.jsonl"
    metric_records_path = resume_path / "metric_records.jsonl"
    run_records = _read_jsonl(run_records_path) if run_records_path.is_file() else []
    metric_records = _read_jsonl(metric_records_path) if metric_records_path.is_file() else []
    return run_records, metric_records


def _sum_usage_tokens(run_records, token_name):
    total = 0
    for record in run_records:
        usage = record.get("run_metadata", {}).get("usage", {})
        total += int(usage.get(token_name) or 0)
    return total


def run_hotpotqa_mini_run(
    repo_root,
    output_path,
    sample_count=DEFAULT_SAMPLE_COUNT,
    baselines=DEFAULT_BASELINES,
    api_key=None,
    base_url="https://api.deepseek.com",
    transport=post_chat_completion,
    dry_run=False,
    max_provider_attempts=DEFAULT_PROVIDER_ATTEMPTS,
    resume_from=None,
    dataset_id="hotpotqa",
    progress_path=None,
    progress_stream=None,
):
    repo_root = Path(repo_root)
    output = Path(output_path)
    output.mkdir(parents=True, exist_ok=True)
    snapshot = _load_snapshot_record(repo_root, dataset_id)
    dataset_path = _resolve_repo_path(repo_root, snapshot["dataset_path"])
    questions_path = dataset_path / "processed" / "questions.jsonl"
    corpus_path = dataset_path / "processed" / "corpus.jsonl"
    index_manifest_path = _resolve_repo_path(repo_root, snapshot["retrieval_index_path"])
    if not questions_path.is_file() or not corpus_path.is_file() or not index_manifest_path.is_file():
        raise FileNotFoundError("HotpotQA snapshot or lexical index is missing")

    prompt_versions = _load_prompt_versions(repo_root)
    generation_constraints = _load_generation_constraints(repo_root)
    max_output_tokens = int(generation_constraints.get("max_output_tokens", DEFAULT_MAX_OUTPUT_TOKENS))
    top_k = int(generation_constraints.get("max_evidence_items", DEFAULT_TOP_K))
    questions = load_questions(questions_path, sample_count)
    split = snapshot["split"]
    run_id = f"gate8_main_v1_{dataset_id}_run"
    started_at = _utc_now()
    baselines = list(baselines)
    attempted_call_count = len(questions) * len(baselines)

    resumed_run_records, resumed_metric_records = _load_resume_records(resume_from)
    completed_run_ids = {record.get("run_metadata", {}).get("run_id") for record in resumed_run_records}
    run_records = list(resumed_run_records)
    metric_records = list(resumed_metric_records)
    retrieval_records = []
    request_manifest = []
    raw_responses = []
    failures = []
    total_prompt_tokens = _sum_usage_tokens(resumed_run_records, "prompt_tokens")
    total_completion_tokens = _sum_usage_tokens(resumed_run_records, "completion_tokens")

    json_parse_failures = 0
    provider_failures = 0
    skipped_count = 0
    for question_index, question in enumerate(questions, start=1):
        evidence = rank_evidence(
            question["question_text"],
            index_manifest_path,
            corpus_path,
            top_k=top_k,
            allowed_source_doc_ids=question.get("context_source_doc_ids") or [],
        )
        retrieval_records.append({"question_id": question["question_id"], "evidence": evidence})
        for baseline in baselines:
            per_run_id = f"{run_id}_{baseline}_{question['question_id']}"
            if per_run_id in completed_run_ids:
                skipped_count += 1
                request_manifest.append(
                    {
                        "run_id": per_run_id,
                        "baseline_family": baseline,
                        "question_id": question["question_id"],
                        "model": MODEL_ID,
                        "prompt_version": prompt_versions.get(baseline, "unset"),
                        "request_sha256_length": 0,
                        "provider_attempt_count": 0,
                        "resume_status": "skipped_existing_success",
                    }
                )
                _emit_progress(
                    progress_path,
                    progress_stream,
                    {
                        "dataset_id": dataset_id,
                        "split": split,
                        "question_index": question_index,
                        "question_count": len(questions),
                        "baseline_family": baseline,
                        "attempted_call_count": attempted_call_count,
                        "success_count": len(run_records),
                        "failure_count": len(failures),
                        "skipped_count": skipped_count,
                        "estimated_cost_usd": round(
                            (total_prompt_tokens / 1_000_000 * INPUT_USD_PER_1M_TOKENS)
                            + (total_completion_tokens / 1_000_000 * OUTPUT_USD_PER_1M_TOKENS),
                            6,
                        ),
                        "status": "skipped_existing_success",
                    },
                )
                continue
            request_payload = build_chat_request(
                baseline_family=baseline,
                question_text=question["question_text"],
                evidence=evidence,
                prompt_version=prompt_versions.get(baseline, "unset"),
                max_output_tokens=max_output_tokens,
            )
            request_manifest.append(
                {
                    "run_id": per_run_id,
                    "baseline_family": baseline,
                    "question_id": question["question_id"],
                    "model": MODEL_ID,
                    "prompt_version": prompt_versions.get(baseline, "unset"),
                    "request_sha256_length": len(_json_dumps(request_payload)),
                    "provider_attempt_count": 0,
                    "resume_status": "new_request",
                }
            )
            request_manifest_index = len(request_manifest) - 1
            started = time.perf_counter()
            try:
                if dry_run:
                    response_payload = {"choices": [{"message": {"content": json.dumps(_dry_answer(evidence))}}], "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
                    provider_attempt_count = 0
                else:
                    response_payload, provider_attempt_count = _call_with_retry(
                        base_url,
                        api_key,
                        request_payload,
                        transport,
                        max_attempts=max_provider_attempts,
                    )
                request_manifest[request_manifest_index]["provider_attempt_count"] = provider_attempt_count
                latency_ms = round((time.perf_counter() - started) * 1000, 3)
            except Exception as exc:
                provider_failures += 1
                failures.append({"run_id": per_run_id, "error_type": "provider_error", "message": str(exc)})
                _emit_progress(
                    progress_path,
                    progress_stream,
                    {
                        "dataset_id": dataset_id,
                        "split": split,
                        "question_index": question_index,
                        "question_count": len(questions),
                        "baseline_family": baseline,
                        "attempted_call_count": attempted_call_count,
                        "success_count": len(run_records),
                        "failure_count": len(failures),
                        "skipped_count": skipped_count,
                        "estimated_cost_usd": round(
                            (total_prompt_tokens / 1_000_000 * INPUT_USD_PER_1M_TOKENS)
                            + (total_completion_tokens / 1_000_000 * OUTPUT_USD_PER_1M_TOKENS),
                            6,
                        ),
                        "status": "provider_error",
                    },
                )
                if provider_failures > 2:
                    raise RuntimeError("stopping Gate 8T mini run after repeated provider errors") from exc
                continue
            try:
                answer_payload = extract_json_answer(response_content(response_payload))
            except Exception as exc:
                json_parse_failures += 1
                failures.append({"run_id": per_run_id, "error_type": "json_parse_error", "message": str(exc)})
                _emit_progress(
                    progress_path,
                    progress_stream,
                    {
                        "dataset_id": dataset_id,
                        "split": split,
                        "question_index": question_index,
                        "question_count": len(questions),
                        "baseline_family": baseline,
                        "attempted_call_count": attempted_call_count,
                        "success_count": len(run_records),
                        "failure_count": len(failures),
                        "skipped_count": skipped_count,
                        "estimated_cost_usd": round(
                            (total_prompt_tokens / 1_000_000 * INPUT_USD_PER_1M_TOKENS)
                            + (total_completion_tokens / 1_000_000 * OUTPUT_USD_PER_1M_TOKENS),
                            6,
                        ),
                        "status": "json_parse_error",
                    },
                )
                if json_parse_failures > 2:
                    raise RuntimeError("stopping Gate 8T mini run after repeated JSON parse failures") from exc
                continue
            usage = response_payload.get("usage", {})
            total_prompt_tokens += int(usage.get("prompt_tokens") or 0)
            total_completion_tokens += int(usage.get("completion_tokens") or 0)
            raw_responses.append({"run_id": per_run_id, "response": response_payload})
            run_record = _build_run_record(
                per_run_id,
                baseline,
                question,
                evidence,
                answer_payload,
                usage,
                latency_ms,
                prompt_versions.get(baseline, "unset"),
                snapshot["source_snapshot_id"],
                dataset_id,
                split,
            )
            run_records.append(run_record)
            metric_records.append(_build_metric_record(run_record))
            _emit_progress(
                progress_path,
                progress_stream,
                {
                    "dataset_id": dataset_id,
                    "split": split,
                    "question_index": question_index,
                    "question_count": len(questions),
                    "baseline_family": baseline,
                    "attempted_call_count": attempted_call_count,
                    "success_count": len(run_records),
                    "failure_count": len(failures),
                    "skipped_count": skipped_count,
                    "estimated_cost_usd": round(
                        (total_prompt_tokens / 1_000_000 * INPUT_USD_PER_1M_TOKENS)
                        + (total_completion_tokens / 1_000_000 * OUTPUT_USD_PER_1M_TOKENS),
                        6,
                    ),
                    "status": "running",
                },
            )

    total_cost = round((total_prompt_tokens / 1_000_000 * INPUT_USD_PER_1M_TOKENS) + (total_completion_tokens / 1_000_000 * OUTPUT_USD_PER_1M_TOKENS), 6)
    completed_at = _utc_now()
    summary = {
        "run_id": run_id,
        "stage": "gate8t_hotpotqa_mini_main_run",
        "dataset_id": dataset_id,
        "split": split,
        "source_snapshot_id": snapshot["source_snapshot_id"],
        "retrieval_index_path": snapshot["retrieval_index_path"],
        "baselines": list(baselines),
        "question_count": len(questions),
        "attempted_call_count": attempted_call_count,
        "success_count": len(run_records),
        "failure_count": len(failures),
        "resumed_record_count": len(resumed_run_records),
        "new_success_count": len(run_records) - len(resumed_run_records),
        "max_provider_attempts": int(max_provider_attempts),
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "estimated_cost_usd": total_cost,
        "pricing_source": PRICING_SOURCE,
        "started_at": started_at,
        "completed_at": completed_at,
        "artifact_path": output.as_posix(),
        "not_paper_result": True,
    }
    cost_summary = {
        "provider": "deepseek",
        "model": MODEL_ID,
        "pricing_source": PRICING_SOURCE,
        "input_usd_per_1m_tokens": INPUT_USD_PER_1M_TOKENS,
        "output_usd_per_1m_tokens": OUTPUT_USD_PER_1M_TOKENS,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "estimated_cost_usd": total_cost,
    }

    _write_jsonl(output / "run_records.jsonl", run_records)
    _write_jsonl(output / "metric_records.jsonl", metric_records)
    _write_jsonl(output / "retrieval_records.jsonl", retrieval_records)
    _write_jsonl(output / "request_manifest.jsonl", request_manifest)
    _write_json(output / "cost_summary.json", cost_summary)
    _write_json(output / "failures.json", failures)
    _write_yaml(output / "mini_run_summary.yaml", summary)
    if not dry_run:
        _write_jsonl(output / "raw_responses.jsonl", raw_responses)
    _emit_progress(
        progress_path,
        progress_stream,
        {
            "dataset_id": dataset_id,
            "split": split,
            "question_index": len(questions),
            "question_count": len(questions),
            "baseline_family": "complete",
            "attempted_call_count": attempted_call_count,
            "success_count": len(run_records),
            "failure_count": len(failures),
            "skipped_count": skipped_count,
            "estimated_cost_usd": total_cost,
            "status": "completed",
        },
    )
    return summary

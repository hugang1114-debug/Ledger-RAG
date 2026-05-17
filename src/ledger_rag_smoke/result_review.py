import hashlib
import json
import re
from pathlib import Path


REQUIRED_ARTIFACTS = (
    "request.json",
    "response.json",
    "run_record.json",
    "metric_record.json",
    "cost_estimate.json",
)

SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_\-]{12,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-.]{12,}", re.IGNORECASE),
    re.compile(r"DEEPSEEK_API_KEY\s*=", re.IGNORECASE),
)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _scan_for_secret(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def _answer_digest(answer_text):
    return hashlib.sha256(answer_text.encode("utf-8")).hexdigest()


def _append_blocker(blockers, condition, blocker):
    if condition:
        blockers.append(blocker)


def review_smoke_artifacts(artifact_dir, budget_ceiling_usd=10):
    artifact_dir = Path(artifact_dir)
    blockers = []
    artifact_hashes = {}
    artifact_sizes = {}

    for artifact_name in REQUIRED_ARTIFACTS:
        path = artifact_dir / artifact_name
        if not path.is_file():
            blockers.append(f"missing_artifact_{artifact_name}")
            continue
        artifact_hashes[artifact_name] = sha256_file(path)
        artifact_sizes[artifact_name] = path.stat().st_size

    if blockers:
        return {
            "gate": "gate8q_smoke_result_review",
            "review_status": "failed",
            "artifact_dir": artifact_dir.as_posix(),
            "artifact_hashes": artifact_hashes,
            "artifact_sizes": artifact_sizes,
            "blockers": blockers,
            "full_gate8_execution_authorized": False,
            "not_paper_result": True,
        }

    request = _load_json(artifact_dir / "request.json")
    response = _load_json(artifact_dir / "response.json")
    run_record = _load_json(artifact_dir / "run_record.json")
    metric_record = _load_json(artifact_dir / "metric_record.json")
    cost_estimate = _load_json(artifact_dir / "cost_estimate.json")

    secret_hits = [name for name in REQUIRED_ARTIFACTS if _scan_for_secret(artifact_dir / name)]
    answer = run_record.get("answer", {})
    claims = answer.get("atomic_claims") or []
    citations = run_record.get("citations") or []
    run_metadata = run_record.get("run_metadata", {})
    input_record = run_record.get("input", {})
    estimated_cost = cost_estimate.get("estimated_cost_usd")

    _append_blocker(blockers, request.get("model") != "deepseek-v4-pro", "request_model_not_deepseek_v4_pro")
    _append_blocker(blockers, response.get("model") != "deepseek-v4-pro", "response_model_not_deepseek_v4_pro")
    _append_blocker(blockers, cost_estimate.get("provider") != "deepseek", "cost_provider_not_deepseek")
    _append_blocker(blockers, cost_estimate.get("model") != "deepseek-v4-pro", "cost_model_not_deepseek_v4_pro")
    _append_blocker(blockers, not answer.get("global_answer"), "answer_missing")
    _append_blocker(blockers, not claims, "atomic_claims_missing")
    _append_blocker(blockers, not citations, "citations_missing")
    _append_blocker(blockers, not isinstance(metric_record.get("metric_record"), dict), "metric_record_missing")
    _append_blocker(blockers, estimated_cost is None, "estimated_cost_missing")
    _append_blocker(
        blockers,
        estimated_cost is not None and float(estimated_cost) > float(budget_ceiling_usd),
        "estimated_cost_exceeds_budget",
    )
    _append_blocker(blockers, bool(secret_hits), "secret_pattern_found_in_artifacts")

    summary = {
        "gate": "gate8q_smoke_result_review",
        "review_status": "failed" if blockers else "passed",
        "artifact_dir": artifact_dir.as_posix(),
        "artifact_hashes": artifact_hashes,
        "artifact_sizes": artifact_sizes,
        "provider": cost_estimate.get("provider"),
        "model": cost_estimate.get("model"),
        "run_id": run_metadata.get("run_id"),
        "dataset_id": input_record.get("dataset_id"),
        "split": input_record.get("split"),
        "question_id": input_record.get("question_id"),
        "estimated_cost_usd": estimated_cost,
        "budget_ceiling_usd": budget_ceiling_usd,
        "within_budget": estimated_cost is not None and float(estimated_cost) <= float(budget_ceiling_usd),
        "usage": cost_estimate.get("usage", {}),
        "answer_present": bool(answer.get("global_answer")),
        "answer_sha256": _answer_digest(answer.get("global_answer", "")),
        "claim_count": len(claims),
        "citation_count": len(citations),
        "secret_scan_passed": not secret_hits,
        "secret_scan_artifact_hits": secret_hits,
        "full_gate8_execution_authorized": False,
        "not_paper_result": True,
        "blockers": blockers,
    }
    return summary


def _yaml_scalar(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if not text:
        return '""'
    if re.fullmatch(r"[A-Za-z0-9_./:\-]+", text):
        return text
    return json.dumps(text)


def _write_yaml_lines(lines, key, value, indent=0):
    prefix = " " * indent
    if isinstance(value, dict):
        lines.append(f"{prefix}{key}:")
        for child_key in sorted(value):
            _write_yaml_lines(lines, child_key, value[child_key], indent + 2)
    elif isinstance(value, list):
        lines.append(f"{prefix}{key}:")
        for item in value:
            lines.append(f"{prefix}  - {_yaml_scalar(item)}")
    else:
        lines.append(f"{prefix}{key}: {_yaml_scalar(value)}")


def write_summary_yaml(path, summary):
    lines = []
    for key in sorted(summary):
        _write_yaml_lines(lines, key, summary[key], 0)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")

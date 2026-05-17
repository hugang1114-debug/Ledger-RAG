from dataclasses import dataclass
from pathlib import Path

from ledger_rag_gate8.freeze_readiness import load_simple_yaml
from ledger_rag_gate8.prompt_config_readiness import parse_slot_section


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_PROVIDER_IDS = {"openai_gpt_5_4", "deepseek_v4_pro"}
REQUIRED_CANDIDATE_FIELDS = {
    "id",
    "provider",
    "model",
    "candidate_locked",
    "final_selected",
    "authorized_to_run",
    "official_model_url",
    "official_pricing_url",
    "pricing_checked_at",
    "input_usd_per_1m_tokens",
    "cached_input_usd_per_1m_tokens",
    "output_usd_per_1m_tokens",
    "context_window_note",
    "max_output_note",
    "json_output_support",
    "tool_call_support",
    "terms_or_data_policy_note",
    "risk_notes",
    "recommended_role",
}


@dataclass(frozen=True)
class ProviderBudgetPreflightInputs:
    provider_candidates_path: Path
    budget_preflight_path: Path
    provider_registry: dict
    budget_preflight: dict
    provider_candidates: list
    budget_includes: list
    budget_excludes: list


def _resolve_repo_path(path):
    candidate = Path(str(path))
    if candidate.is_absolute():
        return candidate.resolve()
    return (ROOT / candidate).resolve()


def parse_provider_candidates(path):
    return parse_slot_section(path, "provider_candidates")


def _parse_list_section(path, section_name):
    path = Path(path)
    values = []
    in_section = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()
        if indent == 0 and stripped == f"{section_name}:":
            in_section = True
            continue
        if in_section and indent == 0:
            break
        if in_section and indent > 0 and stripped.startswith("- "):
            values.append(stripped[2:].strip())
    return values


def parse_budget_lists(path):
    return _parse_list_section(path, "budget_includes"), _parse_list_section(path, "budget_excludes")


def load_provider_budget_preflight_inputs(provider_candidates_path, budget_preflight_path):
    provider_candidates_path = _resolve_repo_path(provider_candidates_path)
    budget_preflight_path = _resolve_repo_path(budget_preflight_path)
    budget_includes, budget_excludes = parse_budget_lists(budget_preflight_path)
    return ProviderBudgetPreflightInputs(
        provider_candidates_path=provider_candidates_path,
        budget_preflight_path=budget_preflight_path,
        provider_registry=load_simple_yaml(provider_candidates_path),
        budget_preflight=load_simple_yaml(budget_preflight_path),
        provider_candidates=parse_provider_candidates(provider_candidates_path),
        budget_includes=budget_includes,
        budget_excludes=budget_excludes,
    )


def _is_unset(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() in {"", "unset"}
    return False


def _is_positive_number(value):
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def _summary_path(path):
    path = Path(path)
    if path.is_relative_to(ROOT):
        return path.relative_to(ROOT).as_posix()
    return path.as_posix()


def _dedupe(items):
    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _candidate_blockers(candidates, selected_provider):
    blockers = []
    ids = {candidate.get("id") for candidate in candidates if candidate.get("id")}
    missing_ids = EXPECTED_PROVIDER_IDS - ids
    extra_ids = ids - EXPECTED_PROVIDER_IDS
    if missing_ids:
        blockers.append("provider_candidates_missing_expected_ids")
    if extra_ids:
        blockers.append("provider_candidates_have_unexpected_ids")

    final_selected_count = 0
    selected_candidate_ids = []
    for candidate in candidates:
        candidate_id = candidate.get("id", "unknown")
        missing_fields = REQUIRED_CANDIDATE_FIELDS - set(candidate)
        if missing_fields:
            blockers.append(f"candidate_missing_fields_{candidate_id}")
            continue
        if candidate.get("candidate_locked") is not True:
            blockers.append(f"candidate_not_locked_{candidate_id}")
        if candidate.get("final_selected") is True:
            final_selected_count += 1
            selected_candidate_ids.append(candidate_id)
        if candidate.get("authorized_to_run") is True:
            blockers.append(f"candidate_authorized_{candidate_id}")
        for field in ("official_model_url", "official_pricing_url", "pricing_checked_at"):
            if _is_unset(candidate.get(field)):
                blockers.append(f"candidate_missing_{field}_{candidate_id}")
        for field in (
            "input_usd_per_1m_tokens",
            "cached_input_usd_per_1m_tokens",
            "output_usd_per_1m_tokens",
        ):
            if not _is_positive_number(candidate.get(field)):
                blockers.append(f"candidate_invalid_price_{field}_{candidate_id}")

    if final_selected_count > 1:
        blockers.append("multiple_provider_candidates_final_selected")
    if final_selected_count == 0:
        blockers.append("no_provider_candidate_final_selected")
    if selected_provider not in EXPECTED_PROVIDER_IDS:
        blockers.append("selected_provider_not_expected_candidate")
    if final_selected_count == 1 and selected_provider != selected_candidate_ids[0]:
        blockers.append("selected_provider_final_selected_mismatch")
    return _dedupe(blockers)


def _budget_blockers(budget, includes, excludes):
    blockers = []
    if budget.get("authorized_to_run") is True or budget.get("execution_authorized") is True:
        blockers.append("budget_execution_authorized")
    if not _is_positive_number(budget.get("smoke_run_budget_usd")):
        blockers.append("smoke_budget_missing_or_nonpositive")
    if budget.get("main_run_budget_usd") != "unset_requires_later_approval":
        blockers.append("main_budget_should_remain_unapproved")
    if not _is_positive_number(budget.get("retry_buffer_fraction")):
        blockers.append("retry_buffer_missing_or_nonpositive")
    if not includes:
        blockers.append("budget_includes_empty")
    if not excludes:
        blockers.append("budget_excludes_empty")
    return _dedupe(blockers)


def build_provider_budget_preflight_summary(inputs):
    provider_registry = inputs.provider_registry
    budget = inputs.budget_preflight
    execution_blockers = []
    selected_provider = provider_registry.get("selected_provider", "unset")
    selected_candidate_ids = [
        candidate.get("id")
        for candidate in inputs.provider_candidates
        if candidate.get("final_selected") is True
    ]
    selected_candidate_id = selected_candidate_ids[0] if len(selected_candidate_ids) == 1 else "unset"
    candidate_blockers = _candidate_blockers(inputs.provider_candidates, selected_provider)
    budget_blockers = _budget_blockers(budget, inputs.budget_includes, inputs.budget_excludes)
    execution_authorized = (
        provider_registry.get("authorized_to_run") is True
        and provider_registry.get("execution_authorized") is True
        and budget.get("authorized_to_run") is True
        and budget.get("execution_authorized") is True
    )

    if _is_unset(selected_provider):
        execution_blockers.append("selected_provider_unset")
    if not execution_authorized:
        execution_blockers.append("execution_not_authorized")
    if provider_registry.get("pricing_recheck_required_on_run_date") is True:
        execution_blockers.append("run_date_pricing_recheck_required")
    if budget.get("budget_owner_approval") != "approved":
        execution_blockers.append("budget_owner_approval_missing")

    provider_budget_preflight_ready = not candidate_blockers and not budget_blockers

    return {
        "gate": provider_registry.get("gate"),
        "stage": provider_registry.get("stage"),
        "provider_budget_preflight_ready": provider_budget_preflight_ready,
        "execution_authorized": execution_authorized,
        "selected_provider": selected_provider,
        "selected_candidate_id": selected_candidate_id,
        "candidate_ids": sorted(candidate.get("id") for candidate in inputs.provider_candidates),
        "smoke_run_budget_usd": budget.get("smoke_run_budget_usd"),
        "main_run_budget_usd": budget.get("main_run_budget_usd"),
        "retry_buffer_fraction": budget.get("retry_buffer_fraction"),
        "candidate_blockers": candidate_blockers,
        "budget_blockers": budget_blockers,
        "execution_blockers": _dedupe(execution_blockers),
        "checked_configs": {
            "provider_candidates": _summary_path(inputs.provider_candidates_path),
            "budget_preflight": _summary_path(inputs.budget_preflight_path),
        },
    }

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FREEZE_FIELDS = {
    "version",
    "gate",
    "stage",
    "status",
    "authorized_to_run",
    "run_matrix",
    "provider_decision",
    "provider_freeze_selected",
    "provider_pricing_checked_on_run_date",
    "provider_docs_checked_on_run_date",
    "terms_checked_on_run_date",
    "api_key_or_runtime_available",
    "prompt_versions_locked",
    "generation_config_locked",
    "cost_budget_approved",
    "execution_card",
    "reproducibility_review_complete",
    "execution_authorized",
    "blockers",
}

REQUIRED_RUN_MATRIX_FIELDS = {"gate", "stage", "authorized_to_run"}
REQUIRED_PROVIDER_FIELDS = {"gate", "stage", "selected", "provider", "model", "run_authorized"}


@dataclass(frozen=True)
class FreezeInputs:
    freeze_path: Path
    run_matrix_path: Path
    provider_decision_path: Path
    freeze_config: dict
    run_matrix: dict
    provider_decision: dict


def _parse_scalar(value):
    value = value.strip()
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if value.isdigit():
        return int(value)
    return value


def load_simple_yaml(path):
    path = Path(path)
    data = {}
    current_list_key = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()

        if indent == 0 and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value == "":
                data[key] = []
                current_list_key = key
            else:
                data[key] = _parse_scalar(value)
                current_list_key = None
            continue

        if indent > 0 and current_list_key and stripped.startswith("- "):
            data[current_list_key].append(_parse_scalar(stripped[2:].strip()))

    return data


def _resolve_repo_path(base_path, candidate):
    candidate_path = Path(str(candidate))
    if candidate_path.is_absolute():
        return candidate_path
    return (ROOT / candidate_path).resolve()


def load_freeze_inputs(freeze_config_path):
    freeze_path = Path(freeze_config_path).resolve()
    freeze_config = load_simple_yaml(freeze_path)
    run_matrix_path = _resolve_repo_path(freeze_path, freeze_config.get("run_matrix", ""))
    provider_path = _resolve_repo_path(freeze_path, freeze_config.get("provider_decision", ""))

    return FreezeInputs(
        freeze_path=freeze_path,
        run_matrix_path=run_matrix_path,
        provider_decision_path=provider_path,
        freeze_config=freeze_config,
        run_matrix=load_simple_yaml(run_matrix_path),
        provider_decision=load_simple_yaml(provider_path),
    )


def _missing_fields(record, required_fields, label):
    return [
        {
            "config": label,
            "field": field,
            "message": "required field is missing",
        }
        for field in sorted(required_fields - set(record))
    ]


def _dedupe(items):
    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _add_blocker(blockers, condition, blocker):
    if condition:
        blockers.append(blocker)


def build_freeze_readiness_summary(inputs):
    freeze_config = inputs.freeze_config
    run_matrix = inputs.run_matrix
    provider_decision = inputs.provider_decision
    validation_errors = []
    validation_errors.extend(_missing_fields(freeze_config, REQUIRED_FREEZE_FIELDS, "freeze_config"))
    validation_errors.extend(_missing_fields(run_matrix, REQUIRED_RUN_MATRIX_FIELDS, "run_matrix"))
    validation_errors.extend(_missing_fields(provider_decision, REQUIRED_PROVIDER_FIELDS, "provider_decision"))

    blockers = list(freeze_config.get("blockers", []))
    _add_blocker(blockers, freeze_config.get("authorized_to_run") is not True, "freeze_authorization_disabled")
    _add_blocker(blockers, freeze_config.get("provider_freeze_selected") is not True, "provider_freeze_unselected")
    _add_blocker(blockers, freeze_config.get("provider_pricing_checked_on_run_date") is not True, "provider_pricing_not_checked_on_run_date")
    _add_blocker(blockers, freeze_config.get("provider_docs_checked_on_run_date") is not True, "provider_docs_not_checked_on_run_date")
    _add_blocker(blockers, freeze_config.get("terms_checked_on_run_date") is not True, "terms_not_checked_on_run_date")
    _add_blocker(blockers, freeze_config.get("api_key_or_runtime_available") is not True, "api_key_or_runtime_unverified")
    _add_blocker(blockers, freeze_config.get("prompt_versions_locked") is not True, "prompt_versions_unlocked")
    _add_blocker(blockers, freeze_config.get("generation_config_locked") is not True, "generation_config_unlocked")
    _add_blocker(blockers, freeze_config.get("cost_budget_approved") is not True, "cost_budget_unapproved")
    _add_blocker(blockers, freeze_config.get("execution_card") == "unset", "execution_card_missing")
    _add_blocker(blockers, freeze_config.get("reproducibility_review_complete") is not True, "reproducibility_review_unfinished")
    _add_blocker(blockers, freeze_config.get("execution_authorized") is not True, "execution_not_authorized")
    _add_blocker(blockers, run_matrix.get("authorized_to_run") is not True, "run_matrix_not_authorized")
    _add_blocker(blockers, provider_decision.get("selected") is not True, "provider_decision_unselected")
    _add_blocker(blockers, provider_decision.get("run_authorized") is not True, "provider_decision_not_authorized")
    blockers = _dedupe(blockers)

    freeze_ready = not validation_errors and not blockers

    return {
        "gate": freeze_config.get("gate"),
        "stage": freeze_config.get("stage"),
        "status": freeze_config.get("status"),
        "freeze_ready": freeze_ready,
        "authorized_to_run": freeze_config.get("authorized_to_run") is True,
        "blockers": blockers,
        "checked_configs": {
            "freeze_config": inputs.freeze_path.relative_to(ROOT).as_posix(),
            "run_matrix": inputs.run_matrix_path.relative_to(ROOT).as_posix(),
            "provider_decision": inputs.provider_decision_path.relative_to(ROOT).as_posix(),
        },
        "validation_errors": validation_errors,
    }

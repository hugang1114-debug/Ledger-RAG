from dataclasses import dataclass
from pathlib import Path

from ledger_rag_gate8.freeze_readiness import load_simple_yaml
from ledger_rag_gate8.prompt_config_readiness import parse_slot_section


ROOT = Path(__file__).resolve().parents[2]

EXPECTED_EVIDENCE_IDS = {
    "official_pricing_source",
    "official_model_docs_source",
    "official_terms_privacy_source",
    "model_id_version_source",
    "context_window_source",
    "output_limit_source",
    "rate_limit_or_throughput_source",
    "api_key_or_runtime_availability_note",
    "cost_budget_approval_note",
}

CANDIDATE_EVIDENCE_IDS = {
    "official_pricing_source",
    "official_model_docs_source",
    "official_terms_privacy_source",
    "model_id_version_source",
    "context_window_source",
    "output_limit_source",
    "rate_limit_or_throughput_source",
}

REQUIRED_CANDIDATE_REGISTRY_FIELDS = {
    "provider_evidence_candidate_locked",
    "provider_candidate_selected",
    "candidate_provider",
    "candidate_model",
    "candidate_model_snapshot",
}

REQUIRED_REGISTRY_FIELDS = {
    "gate",
    "stage",
    "status",
    "authorized_to_run",
    "provider_evidence_locked",
    "provider_selected",
    "provider",
    "model",
    "evidence_slots",
    "blockers",
}

REQUIRED_PROVIDER_DECISION_FIELDS = {
    "gate",
    "stage",
    "selected",
    "provider",
    "model",
    "run_authorized",
}


@dataclass(frozen=True)
class ProviderEvidenceInputs:
    registry_path: Path
    provider_decision_path: Path
    registry: dict
    provider_decision: dict
    evidence_slots: list


def parse_evidence_slots(path):
    return parse_slot_section(path, "evidence_slots")


def _resolve_repo_path(candidate):
    candidate_path = Path(str(candidate))
    if candidate_path.is_absolute():
        return candidate_path.resolve()
    return (ROOT / candidate_path).resolve()


def load_provider_evidence_inputs(registry_path, provider_decision_path=None):
    registry_path = _resolve_repo_path(registry_path)
    registry = load_simple_yaml(registry_path)
    provider_decision_ref = provider_decision_path
    if provider_decision_ref is None:
        provider_decision_ref = registry.get("provider_decision", "configs/gate8/provider_decision.yaml")
    provider_decision_path = _resolve_repo_path(provider_decision_ref)

    return ProviderEvidenceInputs(
        registry_path=registry_path,
        provider_decision_path=provider_decision_path,
        registry=registry,
        provider_decision=load_simple_yaml(provider_decision_path),
        evidence_slots=parse_evidence_slots(registry_path),
    )


def _missing_fields(record, required_fields, label):
    return [
        {"config": label, "field": field, "message": "required field is missing"}
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


def _has_items(record, field):
    value = record.get(field)
    return isinstance(value, list) and len(value) > 0


def _is_unset(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() in {"", "unset"}
    return False


def _summary_path(path):
    path = Path(path)
    if path.is_relative_to(ROOT):
        return path.relative_to(ROOT).as_posix()
    return path.as_posix()


def _slot_by_id(slots):
    return {slot.get("evidence_id"): slot for slot in slots if slot.get("evidence_id")}


def _candidate_path_active(registry):
    return (
        registry.get("provider_evidence_candidate_locked") is True
        or registry.get("provider_candidate_selected") is True
        or not _is_unset(registry.get("candidate_provider"))
        or not _is_unset(registry.get("candidate_model"))
        or not _is_unset(registry.get("candidate_model_snapshot"))
    )


def _candidate_missing_evidence_ids(slots_by_id):
    missing = []
    unreviewed = []
    for evidence_id in sorted(CANDIDATE_EVIDENCE_IDS):
        slot = slots_by_id.get(evidence_id, {})
        if (
            not slot
            or _is_unset(slot.get("official_source_url"))
            or _is_unset(slot.get("checked_at"))
            or slot.get("evidence_status") != "reviewed"
        ):
            missing.append(evidence_id)
        if (
            not slot
            or slot.get("evidence_status") != "reviewed"
            or _is_unset(slot.get("reviewer"))
        ):
            unreviewed.append(evidence_id)
    return missing, unreviewed


def _candidate_blockers(registry, provider_decision, missing_candidate_ids, unreviewed_candidate_ids):
    blockers = []
    candidate_provider = registry.get("candidate_provider")
    candidate_model = registry.get("candidate_model")
    candidate_model_snapshot = registry.get("candidate_model_snapshot")
    decision_candidate_provider = provider_decision.get("candidate_provider")
    decision_candidate_model = provider_decision.get("candidate_model")
    decision_candidate_model_snapshot = provider_decision.get("candidate_model_snapshot")

    if registry.get("provider_evidence_candidate_locked") is not True:
        blockers.append("provider_evidence_candidate_not_locked")
    if registry.get("provider_candidate_selected") is not True:
        blockers.append("provider_candidate_not_selected")
    if _is_unset(candidate_provider):
        blockers.append("candidate_provider_unset")
    if _is_unset(candidate_model):
        blockers.append("candidate_model_unset")
    if _is_unset(candidate_model_snapshot):
        blockers.append("candidate_snapshot_unset")
    if _is_unset(decision_candidate_provider):
        blockers.append("provider_decision_candidate_provider_unset")
    if _is_unset(decision_candidate_model):
        blockers.append("provider_decision_candidate_model_unset")
    if _is_unset(decision_candidate_model_snapshot):
        blockers.append("provider_decision_candidate_snapshot_unset")
    if missing_candidate_ids:
        blockers.append("provider_candidate_missing_sources")
    if unreviewed_candidate_ids:
        blockers.append("provider_candidate_unreviewed")
    if not _is_unset(candidate_provider) and not _is_unset(decision_candidate_provider):
        if candidate_provider != decision_candidate_provider:
            blockers.append("provider_decision_candidate_provider_mismatch")
    if not _is_unset(candidate_model) and not _is_unset(decision_candidate_model):
        if candidate_model != decision_candidate_model:
            blockers.append("provider_decision_candidate_model_mismatch")
    if not _is_unset(candidate_model_snapshot) and not _is_unset(decision_candidate_model_snapshot):
        if candidate_model_snapshot != decision_candidate_model_snapshot:
            blockers.append("provider_decision_candidate_snapshot_mismatch")
    return blockers


def build_provider_evidence_readiness_summary(inputs):
    registry = inputs.registry
    provider_decision = inputs.provider_decision
    registry_provider = registry.get("provider")
    registry_model = registry.get("model")
    decision_provider = provider_decision.get("provider")
    decision_model = provider_decision.get("model")
    slots_by_id = _slot_by_id(inputs.evidence_slots)
    absent_evidence_ids = sorted(EXPECTED_EVIDENCE_IDS - set(slots_by_id))
    candidate_path_active = _candidate_path_active(registry)
    missing_candidate_ids, unreviewed_candidate_ids = _candidate_missing_evidence_ids(slots_by_id)
    candidate_blockers = []
    if candidate_path_active:
        candidate_blockers = _candidate_blockers(
            registry,
            provider_decision,
            missing_candidate_ids,
            unreviewed_candidate_ids,
        )

    missing_evidence_ids = []
    unreviewed_evidence_ids = []
    for evidence_id in sorted(EXPECTED_EVIDENCE_IDS):
        slot = slots_by_id.get(evidence_id, {})
        if (
            not slot
            or _is_unset(slot.get("official_source_url"))
            or _is_unset(slot.get("checked_at"))
            or slot.get("evidence_status") != "reviewed"
        ):
            missing_evidence_ids.append(evidence_id)
        if (
            not slot
            or slot.get("evidence_status") != "reviewed"
            or _is_unset(slot.get("reviewer"))
        ):
            unreviewed_evidence_ids.append(evidence_id)

    validation_errors = []
    validation_errors.extend(_missing_fields(registry, REQUIRED_REGISTRY_FIELDS, "provider_evidence_registry"))
    validation_errors.extend(
        _missing_fields(provider_decision, REQUIRED_PROVIDER_DECISION_FIELDS, "provider_decision")
    )
    if candidate_path_active and registry.get("provider_evidence_candidate_locked") is True:
        validation_errors.extend(
            _missing_fields(
                registry,
                REQUIRED_CANDIDATE_REGISTRY_FIELDS,
                "provider_evidence_registry",
            )
        )

    blockers = []
    blockers.extend(registry.get("blockers", []))
    if registry.get("authorized_to_run") is not True:
        blockers.append("provider_evidence_registry_not_authorized")
    if registry.get("provider_evidence_locked") is not True:
        blockers.append("provider_evidence_not_locked")
    if registry.get("provider_selected") is not True or registry.get("provider") == "unset":
        blockers.append("provider_not_selected")
    if registry.get("model") == "unset":
        blockers.append("model_not_selected")
    if absent_evidence_ids:
        blockers.append("provider_evidence_missing_slots")
    if missing_evidence_ids:
        blockers.append("provider_evidence_missing_sources")
    if unreviewed_evidence_ids:
        blockers.append("provider_evidence_unreviewed")
    if _has_items(registry, "blockers"):
        blockers.append("provider_evidence_registry_has_blockers")
    if provider_decision.get("selected") is not True:
        blockers.append("provider_decision_unselected")
    if provider_decision.get("run_authorized") is not True:
        blockers.append("provider_decision_not_authorized")
    if _is_unset(decision_provider):
        blockers.append("provider_decision_provider_unset")
    if _is_unset(decision_model):
        blockers.append("provider_decision_model_unset")
    if not _is_unset(registry_provider) and not _is_unset(decision_provider):
        if registry_provider != decision_provider:
            blockers.append("provider_decision_provider_mismatch")
    if not _is_unset(registry_model) and not _is_unset(decision_model):
        if registry_model != decision_model:
            blockers.append("provider_decision_model_mismatch")
    blockers.extend(candidate_blockers)
    blockers = _dedupe(blockers)

    provider_evidence_ready = not validation_errors and not blockers
    provider_candidate_ready = (
        not validation_errors
        and registry.get("provider_evidence_candidate_locked") is True
        and registry.get("provider_candidate_selected") is True
        and not candidate_blockers
    )

    return {
        "gate": registry.get("gate"),
        "stage": "gate8i_provider_evidence_readiness",
        "status": registry.get("status"),
        "provider_evidence_ready": provider_evidence_ready,
        "provider_candidate_ready": provider_candidate_ready,
        "authorized_to_run": registry.get("authorized_to_run") is True,
        "provider_selected": registry.get("provider_selected") is True,
        "provider_candidate_selected": registry.get("provider_candidate_selected") is True,
        "provider_evidence_candidate_locked": registry.get("provider_evidence_candidate_locked") is True,
        "provider": registry_provider,
        "model": registry_model,
        "candidate_provider": registry.get("candidate_provider", "unset"),
        "candidate_model": registry.get("candidate_model", "unset"),
        "candidate_model_snapshot": registry.get("candidate_model_snapshot", "unset"),
        "provider_decision_selected": provider_decision.get("selected") is True,
        "provider_decision_authorized": provider_decision.get("run_authorized") is True,
        "missing_evidence_ids": missing_evidence_ids,
        "unreviewed_evidence_ids": unreviewed_evidence_ids,
        "missing_candidate_evidence_ids": missing_candidate_ids,
        "unreviewed_candidate_evidence_ids": unreviewed_candidate_ids,
        "evidence_slot_count": len(inputs.evidence_slots),
        "blockers": blockers,
        "checked_configs": {
            "provider_evidence_registry": _summary_path(inputs.registry_path),
            "provider_decision": _summary_path(inputs.provider_decision_path),
        },
        "validation_errors": validation_errors,
    }

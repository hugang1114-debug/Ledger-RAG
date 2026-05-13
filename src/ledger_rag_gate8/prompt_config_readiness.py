from dataclasses import dataclass
from pathlib import Path

from ledger_rag_gate8.freeze_readiness import load_simple_yaml


ROOT = Path(__file__).resolve().parents[2]

EXPECTED_BASELINE_FAMILIES = {
    "vanilla_rag",
    "hybrid_rag",
    "citation_only",
    "validator_only",
    "ledger_only",
    "ledger_validator",
}

REQUIRED_PROMPT_FIELDS = {"gate", "stage", "authorized_to_run", "prompt_versions_locked"}
REQUIRED_GENERATION_FIELDS = {"gate", "stage", "authorized_to_run", "generation_config_locked"}


@dataclass(frozen=True)
class PromptConfigInputs:
    prompt_registry_path: Path
    generation_config_path: Path
    prompt_registry: dict
    generation_config: dict
    prompt_slots: list
    generation_slots: list


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


def parse_slot_section(path, section_name):
    path = Path(path)
    slots = []
    current = None
    in_section = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()

        if indent == 0 and stripped == f"{section_name}:":
            in_section = True
            current = None
            continue

        if in_section and indent == 0:
            break

        if not in_section:
            continue

        if stripped.startswith("- "):
            if current:
                slots.append(current)
            current = {}
            payload = stripped[2:].strip()
            if ":" in payload:
                key, value = payload.split(":", 1)
                current[key.strip()] = _parse_scalar(value.strip())
            continue

        if current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = _parse_scalar(value.strip())

    if current:
        slots.append(current)

    return slots


def load_prompt_config_inputs(prompt_registry_path, generation_config_path):
    prompt_path = Path(prompt_registry_path).resolve()
    generation_path = Path(generation_config_path).resolve()
    return PromptConfigInputs(
        prompt_registry_path=prompt_path,
        generation_config_path=generation_path,
        prompt_registry=load_simple_yaml(prompt_path),
        generation_config=load_simple_yaml(generation_path),
        prompt_slots=parse_slot_section(prompt_path, "baseline_prompt_slots"),
        generation_slots=parse_slot_section(generation_path, "baseline_generation_slots"),
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


def _families(slots):
    return {slot.get("baseline_family") for slot in slots if slot.get("baseline_family")}


def _has_items(record, field):
    value = record.get(field)
    return isinstance(value, list) and len(value) > 0


def _summary_path(path):
    path = Path(path)
    if path.is_relative_to(ROOT):
        return path.relative_to(ROOT).as_posix()
    return path.as_posix()


def build_prompt_config_readiness_summary(inputs):
    prompt_registry = inputs.prompt_registry
    generation_config = inputs.generation_config
    prompt_families = _families(inputs.prompt_slots)
    generation_families = _families(inputs.generation_slots)
    missing_prompt = sorted(EXPECTED_BASELINE_FAMILIES - prompt_families)
    missing_generation = sorted(EXPECTED_BASELINE_FAMILIES - generation_families)

    validation_errors = []
    validation_errors.extend(_missing_fields(prompt_registry, REQUIRED_PROMPT_FIELDS, "prompt_registry"))
    validation_errors.extend(_missing_fields(generation_config, REQUIRED_GENERATION_FIELDS, "generation_config_registry"))

    blockers = []
    blockers.extend(prompt_registry.get("blockers", []))
    blockers.extend(generation_config.get("blockers", []))
    if prompt_registry.get("authorized_to_run") is not True:
        blockers.append("prompt_registry_not_authorized")
    if generation_config.get("authorized_to_run") is not True:
        blockers.append("generation_config_registry_not_authorized")
    if prompt_registry.get("prompt_versions_locked") is not True:
        blockers.append("prompt_versions_unlocked")
    if prompt_registry.get("prompt_text_frozen") is not True:
        blockers.append("prompt_text_not_frozen")
    if generation_config.get("generation_config_locked") is not True:
        blockers.append("generation_config_unlocked")
    if generation_config.get("shared_answer_style_locked") is not True:
        blockers.append("shared_answer_style_unlocked")
    if generation_config.get("shared_evidence_budget_locked") is not True:
        blockers.append("shared_evidence_budget_unlocked")
    if missing_prompt:
        blockers.append("prompt_registry_missing_baselines")
    if missing_generation:
        blockers.append("generation_config_missing_baselines")
    if _has_items(prompt_registry, "blockers"):
        blockers.append("prompt_registry_has_blockers")
    if _has_items(generation_config, "blockers"):
        blockers.append("generation_config_registry_has_blockers")
    blockers = _dedupe(blockers)

    prompt_config_ready = not validation_errors and not blockers

    return {
        "gate": prompt_registry.get("gate"),
        "stage": "gate8h_prompt_config_readiness",
        "prompt_config_ready": prompt_config_ready,
        "authorized_to_run": (
            prompt_registry.get("authorized_to_run") is True
            and generation_config.get("authorized_to_run") is True
        ),
        "baseline_families": sorted(EXPECTED_BASELINE_FAMILIES),
        "missing_prompt_families": missing_prompt,
        "missing_generation_families": missing_generation,
        "prompt_slot_count": len(inputs.prompt_slots),
        "generation_slot_count": len(inputs.generation_slots),
        "blockers": blockers,
        "checked_configs": {
            "prompt_registry": _summary_path(inputs.prompt_registry_path),
            "generation_config": _summary_path(inputs.generation_config_path),
        },
        "validation_errors": validation_errors,
    }

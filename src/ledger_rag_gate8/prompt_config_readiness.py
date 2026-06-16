import re
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from ledger_rag_gate8.freeze_readiness import load_simple_yaml


ROOT = Path(__file__).resolve().parents[2]
PROMPT_DIR = ROOT / "prompts" / "gate8" / "main_v1"

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
REQUIRED_CANDIDATE_PROMPT_SLOT_FIELDS = {
    "baseline_family",
    "prompt_version",
    "prompt_status",
    "prompt_file",
    "prompt_sha256",
    "authorized_to_run",
}
REQUIRED_CANDIDATE_GENERATION_SLOT_FIELDS = {
    "baseline_family",
    "generation_config_version",
    "config_status",
    "authorized_to_run",
}


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


def parse_mapping_section(path, section_name):
    path = Path(path)
    mapping = {}
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

        if in_section and indent > 0 and ":" in stripped:
            key, value = stripped.split(":", 1)
            mapping[key.strip()] = _parse_scalar(value.strip())

    return mapping


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


def _repo_path(value):
    candidate = Path(str(value))
    if candidate.is_absolute():
        return candidate
    return (ROOT / candidate).resolve()


def _sha256_file(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def _contains_disallowed_marker(path):
    text = Path(path).read_text(encoding="utf-8")
    lowered = text.lower()
    markers = ["tb" + "d", "to" + "do"]
    return any(marker in lowered for marker in markers) or re.search(r"turn[0-9]+", lowered) is not None


def _summary_path(path):
    path = Path(path)
    if path.is_relative_to(ROOT):
        return path.relative_to(ROOT).as_posix()
    return path.as_posix()


def _candidate_blockers(inputs, prompt_families, generation_families):
    prompt_registry = inputs.prompt_registry
    generation_config = inputs.generation_config
    blockers = []

    if prompt_registry.get("authorized_to_run") is True:
        blockers.append("prompt_registry_accidentally_authorized")
    if generation_config.get("authorized_to_run") is True:
        blockers.append("generation_config_registry_accidentally_authorized")
    if prompt_registry.get("candidate_prompt_versions_locked") is not True:
        blockers.append("candidate_prompt_versions_unlocked")
    if prompt_registry.get("candidate_prompt_text_frozen") is not True:
        blockers.append("candidate_prompt_text_not_frozen")
    if generation_config.get("candidate_generation_config_locked") is not True:
        blockers.append("candidate_generation_config_unlocked")
    if generation_config.get("candidate_shared_answer_style_locked") is not True:
        blockers.append("candidate_shared_answer_style_unlocked")
    if generation_config.get("candidate_shared_evidence_budget_locked") is not True:
        blockers.append("candidate_shared_evidence_budget_unlocked")
    if EXPECTED_BASELINE_FAMILIES - prompt_families:
        blockers.append("candidate_prompt_registry_missing_baselines")
    if EXPECTED_BASELINE_FAMILIES - generation_families:
        blockers.append("candidate_generation_config_missing_baselines")

    shared_constraints = parse_mapping_section(inputs.generation_config_path, "shared_constraints")
    for field in [
        "answer_style",
        "citation_granularity",
        "max_evidence_items",
        "max_atomic_claims",
        "temperature",
        "max_output_tokens",
    ]:
        if shared_constraints.get(field) in (None, "unset", ""):
            blockers.append(f"candidate_shared_constraint_unset_{field}")

    for slot in inputs.prompt_slots:
        family = slot.get("baseline_family", "unknown")
        missing = REQUIRED_CANDIDATE_PROMPT_SLOT_FIELDS - set(slot)
        if missing:
            blockers.append(f"candidate_prompt_slot_missing_fields_{family}")
            continue
        if slot.get("authorized_to_run") is True:
            blockers.append(f"candidate_prompt_slot_authorized_{family}")
        if slot.get("prompt_status") != "candidate_locked":
            blockers.append(f"candidate_prompt_slot_not_locked_{family}")
        prompt_path = _repo_path(slot["prompt_file"])
        if not prompt_path.is_relative_to(PROMPT_DIR.resolve()):
            blockers.append(f"candidate_prompt_file_outside_prompt_dir_{family}")
            continue
        if prompt_path.name != f"{family}.md":
            blockers.append(f"candidate_prompt_file_name_mismatch_{family}")
            continue
        if not prompt_path.is_file():
            blockers.append(f"candidate_prompt_file_missing_{family}")
            continue
        if _sha256_file(prompt_path) != slot.get("prompt_sha256"):
            blockers.append(f"candidate_prompt_hash_mismatch_{family}")
        if _contains_disallowed_marker(prompt_path):
            blockers.append(f"candidate_prompt_marker_found_{family}")

    for slot in inputs.generation_slots:
        family = slot.get("baseline_family", "unknown")
        missing = REQUIRED_CANDIDATE_GENERATION_SLOT_FIELDS - set(slot)
        if missing:
            blockers.append(f"candidate_generation_slot_missing_fields_{family}")
            continue
        if slot.get("authorized_to_run") is True:
            blockers.append(f"candidate_generation_slot_authorized_{family}")
        if slot.get("config_status") != "candidate_locked":
            blockers.append(f"candidate_generation_slot_not_locked_{family}")

    return _dedupe(blockers)


def _freeze_blockers(inputs, prompt_families, generation_families):
    prompt_registry = inputs.prompt_registry
    generation_config = inputs.generation_config
    blockers = []

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
    if EXPECTED_BASELINE_FAMILIES - prompt_families:
        blockers.append("prompt_registry_missing_baselines")
    if EXPECTED_BASELINE_FAMILIES - generation_families:
        blockers.append("generation_config_missing_baselines")

    shared_constraints = parse_mapping_section(inputs.generation_config_path, "shared_constraints")
    for field in [
        "answer_style",
        "citation_granularity",
        "max_evidence_items",
        "max_atomic_claims",
        "temperature",
        "max_output_tokens",
    ]:
        if shared_constraints.get(field) in (None, "unset", ""):
            blockers.append(f"shared_constraint_unset_{field}")

    for slot in inputs.prompt_slots:
        family = slot.get("baseline_family", "unknown")
        missing = REQUIRED_CANDIDATE_PROMPT_SLOT_FIELDS - set(slot)
        if missing:
            blockers.append(f"prompt_slot_missing_fields_{family}")
            continue
        if slot.get("authorized_to_run") is True:
            blockers.append(f"prompt_slot_authorized_{family}")
        if slot.get("prompt_status") != "final_locked":
            blockers.append(f"prompt_slot_not_final_locked_{family}")
        prompt_path = _repo_path(slot["prompt_file"])
        if not prompt_path.is_relative_to(PROMPT_DIR.resolve()):
            blockers.append(f"prompt_file_outside_prompt_dir_{family}")
            continue
        if prompt_path.name != f"{family}.md":
            blockers.append(f"prompt_file_name_mismatch_{family}")
            continue
        if not prompt_path.is_file():
            blockers.append(f"prompt_file_missing_{family}")
            continue
        if _sha256_file(prompt_path) != slot.get("prompt_sha256"):
            blockers.append(f"prompt_hash_mismatch_{family}")
        if _contains_disallowed_marker(prompt_path):
            blockers.append(f"prompt_marker_found_{family}")

    for slot in inputs.generation_slots:
        family = slot.get("baseline_family", "unknown")
        missing = REQUIRED_CANDIDATE_GENERATION_SLOT_FIELDS - set(slot)
        if missing:
            blockers.append(f"generation_slot_missing_fields_{family}")
            continue
        if slot.get("authorized_to_run") is True:
            blockers.append(f"generation_slot_authorized_{family}")
        if slot.get("config_status") != "final_locked":
            blockers.append(f"generation_slot_not_final_locked_{family}")

    return _dedupe(blockers)


def build_prompt_config_readiness_summary(inputs):
    prompt_registry = inputs.prompt_registry
    generation_config = inputs.generation_config
    prompt_families = _families(inputs.prompt_slots)
    generation_families = _families(inputs.generation_slots)
    missing_prompt = sorted(EXPECTED_BASELINE_FAMILIES - prompt_families)
    missing_generation = sorted(EXPECTED_BASELINE_FAMILIES - generation_families)
    candidate_blockers = _candidate_blockers(inputs, prompt_families, generation_families)
    prompt_config_candidate_ready = not candidate_blockers
    freeze_blockers = _freeze_blockers(inputs, prompt_families, generation_families)
    prompt_config_frozen_ready = not freeze_blockers

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
        "stage": prompt_registry.get("stage"),
        "prompt_config_candidate_ready": prompt_config_candidate_ready,
        "prompt_config_frozen_ready": prompt_config_frozen_ready,
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
        "candidate_blockers": candidate_blockers,
        "freeze_blockers": freeze_blockers,
        "blockers": blockers,
        "checked_configs": {
            "prompt_registry": _summary_path(inputs.prompt_registry_path),
            "generation_config": _summary_path(inputs.generation_config_path),
        },
        "validation_errors": validation_errors,
    }

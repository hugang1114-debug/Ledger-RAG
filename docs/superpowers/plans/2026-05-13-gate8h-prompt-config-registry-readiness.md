# Gate 8H Prompt Config Registry Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add prompt and generation-config registry readiness checks for all Gate 5 baseline families without freezing final prompts or authorizing Gate 8 execution.

**Architecture:** Gate 8H adds two tracked registries, a standard-library-only prompt/config readiness checker, tests, docs, and freeze-readiness references. The checker confirms all six baseline families have reserved prompt/config slots while keeping prompt/config lockout blockers active.

**Tech Stack:** Python standard library, Markdown, YAML-like tracked config, pytest, existing Gate 8 readiness CLI patterns.

---

## File Structure

- Create `configs/gate8/prompt_registry.yaml`: non-executable prompt slot registry for all six Gate 5 baseline families.
- Create `configs/gate8/generation_config_registry.yaml`: non-executable generation config slot registry for all six Gate 5 baseline families.
- Create `docs/gate8-prompt-config-readiness.md`: human-readable Gate 8H scope and lockout rules.
- Create `experiments/cards/E013-gate8-prompt-config-readiness.md`: non-running experiment card for registry/checker work.
- Create `src/ledger_rag_gate8/prompt_config_readiness.py`: parser and readiness summary builder for the two registries.
- Create `scripts/check_gate8_prompt_config_readiness.py`: CLI wrapper that prints JSON and supports strict mode.
- Create `tests/test_gate8_prompt_config_readiness.py`: tests for registry coverage, missing-family detection, and CLI behavior.
- Modify `configs/gate8/freeze_readiness.yaml`: add prompt and generation config registry references.
- Modify `src/ledger_rag_gate8/freeze_readiness.py`: load optional registry references and keep freeze readiness blocked while registries are not locked.
- Modify `tests/test_gate8_freeze_readiness.py`: update freeze tests for registry references.
- Modify `README.md`: list Gate 8H docs/config/script.
- Modify `docs/main-comparison-readiness.md`: add Gate 8H command and non-execution boundary.
- Modify `configs/gate8/main_v1_readiness.yaml`: reference Gate 8H registry/check command and add lockout blockers.

---

### Task 1: Add Gate 8H Registries, Docs, And Card

**Files:**
- Create: `configs/gate8/prompt_registry.yaml`
- Create: `configs/gate8/generation_config_registry.yaml`
- Create: `docs/gate8-prompt-config-readiness.md`
- Create: `experiments/cards/E013-gate8-prompt-config-readiness.md`

- [ ] **Step 1: Create prompt registry**

Create `configs/gate8/prompt_registry.yaml` with:

```yaml
version: 1
gate: gate8_main_comparison
stage: gate8h_prompt_registry_readiness
status: readiness_in_progress
authorized_to_run: false
purpose: non_executable_prompt_registry
prompt_versions_locked: false
prompt_text_frozen: false

baseline_prompt_slots:
  - baseline_family: vanilla_rag
    prompt_version: unset
    prompt_status: slot_reserved
    prompt_file: unset
    requires_provider_freeze: true
    notes: final_prompt_required_later
  - baseline_family: hybrid_rag
    prompt_version: unset
    prompt_status: slot_reserved
    prompt_file: unset
    requires_provider_freeze: true
    notes: final_prompt_required_later
  - baseline_family: citation_only
    prompt_version: unset
    prompt_status: slot_reserved
    prompt_file: unset
    requires_provider_freeze: true
    notes: final_prompt_required_later
  - baseline_family: validator_only
    prompt_version: unset
    prompt_status: slot_reserved
    prompt_file: unset
    requires_provider_freeze: true
    notes: final_prompt_required_later
  - baseline_family: ledger_only
    prompt_version: unset
    prompt_status: slot_reserved
    prompt_file: unset
    requires_provider_freeze: true
    notes: final_prompt_required_later
  - baseline_family: ledger_validator
    prompt_version: unset
    prompt_status: slot_reserved
    prompt_file: unset
    requires_provider_freeze: true
    notes: final_prompt_required_later

blockers:
  - prompt_versions_unlocked
  - prompt_text_not_frozen
  - provider_not_selected
  - final_prompt_files_unset
```

- [ ] **Step 2: Create generation config registry**

Create `configs/gate8/generation_config_registry.yaml` with:

```yaml
version: 1
gate: gate8_main_comparison
stage: gate8h_generation_config_readiness
status: readiness_in_progress
authorized_to_run: false
purpose: non_executable_generation_config_registry
generation_config_locked: false
shared_answer_style_locked: false
shared_evidence_budget_locked: false

shared_constraints:
  answer_style: unset
  max_evidence_budget: unset
  temperature: unset
  seed: unset
  max_output_tokens: unset

baseline_generation_slots:
  - baseline_family: vanilla_rag
    generation_config_version: unset
    config_status: slot_reserved
    requires_provider_freeze: true
    notes: final_generation_config_required_later
  - baseline_family: hybrid_rag
    generation_config_version: unset
    config_status: slot_reserved
    requires_provider_freeze: true
    notes: final_generation_config_required_later
  - baseline_family: citation_only
    generation_config_version: unset
    config_status: slot_reserved
    requires_provider_freeze: true
    notes: final_generation_config_required_later
  - baseline_family: validator_only
    generation_config_version: unset
    config_status: slot_reserved
    requires_provider_freeze: true
    notes: final_generation_config_required_later
  - baseline_family: ledger_only
    generation_config_version: unset
    config_status: slot_reserved
    requires_provider_freeze: true
    notes: final_generation_config_required_later
  - baseline_family: ledger_validator
    generation_config_version: unset
    config_status: slot_reserved
    requires_provider_freeze: true
    notes: final_generation_config_required_later

blockers:
  - generation_config_unlocked
  - shared_answer_style_unlocked
  - shared_evidence_budget_unlocked
  - provider_not_selected
```

- [ ] **Step 3: Create Gate 8H readiness doc**

Create `docs/gate8-prompt-config-readiness.md` with:

```markdown
# Gate 8 Prompt Config Readiness

Gate 8H reserves prompt and generation config slots for the future main comparison. It does not write final prompt text, select a provider, check live prices, call models, run baselines, compute metrics, create result artifacts, or pass Gate 8.

## Current State

The current registries are intentionally non-executable:

- `prompt_versions_locked: false`
- `prompt_text_frozen: false`
- `generation_config_locked: false`
- `shared_answer_style_locked: false`
- `shared_evidence_budget_locked: false`
- `authorized_to_run: false`

Each Gate 5 baseline family has a reserved prompt slot and generation config slot:

- `vanilla_rag`
- `hybrid_rag`
- `citation_only`
- `validator_only`
- `ledger_only`
- `ledger_validator`

## Future Freeze Requirements

Before a main baseline run can be authorized, the project must record:

- final prompt version id for each baseline family
- final prompt file path for each baseline family
- generation config version id for each baseline family
- shared answer style
- shared max evidence budget
- deterministic settings where supported
- model/provider assumptions checked on the run date
- execution card with exact commands and output paths

## CLI Contract

Default mode is inspect-only:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml
```

Strict mode is for execution authorization checks:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml --require-ready
```

Strict mode is expected to fail until prompt text, generation config, provider, and execution metadata are locked.
```

- [ ] **Step 4: Create E013 card**

Create `experiments/cards/E013-gate8-prompt-config-readiness.md` with:

```markdown
# E013 Gate 8 Prompt Config Readiness

## Purpose

Create prompt and generation config registry readiness checks for all Gate 5 baseline families. This card authorizes registry metadata and local validation tooling only.

## Authorized Scope

- create `configs/gate8/prompt_registry.yaml`
- create `configs/gate8/generation_config_registry.yaml`
- create `docs/gate8-prompt-config-readiness.md`
- create `scripts/check_gate8_prompt_config_readiness.py`
- create standard-library-only readiness helper code
- add tests for registry coverage and strict lockout behavior
- update Gate 8 readiness references

## Prohibited Actions

- final prompt text creation
- model calls
- embedding calls
- reranker calls
- provider selection
- live pricing claims
- baseline execution
- retrieval evaluation
- metric computation
- result artifact creation
- source snapshot status promotion to `ready`

## Expected Outputs

- `configs/gate8/prompt_registry.yaml`
- `configs/gate8/generation_config_registry.yaml`
- `docs/gate8-prompt-config-readiness.md`
- `src/ledger_rag_gate8/prompt_config_readiness.py`
- `scripts/check_gate8_prompt_config_readiness.py`
- `tests/test_gate8_prompt_config_readiness.py`
- README and readiness doc references

## Success Criteria

- all six Gate 5 baseline families have prompt slots
- all six Gate 5 baseline families have generation config slots
- default prompt/config readiness command exits `0`
- default prompt/config readiness reports `prompt_config_ready: false`
- strict prompt/config readiness command exits nonzero
- Gate 8G freeze readiness remains blocked
- no provider, final prompt text, model calls, or result artifacts are created

## Cost Class

Local metadata and tests only. No model, API, provider, or cloud cost is authorized.
```

- [ ] **Step 5: Verify registries and docs**

Run:

```powershell
Test-Path configs\gate8\prompt_registry.yaml
Test-Path configs\gate8\generation_config_registry.yaml
Test-Path docs\gate8-prompt-config-readiness.md
Test-Path experiments\cards\E013-gate8-prompt-config-readiness.md
Select-String -Path configs\gate8\prompt_registry.yaml,configs\gate8\generation_config_registry.yaml,docs\gate8-prompt-config-readiness.md,experiments\cards\E013-gate8-prompt-config-readiness.md -Pattern 'authorized_to_run: false|prompt_versions_locked: false|generation_config_locked: false|vanilla_rag|ledger_validator|Prohibited'
```

Expected: four `True` lines and matches showing lockout fields plus baseline coverage.

- [ ] **Step 6: Commit Gate 8H metadata docs**

Run:

```powershell
git add configs/gate8/prompt_registry.yaml configs/gate8/generation_config_registry.yaml docs/gate8-prompt-config-readiness.md experiments/cards/E013-gate8-prompt-config-readiness.md
git commit -m "docs: add gate8h prompt config registries"
```

---

### Task 2: Add Prompt Config Readiness Tests First

**Files:**
- Create: `tests/test_gate8_prompt_config_readiness.py`

- [ ] **Step 1: Create failing tests**

Create `tests/test_gate8_prompt_config_readiness.py` with:

```python
import json
import subprocess
import sys
from pathlib import Path

from ledger_rag_gate8.prompt_config_readiness import (
    EXPECTED_BASELINE_FAMILIES,
    build_prompt_config_readiness_summary,
    load_prompt_config_inputs,
    parse_slot_section,
)


ROOT = Path(__file__).resolve().parents[1]
PROMPT_REGISTRY = ROOT / "configs" / "gate8" / "prompt_registry.yaml"
GENERATION_CONFIG = ROOT / "configs" / "gate8" / "generation_config_registry.yaml"
CLI = ROOT / "scripts" / "check_gate8_prompt_config_readiness.py"


def test_registries_cover_all_gate5_baselines():
    inputs = load_prompt_config_inputs(PROMPT_REGISTRY, GENERATION_CONFIG)

    assert {slot["baseline_family"] for slot in inputs.prompt_slots} == EXPECTED_BASELINE_FAMILIES
    assert {slot["baseline_family"] for slot in inputs.generation_slots} == EXPECTED_BASELINE_FAMILIES


def test_default_summary_is_valid_but_not_ready():
    summary = build_prompt_config_readiness_summary(load_prompt_config_inputs(PROMPT_REGISTRY, GENERATION_CONFIG))

    assert summary["gate"] == "gate8_main_comparison"
    assert summary["prompt_config_ready"] is False
    assert summary["authorized_to_run"] is False
    assert summary["missing_prompt_families"] == []
    assert summary["missing_generation_families"] == []
    assert summary["validation_errors"] == []
    assert "prompt_versions_unlocked" in summary["blockers"]
    assert "generation_config_unlocked" in summary["blockers"]
    assert "prompt_registry_not_authorized" in summary["blockers"]
    assert "generation_config_registry_not_authorized" in summary["blockers"]


def test_parse_slot_section_reads_list_of_maps(tmp_path):
    registry = tmp_path / "registry.yaml"
    registry.write_text(
        "\n".join(
            [
                "baseline_prompt_slots:",
                "  - baseline_family: vanilla_rag",
                "    prompt_version: unset",
                "    prompt_status: slot_reserved",
                "  - baseline_family: ledger_validator",
                "    prompt_version: unset",
                "    prompt_status: slot_reserved",
                "blockers:",
                "  - prompt_versions_unlocked",
            ]
        ),
        encoding="utf-8",
    )

    slots = parse_slot_section(registry, "baseline_prompt_slots")

    assert slots == [
        {
            "baseline_family": "vanilla_rag",
            "prompt_version": "unset",
            "prompt_status": "slot_reserved",
        },
        {
            "baseline_family": "ledger_validator",
            "prompt_version": "unset",
            "prompt_status": "slot_reserved",
        },
    ]


def test_missing_baseline_family_is_reported(tmp_path):
    prompt_registry = tmp_path / "prompt.yaml"
    generation_config = tmp_path / "generation.yaml"
    prompt_registry.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8h_prompt_registry_readiness",
                "authorized_to_run: false",
                "prompt_versions_locked: false",
                "baseline_prompt_slots:",
                "  - baseline_family: vanilla_rag",
                "    prompt_version: unset",
                "    prompt_status: slot_reserved",
                "blockers:",
            ]
        ),
        encoding="utf-8",
    )
    generation_config.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8h_generation_config_readiness",
                "authorized_to_run: false",
                "generation_config_locked: false",
                "baseline_generation_slots:",
                "  - baseline_family: vanilla_rag",
                "    generation_config_version: unset",
                "    config_status: slot_reserved",
                "blockers:",
            ]
        ),
        encoding="utf-8",
    )

    summary = build_prompt_config_readiness_summary(load_prompt_config_inputs(prompt_registry, generation_config))

    assert "hybrid_rag" in summary["missing_prompt_families"]
    assert "hybrid_rag" in summary["missing_generation_families"]
    assert "prompt_registry_missing_baselines" in summary["blockers"]
    assert "generation_config_missing_baselines" in summary["blockers"]


def test_cli_default_mode_exits_zero_and_reports_not_ready():
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--prompt-registry",
            str(PROMPT_REGISTRY),
            "--generation-config",
            str(GENERATION_CONFIG),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)

    assert payload["prompt_config_ready"] is False
    assert payload["authorized_to_run"] is False
    assert payload["missing_prompt_families"] == []
    assert payload["missing_generation_families"] == []
    assert payload["blockers"]


def test_cli_require_ready_exits_nonzero_while_blockers_remain():
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--prompt-registry",
            str(PROMPT_REGISTRY),
            "--generation-config",
            str(GENERATION_CONFIG),
            "--require-ready",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["prompt_config_ready"] is False
    assert "prompt_versions_unlocked" in payload["blockers"]
```

- [ ] **Step 2: Run tests to verify they fail before implementation**

Run:

```powershell
python -m pytest tests/test_gate8_prompt_config_readiness.py -v
```

Expected: collection/import failure because `ledger_rag_gate8.prompt_config_readiness` and the CLI do not exist yet.

Do not commit failing tests by themselves.

---

### Task 3: Implement Prompt Config Readiness Checker

**Files:**
- Create: `src/ledger_rag_gate8/prompt_config_readiness.py`
- Create: `scripts/check_gate8_prompt_config_readiness.py`
- Test: `tests/test_gate8_prompt_config_readiness.py`

- [ ] **Step 1: Implement readiness helper**

Create `src/ledger_rag_gate8/prompt_config_readiness.py` with:

```python
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
```

- [ ] **Step 2: Implement CLI**

Create `scripts/check_gate8_prompt_config_readiness.py` with:

```python
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_gate8.prompt_config_readiness import (
    build_prompt_config_readiness_summary,
    load_prompt_config_inputs,
)


def main():
    parser = argparse.ArgumentParser(description="Check Gate 8 prompt/config registry readiness.")
    parser.add_argument("--prompt-registry", required=True, help="Path to prompt_registry.yaml.")
    parser.add_argument("--generation-config", required=True, help="Path to generation_config_registry.yaml.")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit nonzero if Gate 8 prompt/config readiness is blocked.",
    )
    args = parser.parse_args()

    inputs = load_prompt_config_inputs(args.prompt_registry, args.generation_config)
    summary = build_prompt_config_readiness_summary(inputs)
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.require_ready and not summary["prompt_config_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Run prompt/config tests**

Run:

```powershell
python -m pytest tests/test_gate8_prompt_config_readiness.py -v
```

Expected: 6 passed.

- [ ] **Step 4: Run CLI checks manually**

Run:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml --require-ready
```

Expected: first command exits `0` with `"prompt_config_ready": false`; second command exits `1` with blockers.

- [ ] **Step 5: Commit tests and checker**

Run:

```powershell
git add src/ledger_rag_gate8/prompt_config_readiness.py scripts/check_gate8_prompt_config_readiness.py tests/test_gate8_prompt_config_readiness.py
git commit -m "feat: add gate8h prompt config readiness checker"
```

---

### Task 4: Integrate Prompt Config Registries Into Freeze Readiness

**Files:**
- Modify: `configs/gate8/freeze_readiness.yaml`
- Modify: `src/ledger_rag_gate8/freeze_readiness.py`
- Modify: `tests/test_gate8_freeze_readiness.py`
- Test: `tests/test_gate8_prompt_config_readiness.py`

- [ ] **Step 1: Update freeze readiness config references**

In `configs/gate8/freeze_readiness.yaml`, add these fields after `provider_decision`:

```yaml
prompt_registry: configs/gate8/prompt_registry.yaml
generation_config_registry: configs/gate8/generation_config_registry.yaml
```

Add these blockers under `blockers:` if absent:

```yaml
  - prompt_registry_not_locked
  - generation_config_registry_not_locked
```

- [ ] **Step 2: Extend freeze readiness inputs**

In `src/ledger_rag_gate8/freeze_readiness.py`, add `prompt_registry_path`, `generation_config_registry_path`, `prompt_registry`, and `generation_config_registry` to `FreezeInputs`:

```python
@dataclass(frozen=True)
class FreezeInputs:
    freeze_path: Path
    run_matrix_path: Path
    provider_decision_path: Path
    prompt_registry_path: Path
    generation_config_registry_path: Path
    freeze_config: dict
    run_matrix: dict
    provider_decision: dict
    prompt_registry: dict
    generation_config_registry: dict
```

Add `prompt_registry` and `generation_config_registry` to `REQUIRED_FREEZE_FIELDS`.

- [ ] **Step 3: Load optional prompt/config registries**

In `load_freeze_inputs`, load the optional registry references:

```python
prompt_registry_path, prompt_registry = _optional_referenced_config(freeze_config, "prompt_registry")
generation_config_path, generation_config = _optional_referenced_config(
    freeze_config,
    "generation_config_registry",
)

return FreezeInputs(
    freeze_path=freeze_path,
    run_matrix_path=run_matrix_path,
    provider_decision_path=provider_path,
    prompt_registry_path=prompt_registry_path,
    generation_config_registry_path=generation_config_path,
    freeze_config=freeze_config,
    run_matrix=run_matrix,
    provider_decision=provider_decision,
    prompt_registry=prompt_registry,
    generation_config_registry=generation_config,
)
```

- [ ] **Step 4: Add registry blockers to freeze summary**

In `build_freeze_readiness_summary`, after provider decision blockers, add:

```python
prompt_registry = inputs.prompt_registry
generation_config_registry = inputs.generation_config_registry
_add_blocker(
    blockers,
    prompt_registry.get("authorized_to_run") is not True,
    "prompt_registry_not_authorized",
)
_add_blocker(
    blockers,
    prompt_registry.get("prompt_versions_locked") is not True,
    "prompt_registry_not_locked",
)
_add_blocker(
    blockers,
    _has_items(prompt_registry, "blockers"),
    "prompt_registry_has_blockers",
)
_add_blocker(
    blockers,
    generation_config_registry.get("authorized_to_run") is not True,
    "generation_config_registry_not_authorized",
)
_add_blocker(
    blockers,
    generation_config_registry.get("generation_config_locked") is not True,
    "generation_config_registry_not_locked",
)
_add_blocker(
    blockers,
    _has_items(generation_config_registry, "blockers"),
    "generation_config_registry_has_blockers",
)
```

In the `checked_configs` object, add:

```python
"prompt_registry": _summary_path(inputs.prompt_registry_path),
"generation_config_registry": _summary_path(inputs.generation_config_registry_path),
```

- [ ] **Step 5: Update freeze readiness tests**

In `tests/test_gate8_freeze_readiness.py`, update `test_load_freeze_inputs_uses_config_references` with:

```python
assert inputs.freeze_config["prompt_registry"] == "configs/gate8/prompt_registry.yaml"
assert inputs.freeze_config["generation_config_registry"] == "configs/gate8/generation_config_registry.yaml"
assert inputs.prompt_registry["authorized_to_run"] is False
assert inputs.generation_config_registry["authorized_to_run"] is False
```

Update `test_default_summary_is_valid_but_not_ready` with:

```python
assert "prompt_registry_not_locked" in summary["blockers"]
assert "generation_config_registry_not_locked" in summary["blockers"]
assert "prompt_registry_has_blockers" in summary["blockers"]
assert "generation_config_registry_has_blockers" in summary["blockers"]
```

Update `test_summary_reports_checked_config_paths` with:

```python
assert summary["checked_configs"]["prompt_registry"].endswith("configs/gate8/prompt_registry.yaml")
assert summary["checked_configs"]["generation_config_registry"].endswith("configs/gate8/generation_config_registry.yaml")
```

Update `test_missing_reference_paths_report_validation_errors` expected field set to include:

```python
{"run_matrix", "provider_decision", "prompt_registry", "generation_config_registry"}
```

- [ ] **Step 6: Run integration tests**

Run:

```powershell
python -m pytest tests/test_gate8_freeze_readiness.py tests/test_gate8_prompt_config_readiness.py -v
```

Expected: all tests pass.

- [ ] **Step 7: Verify strict freeze remains blocked**

Run:

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml --require-ready
```

Expected: exits `1` and JSON includes `prompt_registry_not_locked` and `generation_config_registry_not_locked`.

- [ ] **Step 8: Commit freeze integration**

Run:

```powershell
git add configs/gate8/freeze_readiness.yaml src/ledger_rag_gate8/freeze_readiness.py tests/test_gate8_freeze_readiness.py
git commit -m "feat: link gate8h registries into freeze readiness"
```

---

### Task 5: Wire Gate 8H Into Project Readiness Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/main-comparison-readiness.md`
- Modify: `configs/gate8/main_v1_readiness.yaml`

- [ ] **Step 1: Update README project structure**

In `README.md`, add these bullets near the Gate 8 docs/config/script bullets:

```markdown
- `docs/gate8-prompt-config-readiness.md` - Gate 8H prompt/config registry rules
- `configs/gate8/prompt_registry.yaml` - non-executable prompt slot registry
- `configs/gate8/generation_config_registry.yaml` - non-executable generation config slot registry
- `scripts/check_gate8_prompt_config_readiness.py` - local prompt/config registry readiness checker
```

- [ ] **Step 2: Update main comparison readiness doc**

In `docs/main-comparison-readiness.md`, add this section after the Gate 8G section and before `## Prohibited Actions In This Layer`:

````markdown
Gate 8H adds prompt and generation config registry readiness checks:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml
```

Strict mode remains blocked until prompt versions, prompt files, shared generation config, provider assumptions, and execution metadata are locked:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml --require-ready
```

This check reserves prompt/config slots only. It does not write final prompt text, select a provider, check live prices, run baselines, compute metrics, create result artifacts, or pass Gate 8.
````

- [ ] **Step 3: Update readiness matrix references**

In `configs/gate8/main_v1_readiness.yaml`, add:

```yaml
prompt_registry: configs/gate8/prompt_registry.yaml
generation_config_registry: configs/gate8/generation_config_registry.yaml
prompt_config_readiness_check:
  command: python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml
  strict_command: python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml --require-ready
  strict_mode_expected_exit_before_prompt_config_freeze: 1
```

Add these blockers to `not_ready` if absent:

```yaml
  - prompt_registry_unlocked
  - generation_config_registry_unlocked
```

Keep `authorized_to_run: false`.

- [ ] **Step 4: Verify docs and metadata references**

Run:

```powershell
Select-String -Path README.md,docs\main-comparison-readiness.md,configs\gate8\main_v1_readiness.yaml -Pattern 'gate8-prompt-config-readiness|prompt_registry.yaml|generation_config_registry.yaml|check_gate8_prompt_config_readiness|prompt_registry_unlocked|generation_config_registry_unlocked'
```

Expected: matches in all three files.

- [ ] **Step 5: Commit wiring docs**

Run:

```powershell
git add README.md docs/main-comparison-readiness.md configs/gate8/main_v1_readiness.yaml
git commit -m "docs: wire gate8h prompt config readiness"
```

---

### Task 6: Final Verification

**Files:**
- Verify all Gate 8H files and existing Gate 8 readiness tests.

- [ ] **Step 1: Verify required files exist**

Run:

```powershell
Test-Path configs\gate8\prompt_registry.yaml
Test-Path configs\gate8\generation_config_registry.yaml
Test-Path docs\gate8-prompt-config-readiness.md
Test-Path experiments\cards\E013-gate8-prompt-config-readiness.md
Test-Path src\ledger_rag_gate8\prompt_config_readiness.py
Test-Path scripts\check_gate8_prompt_config_readiness.py
Test-Path tests\test_gate8_prompt_config_readiness.py
```

Expected: seven `True` lines.

- [ ] **Step 2: Run placeholder and report-link scan**

Run:

```powershell
Select-String -Path docs\*.md,docs\superpowers\*.md,docs\superpowers\*\*.md,experiments\cards\*.md,README.md,configs\gate8\*.yaml,tests\test_gate8_prompt_config_readiness.py,scripts\check_gate8_prompt_config_readiness.py,src\ledger_rag_gate8\*.py -Pattern 'TB[D]|TO[D]O|turn[0-9]+'
```

Expected: no matches.

- [ ] **Step 3: Run Gate 8H and existing Gate 8 tests**

Run:

```powershell
python -m pytest tests/test_gate8_prompt_config_readiness.py tests/test_gate8_freeze_readiness.py tests/test_gate8_snapshot_readiness.py tests/test_gate8_lexical_index.py -v
```

Expected: all tests pass.

- [ ] **Step 4: Verify default prompt/config readiness**

Run:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml
```

Expected: JSON includes `"prompt_config_ready": false`, `"authorized_to_run": false`, empty missing-family lists, and blockers for prompt/config lockout.

- [ ] **Step 5: Verify strict prompt/config readiness remains blocked**

Run:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml --require-ready; if ($LASTEXITCODE -ne 0) { Write-Output "STRICT_PROMPT_CONFIG_EXIT=$LASTEXITCODE"; exit 0 } else { Write-Output "STRICT_PROMPT_CONFIG_EXIT=0" }
```

Expected: JSON reports `"prompt_config_ready": false`, followed by `STRICT_PROMPT_CONFIG_EXIT=1`.

- [ ] **Step 6: Verify strict freeze readiness remains blocked**

Run:

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml --require-ready; if ($LASTEXITCODE -ne 0) { Write-Output "STRICT_FREEZE_EXIT=$LASTEXITCODE"; exit 0 } else { Write-Output "STRICT_FREEZE_EXIT=0" }
```

Expected: JSON reports `"freeze_ready": false`, followed by `STRICT_FREEZE_EXIT=1`.

- [ ] **Step 7: Verify git hygiene**

Run:

```powershell
git diff --check
git status --short --ignored
```

Expected: `git diff --check` exits `0`; git status shows no tracked dirty files after commits and only ignored datasets, artifacts, PDFs, and caches.

---

## Execution Notes

- Do not browse for pricing or model docs in this gate.
- Do not choose a provider or model.
- Do not write final prompt text.
- Do not add API keys or secrets.
- Do not alter `snapshots/main_v1/source_snapshots.json`.
- Do not rebuild retrieval indexes.
- Do not create files under `artifacts/`.
- Do not promote Gate 8 to passed.

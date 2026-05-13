# Gate 8I Provider Evidence Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a provider-evidence registry and readiness checker that keep Gate 8 blocked until official provider/model evidence is recorded and reviewed.

**Architecture:** Gate 8I adds one tracked provider evidence registry, a standard-library-only validator, CLI wrapper, tests, and references from provider-decision and freeze-readiness metadata. The checker only validates local metadata shape and lockout state; it does not browse, fetch URLs, choose a provider, check prices, store secrets, or authorize execution.

**Tech Stack:** Python standard library, YAML-like tracked config parsed with existing local helpers, Markdown, pytest, existing Gate 8 readiness CLI patterns.

---

## File Structure

- Create `configs/gate8/provider_evidence_registry.yaml`: non-executable provider evidence slot registry.
- Create `docs/gate8-provider-evidence-readiness.md`: human-readable Gate 8I scope, evidence slots, and lockout rules.
- Create `experiments/cards/E014-gate8-provider-evidence-readiness.md`: non-running card for the registry/checker work.
- Create `src/ledger_rag_gate8/provider_evidence_readiness.py`: parser and readiness summary builder for provider evidence metadata.
- Create `scripts/check_gate8_provider_evidence_readiness.py`: CLI wrapper that prints JSON and supports strict mode.
- Create `tests/test_gate8_provider_evidence_readiness.py`: tests for required slots, default not-ready state, strict mode, and provider-decision linkage.
- Modify `configs/gate8/provider_decision.yaml`: add provider evidence registry reference while keeping provider/model unset and execution unauthorized.
- Modify `configs/gate8/freeze_readiness.yaml`: add provider evidence registry reference and blockers.
- Modify `src/ledger_rag_gate8/freeze_readiness.py`: load optional provider evidence registry and keep freeze readiness blocked while evidence is incomplete.
- Modify `tests/test_gate8_freeze_readiness.py`: update freeze tests for the provider evidence registry reference.
- Modify `README.md`: list Gate 8I docs/config/script and keep Gate 8 readiness in progress.
- Modify `docs/main-comparison-readiness.md`: reference the provider evidence registry and checker.
- Modify `docs/gate8-freeze-readiness.md`: add provider evidence as a freeze blocker.
- Modify `docs/model-provider-readiness.md`: link the new evidence registry as the next provider decision prerequisite.
- Modify `configs/gate8/main_v1_readiness.yaml`: reference Gate 8I registry/check command and add lockout blockers.

---

### Task 1: Add Gate 8I Registry, Docs, And Card

**Files:**
- Create: `configs/gate8/provider_evidence_registry.yaml`
- Create: `docs/gate8-provider-evidence-readiness.md`
- Create: `experiments/cards/E014-gate8-provider-evidence-readiness.md`

- [ ] **Step 1: Create provider evidence registry**

Create `configs/gate8/provider_evidence_registry.yaml` with:

```yaml
version: 1
gate: gate8_main_comparison
stage: gate8i_provider_evidence_readiness
status: readiness_in_progress
authorized_to_run: false
purpose: non_executable_provider_evidence_registry
provider_evidence_locked: false
provider_selected: false
provider: unset
model: unset

evidence_slots:
  - evidence_id: official_pricing_source
    required_for: cost_budget_and_provider_decision
    official_source_url: unset
    checked_at: unset
    evidence_status: missing
    reviewer: unset
    notes: official_pricing_must_be_checked_on_execution_date
  - evidence_id: official_model_docs_source
    required_for: provider_model_decision
    official_source_url: unset
    checked_at: unset
    evidence_status: missing
    reviewer: unset
    notes: official_model_docs_must_define_model_id_or_version
  - evidence_id: official_terms_privacy_source
    required_for: data_retention_and_terms_review
    official_source_url: unset
    checked_at: unset
    evidence_status: missing
    reviewer: unset
    notes: terms_privacy_or_data_retention_source_required
  - evidence_id: model_id_version_source
    required_for: reproducible_model_config
    official_source_url: unset
    checked_at: unset
    evidence_status: missing
    reviewer: unset
    notes: model_id_version_or_date_must_be_reproducible
  - evidence_id: context_window_source
    required_for: prompt_and_context_budget
    official_source_url: unset
    checked_at: unset
    evidence_status: missing
    reviewer: unset
    notes: context_window_must_come_from_official_docs
  - evidence_id: output_limit_source
    required_for: generation_config_budget
    official_source_url: unset
    checked_at: unset
    evidence_status: missing
    reviewer: unset
    notes: max_output_limit_must_come_from_official_docs
  - evidence_id: rate_limit_or_throughput_source
    required_for: run_scheduling_and_reproducibility
    official_source_url: unset
    checked_at: unset
    evidence_status: missing
    reviewer: unset
    notes: rate_limit_or_local_throughput_note_required
  - evidence_id: api_key_or_runtime_availability_note
    required_for: execution_authorization
    official_source_url: unset
    checked_at: unset
    evidence_status: missing
    reviewer: unset
    notes: do_not_store_api_keys_in_repository
  - evidence_id: cost_budget_approval_note
    required_for: execution_authorization
    official_source_url: unset
    checked_at: unset
    evidence_status: missing
    reviewer: unset
    notes: approved_budget_note_required_before_model_calls

blockers:
  - provider_evidence_not_locked
  - provider_not_selected
  - model_not_selected
  - official_pricing_source_missing
  - official_model_docs_source_missing
  - official_terms_privacy_source_missing
  - model_id_version_source_missing
  - context_window_source_missing
  - output_limit_source_missing
  - rate_limit_or_throughput_source_missing
  - api_key_or_runtime_availability_note_missing
  - cost_budget_approval_note_missing
```

- [ ] **Step 2: Create Gate 8I readiness doc**

Create `docs/gate8-provider-evidence-readiness.md` with:

````markdown
# Gate 8 Provider Evidence Readiness

Gate 8I records the provider and model evidence slots that must be filled before any main comparison model calls can be authorized. It does not select a provider, select a model, check live prices, store API keys, call models, run baselines, compute metrics, create result artifacts, or pass Gate 8.

## Current State

The current registry is intentionally non-executable:

- `authorized_to_run: false`
- `provider_evidence_locked: false`
- `provider_selected: false`
- `provider: unset`
- `model: unset`

Every evidence slot starts with `official_source_url: unset`, `checked_at: unset`, `evidence_status: missing`, and `reviewer: unset`.

## Required Evidence Slots

Gate 8 execution remains blocked until the project records and reviews official evidence for:

- official pricing source
- official model documentation source
- official terms, privacy, or data-retention source
- model id and version source
- context window source
- output limit source
- rate-limit or throughput source
- API key or local runtime availability note
- cost budget approval note

The registry must use official provider sources for provider and model facts. Prices must be checked on the execution date, not copied from reports or old notes.

## CLI Contract

Default mode is inspect-only:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml
````

Strict mode is for execution authorization checks:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --require-ready
```

Strict mode is expected to fail until every evidence slot has an official source URL, check timestamp, reviewed evidence status, reviewer, provider/model selection, and execution approval.
```

- [ ] **Step 3: Create E014 card**

Create `experiments/cards/E014-gate8-provider-evidence-readiness.md` with:

````markdown
# E014 Gate 8 Provider Evidence Readiness

## Purpose

Create a tracked provider evidence registry and local checker for Gate 8 main comparison readiness.

## Execution Status

This is a non-running readiness card. It authorizes metadata validation only.

## Authorized Commands

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --require-ready
````

The strict command is expected to exit nonzero while provider evidence remains incomplete.

## Not Authorized

- live provider documentation lookup
- live pricing lookup
- provider or model selection
- API key storage
- model calls
- embedding calls
- reranker calls
- baseline execution
- metric computation
- result artifact creation

## Success Criteria

- provider evidence registry exists
- provider evidence checker reports missing evidence in default mode
- strict provider evidence checker exits nonzero
- provider decision references the registry but remains unselected
- freeze readiness references the registry and remains blocked
- no provider, model, price, API key, model call, or result artifact is created
```

- [ ] **Step 4: Stage and commit metadata skeleton**

Run:

```powershell
git add configs/gate8/provider_evidence_registry.yaml docs/gate8-provider-evidence-readiness.md experiments/cards/E014-gate8-provider-evidence-readiness.md
git commit -m "docs: add gate8i provider evidence metadata"
```

Expected: commit succeeds with only the registry, doc, and card.

---

### Task 2: Write Provider Evidence Checker Tests First

**Files:**
- Create: `tests/test_gate8_provider_evidence_readiness.py`

- [ ] **Step 1: Create failing tests for registry shape and CLI behavior**

Create `tests/test_gate8_provider_evidence_readiness.py` with:

```python
import json
import subprocess
import sys
from pathlib import Path

from ledger_rag_gate8.provider_evidence_readiness import (
    EXPECTED_EVIDENCE_IDS,
    build_provider_evidence_readiness_summary,
    load_provider_evidence_inputs,
    parse_evidence_slots,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "configs" / "gate8" / "provider_evidence_registry.yaml"
PROVIDER_DECISION = ROOT / "configs" / "gate8" / "provider_decision.yaml"
CLI = ROOT / "scripts" / "check_gate8_provider_evidence_readiness.py"


def test_registry_contains_all_required_evidence_slots():
    inputs = load_provider_evidence_inputs(REGISTRY, PROVIDER_DECISION)

    assert {slot["evidence_id"] for slot in inputs.evidence_slots} == EXPECTED_EVIDENCE_IDS
    assert inputs.registry["authorized_to_run"] is False
    assert inputs.registry["provider_evidence_locked"] is False
    assert inputs.registry["provider_selected"] is False
    assert inputs.registry["provider"] == "unset"
    assert inputs.registry["model"] == "unset"


def test_default_summary_is_valid_but_not_ready():
    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(REGISTRY, PROVIDER_DECISION)
    )

    assert summary["gate"] == "gate8_main_comparison"
    assert summary["stage"] == "gate8i_provider_evidence_readiness"
    assert summary["provider_evidence_ready"] is False
    assert summary["authorized_to_run"] is False
    assert summary["provider_selected"] is False
    assert summary["provider"] == "unset"
    assert summary["model"] == "unset"
    assert summary["missing_evidence_ids"] == sorted(EXPECTED_EVIDENCE_IDS)
    assert summary["unreviewed_evidence_ids"] == sorted(EXPECTED_EVIDENCE_IDS)
    assert summary["validation_errors"] == []
    assert "provider_evidence_not_locked" in summary["blockers"]
    assert "provider_not_selected" in summary["blockers"]
    assert "model_not_selected" in summary["blockers"]


def test_parse_evidence_slots_reads_list_of_maps(tmp_path):
    registry = tmp_path / "provider.yaml"
    registry.write_text(
        "\n".join(
            [
                "evidence_slots:",
                "  - evidence_id: official_pricing_source",
                "    required_for: cost_budget_and_provider_decision",
                "    official_source_url: unset",
                "    checked_at: unset",
                "    evidence_status: missing",
                "    reviewer: unset",
                "    notes: official_pricing_required",
                "  - evidence_id: context_window_source",
                "    required_for: prompt_and_context_budget",
                "    official_source_url: https://example.invalid/docs",
                "    checked_at: 2026-05-13",
                "    evidence_status: reviewed",
                "    reviewer: local_agent",
                "    notes: context_window_recorded",
                "blockers:",
                "  - provider_evidence_not_locked",
            ]
        ),
        encoding="utf-8",
    )

    slots = parse_evidence_slots(registry)

    assert slots == [
        {
            "evidence_id": "official_pricing_source",
            "required_for": "cost_budget_and_provider_decision",
            "official_source_url": "unset",
            "checked_at": "unset",
            "evidence_status": "missing",
            "reviewer": "unset",
            "notes": "official_pricing_required",
        },
        {
            "evidence_id": "context_window_source",
            "required_for": "prompt_and_context_budget",
            "official_source_url": "https://example.invalid/docs",
            "checked_at": "2026-05-13",
            "evidence_status": "reviewed",
            "reviewer": "local_agent",
            "notes": "context_window_recorded",
        },
    ]


def test_missing_evidence_slot_is_reported(tmp_path):
    registry = tmp_path / "provider.yaml"
    provider_decision = tmp_path / "provider_decision.yaml"
    registry.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8i_provider_evidence_readiness",
                "authorized_to_run: false",
                "provider_evidence_locked: false",
                "provider_selected: false",
                "provider: unset",
                "model: unset",
                "evidence_slots:",
                "  - evidence_id: official_pricing_source",
                "    required_for: cost_budget_and_provider_decision",
                "    official_source_url: unset",
                "    checked_at: unset",
                "    evidence_status: missing",
                "    reviewer: unset",
                "    notes: official_pricing_required",
                "blockers:",
            ]
        ),
        encoding="utf-8",
    )
    provider_decision.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8f_provider_readiness",
                "selected: false",
                "provider: unset",
                "model: unset",
                "run_authorized: false",
            ]
        ),
        encoding="utf-8",
    )

    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(registry, provider_decision)
    )

    assert "official_model_docs_source" in summary["missing_evidence_ids"]
    assert "provider_evidence_missing_slots" in summary["blockers"]


def test_provider_decision_references_registry_but_remains_unselected():
    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(REGISTRY, PROVIDER_DECISION)
    )

    assert summary["checked_configs"]["provider_decision"].endswith("configs/gate8/provider_decision.yaml")
    assert summary["provider_decision_selected"] is False
    assert summary["provider_decision_authorized"] is False
    assert "provider_decision_unselected" in summary["blockers"]
    assert "provider_decision_not_authorized" in summary["blockers"]


def test_cli_default_mode_exits_zero_and_reports_not_ready():
    result = subprocess.run(
        [sys.executable, str(CLI), "--registry", str(REGISTRY)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)

    assert payload["provider_evidence_ready"] is False
    assert payload["authorized_to_run"] is False
    assert payload["missing_evidence_ids"] == sorted(EXPECTED_EVIDENCE_IDS)
    assert payload["blockers"]


def test_cli_require_ready_exits_nonzero_while_blockers_remain():
    result = subprocess.run(
        [sys.executable, str(CLI), "--registry", str(REGISTRY), "--require-ready"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["provider_evidence_ready"] is False
    assert "provider_evidence_not_locked" in payload["blockers"]
```

- [ ] **Step 2: Run tests to verify they fail for missing implementation**

Run:

```powershell
python -m pytest tests/test_gate8_provider_evidence_readiness.py -v
```

Expected: FAIL during import because `ledger_rag_gate8.provider_evidence_readiness` does not exist yet.

---

### Task 3: Implement Provider Evidence Checker And CLI

**Files:**
- Create: `src/ledger_rag_gate8/provider_evidence_readiness.py`
- Create: `scripts/check_gate8_provider_evidence_readiness.py`

- [ ] **Step 1: Create provider evidence readiness module**

Create `src/ledger_rag_gate8/provider_evidence_readiness.py` with:

```python
from dataclasses import dataclass
from pathlib import Path

from ledger_rag_gate8.freeze_readiness import load_simple_yaml


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

REQUIRED_REGISTRY_FIELDS = {
    "version",
    "gate",
    "stage",
    "status",
    "authorized_to_run",
    "provider_evidence_locked",
    "provider_selected",
    "provider",
    "model",
}

REQUIRED_PROVIDER_DECISION_FIELDS = {"gate", "stage", "selected", "provider", "model", "run_authorized"}


@dataclass(frozen=True)
class ProviderEvidenceInputs:
    registry_path: Path
    provider_decision_path: Path
    registry: dict
    provider_decision: dict
    evidence_slots: list


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


def parse_evidence_slots(path):
    path = Path(path)
    slots = []
    current = None
    in_section = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()

        if indent == 0 and stripped == "evidence_slots:":
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


def _resolve_repo_path(candidate):
    candidate_path = Path(str(candidate))
    if candidate_path.is_absolute():
        return candidate_path
    return (ROOT / candidate_path).resolve()


def load_provider_evidence_inputs(registry_path, provider_decision_path=None):
    registry = Path(registry_path).resolve()
    registry_data = load_simple_yaml(registry)
    decision = provider_decision_path or registry_data.get(
        "provider_decision",
        "configs/gate8/provider_decision.yaml",
    )
    provider_decision = _resolve_repo_path(decision)
    return ProviderEvidenceInputs(
        registry_path=registry,
        provider_decision_path=provider_decision,
        registry=registry_data,
        provider_decision=load_simple_yaml(provider_decision),
        evidence_slots=parse_evidence_slots(registry),
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


def _summary_path(path):
    path = Path(path)
    if path.is_relative_to(ROOT):
        return path.relative_to(ROOT).as_posix()
    return path.as_posix()


def _slot_ids(slots):
    return {slot.get("evidence_id") for slot in slots if slot.get("evidence_id")}


def _is_missing_slot(slot):
    return (
        slot.get("official_source_url") in {None, "", "unset"}
        or slot.get("checked_at") in {None, "", "unset"}
        or slot.get("evidence_status") != "reviewed"
    )


def _is_unreviewed_slot(slot):
    return slot.get("evidence_status") != "reviewed" or slot.get("reviewer") in {None, "", "unset"}


def build_provider_evidence_readiness_summary(inputs):
    registry = inputs.registry
    provider_decision = inputs.provider_decision
    slot_ids = _slot_ids(inputs.evidence_slots)
    absent_slot_ids = sorted(EXPECTED_EVIDENCE_IDS - slot_ids)
    missing_evidence_ids = sorted(
        set(absent_slot_ids)
        | {
            slot["evidence_id"]
            for slot in inputs.evidence_slots
            if slot.get("evidence_id") in EXPECTED_EVIDENCE_IDS and _is_missing_slot(slot)
        }
    )
    unreviewed_evidence_ids = sorted(
        {
            slot["evidence_id"]
            for slot in inputs.evidence_slots
            if slot.get("evidence_id") in EXPECTED_EVIDENCE_IDS and _is_unreviewed_slot(slot)
        }
        | set(absent_slot_ids)
    )

    validation_errors = []
    validation_errors.extend(_missing_fields(registry, REQUIRED_REGISTRY_FIELDS, "provider_evidence_registry"))
    validation_errors.extend(_missing_fields(provider_decision, REQUIRED_PROVIDER_DECISION_FIELDS, "provider_decision"))

    blockers = list(registry.get("blockers", []))
    if registry.get("authorized_to_run") is not True:
        blockers.append("provider_evidence_registry_not_authorized")
    if registry.get("provider_evidence_locked") is not True:
        blockers.append("provider_evidence_not_locked")
    if registry.get("provider_selected") is not True:
        blockers.append("provider_not_selected")
    if registry.get("provider") == "unset":
        blockers.append("provider_not_selected")
    if registry.get("model") == "unset":
        blockers.append("model_not_selected")
    if absent_slot_ids:
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
    blockers = _dedupe(blockers)

    provider_evidence_ready = not validation_errors and not blockers

    return {
        "gate": registry.get("gate"),
        "stage": registry.get("stage"),
        "status": registry.get("status"),
        "provider_evidence_ready": provider_evidence_ready,
        "authorized_to_run": registry.get("authorized_to_run") is True,
        "provider_selected": registry.get("provider_selected") is True,
        "provider": registry.get("provider"),
        "model": registry.get("model"),
        "provider_decision_selected": provider_decision.get("selected") is True,
        "provider_decision_authorized": provider_decision.get("run_authorized") is True,
        "missing_evidence_ids": missing_evidence_ids,
        "unreviewed_evidence_ids": unreviewed_evidence_ids,
        "evidence_slot_count": len(inputs.evidence_slots),
        "blockers": blockers,
        "checked_configs": {
            "provider_evidence_registry": _summary_path(inputs.registry_path),
            "provider_decision": _summary_path(inputs.provider_decision_path),
        },
        "validation_errors": validation_errors,
    }
```

- [ ] **Step 2: Create CLI wrapper**

Create `scripts/check_gate8_provider_evidence_readiness.py` with:

```python
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_gate8.provider_evidence_readiness import (
    build_provider_evidence_readiness_summary,
    load_provider_evidence_inputs,
)


def main():
    parser = argparse.ArgumentParser(description="Check Gate 8 provider evidence readiness.")
    parser.add_argument(
        "--registry",
        required=True,
        help="Path to configs/gate8/provider_evidence_registry.yaml.",
    )
    parser.add_argument(
        "--provider-decision",
        default=None,
        help="Optional path to configs/gate8/provider_decision.yaml.",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit nonzero if provider evidence readiness is blocked.",
    )
    args = parser.parse_args()

    inputs = load_provider_evidence_inputs(args.registry, args.provider_decision)
    summary = build_provider_evidence_readiness_summary(inputs)
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.require_ready and not summary["provider_evidence_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Run provider evidence tests**

Run:

```powershell
python -m pytest tests/test_gate8_provider_evidence_readiness.py -v
```

Expected: PASS, with default mode not ready and strict mode returning exit code `1`.

- [ ] **Step 4: Stage and commit checker**

Run:

```powershell
git add src/ledger_rag_gate8/provider_evidence_readiness.py scripts/check_gate8_provider_evidence_readiness.py tests/test_gate8_provider_evidence_readiness.py
git commit -m "feat: add gate8i provider evidence checker"
```

Expected: commit succeeds with checker, CLI, and tests.

---

### Task 4: Integrate Provider Evidence Into Provider Decision And Freeze Readiness

**Files:**
- Modify: `configs/gate8/provider_decision.yaml`
- Modify: `configs/gate8/freeze_readiness.yaml`
- Modify: `src/ledger_rag_gate8/freeze_readiness.py`
- Modify: `tests/test_gate8_freeze_readiness.py`

- [ ] **Step 1: Update provider decision metadata**

Modify `configs/gate8/provider_decision.yaml` by inserting this line after `run_authorized: false`:

```yaml
provider_evidence_registry: configs/gate8/provider_evidence_registry.yaml
```

Also append this item under `required_future_evidence:`:

```yaml
  - provider_evidence_registry_locked_and_reviewed
```

Expected: `selected: false`, `provider: unset`, `model: unset`, and `run_authorized: false` remain unchanged.

- [ ] **Step 2: Update freeze readiness config**

Modify `configs/gate8/freeze_readiness.yaml` by inserting this line after `provider_decision: configs/gate8/provider_decision.yaml`:

```yaml
provider_evidence_registry: configs/gate8/provider_evidence_registry.yaml
```

Append these blockers under `blockers:`:

```yaml
  - provider_evidence_not_locked
  - provider_evidence_registry_non_executable
```

- [ ] **Step 3: Extend freeze readiness module**

Modify `src/ledger_rag_gate8/freeze_readiness.py` with these exact structural changes.

Add `provider_evidence_registry` to `REQUIRED_FREEZE_FIELDS`:

```python
    "provider_evidence_registry",
```

Add required provider evidence fields near the provider field constants:

```python
REQUIRED_PROVIDER_EVIDENCE_FIELDS = {
    "gate",
    "stage",
    "authorized_to_run",
    "provider_evidence_locked",
    "provider_selected",
    "provider",
    "model",
}
```

Add `provider_evidence_registry_path` and `provider_evidence_registry` to `FreezeInputs`:

```python
    provider_evidence_registry_path: Path
    provider_evidence_registry: dict
```

In `load_freeze_inputs`, load the new reference after provider decision:

```python
    provider_evidence_path, provider_evidence = _optional_referenced_config(
        freeze_config,
        "provider_evidence_registry",
    )
```

Pass those values into `FreezeInputs`:

```python
        provider_evidence_registry_path=provider_evidence_path,
        provider_evidence_registry=provider_evidence,
```

In `build_freeze_readiness_summary`, assign:

```python
    provider_evidence_registry = inputs.provider_evidence_registry
```

Extend validation:

```python
    validation_errors.extend(
        _missing_fields(provider_evidence_registry, REQUIRED_PROVIDER_EVIDENCE_FIELDS, "provider_evidence_registry")
    )
```

Add blockers before dedupe:

```python
    _add_blocker(
        blockers,
        provider_evidence_registry.get("authorized_to_run") is not True,
        "provider_evidence_registry_not_authorized",
    )
    _add_blocker(
        blockers,
        provider_evidence_registry.get("provider_evidence_locked") is not True,
        "provider_evidence_not_locked",
    )
    _add_blocker(
        blockers,
        provider_evidence_registry.get("provider_selected") is not True,
        "provider_evidence_provider_unselected",
    )
    _add_blocker(
        blockers,
        provider_evidence_registry.get("provider") == "unset",
        "provider_evidence_provider_unset",
    )
    _add_blocker(
        blockers,
        provider_evidence_registry.get("model") == "unset",
        "provider_evidence_model_unset",
    )
    _add_blocker(
        blockers,
        _has_items(provider_evidence_registry, "blockers"),
        "provider_evidence_registry_has_blockers",
    )
```

Add checked config path:

```python
            "provider_evidence_registry": _summary_path(inputs.provider_evidence_registry_path),
```

- [ ] **Step 4: Update freeze readiness tests**

Modify `tests/test_gate8_freeze_readiness.py` with these assertions.

In `test_load_freeze_inputs_uses_config_references`, add:

```python
    assert inputs.freeze_config["provider_evidence_registry"] == "configs/gate8/provider_evidence_registry.yaml"
    assert inputs.provider_evidence_registry["authorized_to_run"] is False
    assert inputs.provider_evidence_registry["provider_evidence_locked"] is False
```

In `test_default_summary_is_valid_but_not_ready`, add:

```python
    assert "provider_evidence_not_locked" in summary["blockers"]
    assert "provider_evidence_registry_not_authorized" in summary["blockers"]
    assert "provider_evidence_registry_has_blockers" in summary["blockers"]
```

In `test_summary_reports_checked_config_paths`, add:

```python
    assert summary["checked_configs"]["provider_evidence_registry"].endswith(
        "configs/gate8/provider_evidence_registry.yaml"
    )
```

In `test_missing_reference_paths_report_validation_errors`, add `provider_evidence_registry` to the expected missing fields:

```python
        "provider_evidence_registry",
```

- [ ] **Step 5: Run freeze and provider evidence tests**

Run:

```powershell
python -m pytest tests/test_gate8_provider_evidence_readiness.py tests/test_gate8_freeze_readiness.py -v
```

Expected: PASS. Freeze readiness remains false.

- [ ] **Step 6: Stage and commit integration**

Run:

```powershell
git add configs/gate8/provider_decision.yaml configs/gate8/freeze_readiness.yaml src/ledger_rag_gate8/freeze_readiness.py tests/test_gate8_freeze_readiness.py
git commit -m "feat: wire gate8i provider evidence into freeze readiness"
```

Expected: commit succeeds and strict freeze readiness remains blocked.

---

### Task 5: Update Readiness Docs And Config References

**Files:**
- Modify: `README.md`
- Modify: `docs/main-comparison-readiness.md`
- Modify: `docs/gate8-freeze-readiness.md`
- Modify: `docs/model-provider-readiness.md`
- Modify: `configs/gate8/main_v1_readiness.yaml`

- [ ] **Step 1: Update README**

In `README.md`, add Gate 8I to the Gate 8 readiness notes with these references:

````markdown
- Gate 8I provider evidence readiness: `docs/gate8-provider-evidence-readiness.md`, `configs/gate8/provider_evidence_registry.yaml`, and `scripts/check_gate8_provider_evidence_readiness.py`.
````

Also ensure the Gate 8 status remains readiness in progress, not completed.

- [ ] **Step 2: Update main comparison readiness doc**

In `docs/main-comparison-readiness.md`, add a section:

```markdown
## Provider Evidence Registry

Gate 8 cannot run until `configs/gate8/provider_evidence_registry.yaml` is locked with official provider evidence for pricing, model documentation, terms or privacy, model id/version, context window, output limits, rate limits or throughput, runtime availability, and approved budget.

Inspect-only check:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml
```

Strict check:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --require-ready
```

Strict mode is expected to fail until a future execution gate records reviewed official evidence and authorizes model calls.
```

- [ ] **Step 3: Update freeze readiness doc**

In `docs/gate8-freeze-readiness.md`, add provider evidence to the freeze blockers:

```markdown
- provider evidence registry is not locked and reviewed
```

Also add the strict provider evidence command:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --require-ready
```

- [ ] **Step 4: Update model provider readiness doc**

In `docs/model-provider-readiness.md`, add:

```markdown
Provider selection remains unset. Gate 8I adds `configs/gate8/provider_evidence_registry.yaml` as the tracked place for official provider evidence, but the registry starts incomplete and non-executable.
```

- [ ] **Step 5: Update main readiness config**

Modify `configs/gate8/main_v1_readiness.yaml` by adding a provider evidence reference in the Gate 8 config/checker area:

```yaml
provider_evidence_registry: configs/gate8/provider_evidence_registry.yaml
provider_evidence_readiness_check: python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml
```

Add blockers:

```yaml
  - provider_evidence_not_locked
  - provider_evidence_registry_non_executable
```

- [ ] **Step 6: Run documentation scan**

Run:

```powershell
Select-String -Path docs\*.md,experiments\cards\*.md,README.md,configs\gate8\*.yaml -Pattern ('TB' + 'D|TO' + 'DO|turn[0-9]+')
```

Expected: no matches.

- [ ] **Step 7: Stage and commit docs/config references**

Run:

```powershell
git add README.md docs/main-comparison-readiness.md docs/gate8-freeze-readiness.md docs/model-provider-readiness.md configs/gate8/main_v1_readiness.yaml
git commit -m "docs: reference gate8i provider evidence readiness"
```

Expected: commit succeeds with docs/config references only.

---

### Task 6: Final Verification

**Files:**
- Verify only; no file edits.

- [ ] **Step 1: Run full relevant test set**

Run:

```powershell
python -m pytest tests/test_gate7_offline_pilot.py tests/test_gate8_snapshot_readiness.py tests/test_gate8_lexical_index.py tests/test_gate8_freeze_readiness.py tests/test_gate8_prompt_config_readiness.py tests/test_gate8_provider_evidence_readiness.py -v
```

Expected: PASS.

- [ ] **Step 2: Run default provider evidence readiness check**

Run:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml
```

Expected: exits `0` and prints JSON with:

```json
{
  "provider_evidence_ready": false,
  "authorized_to_run": false,
  "provider_selected": false
}
```

The actual JSON also includes missing evidence ids, unreviewed evidence ids, blockers, checked configs, and validation errors.

- [ ] **Step 3: Run strict provider evidence readiness check**

Run:

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --require-ready
```

Expected: exits `1` and prints JSON with `provider_evidence_ready: false`.

- [ ] **Step 4: Run strict freeze readiness check**

Run:

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml --require-ready
```

Expected: exits `1` and prints JSON with `freeze_ready: false`.

- [ ] **Step 5: Run placeholder and report-link scan**

Run:

```powershell
Select-String -Path docs\*.md,experiments\cards\*.md,README.md,configs\gate8\*.yaml,snapshots\main_v1\*.json -Pattern ('TB' + 'D|TO' + 'DO|turn[0-9]+')
```

Expected: no matches.

- [ ] **Step 6: Check ignored files and tracked status**

Run:

```powershell
git status --short --ignored
```

Expected: only generated caches, `artifacts/`, `datasets/`, and `literature/papers/*.pdf` are ignored. No tracked file remains unstaged after commits.

- [ ] **Step 7: Record completion state**

If all verification commands match expectations, report that Gate 8I provider evidence readiness is implemented and remains non-executable. Do not claim Gate 8 is passed.

---

## Self-Review

Spec coverage:

- Provider evidence registry is covered in Task 1.
- Standard-library-only validator and CLI are covered in Tasks 2 and 3.
- Provider decision linkage is covered in Task 4.
- Freeze readiness linkage is covered in Task 4.
- Docs, card, README, and main readiness references are covered in Task 5.
- Strict nonzero checks and no-execution boundary are covered in Task 6.

Placeholder scan:

- The plan does not use placeholder markers that match the project scan pattern.
- All code and command steps provide concrete paths, content, commands, and expected results.

Type consistency:

- The registry field names match the parser and tests: `provider_evidence_locked`, `provider_selected`, `provider`, `model`, `evidence_slots`, `blockers`.
- The checker summary fields match CLI tests: `provider_evidence_ready`, `authorized_to_run`, `missing_evidence_ids`, `unreviewed_evidence_ids`, `blockers`, `checked_configs`, `validation_errors`.
- Freeze integration field names match config, dataclass, loader, summary, and tests: `provider_evidence_registry`, `provider_evidence_registry_path`.

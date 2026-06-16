# Gate 8G Freeze Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a standard-library-only Gate 8G execution-preflight validator that keeps provider, prompt, budget, and run authorization locked out until a later execution gate.

**Architecture:** Gate 8G adds one tracked freeze-readiness YAML file, a small parser/checker module, a CLI that emits JSON, focused tests, and docs/card references. It reads existing Gate 8F run matrix and provider decision metadata; it does not write files, select providers, check live prices, call models, or promote Gate 8 to passed.

**Tech Stack:** Python standard library, Markdown, YAML-like tracked config, pytest, existing PowerShell verification commands.

---

## File Structure

- Create `configs/gate8/freeze_readiness.yaml`: execution-preflight metadata with provider, prompt, budget, and authorization fields locked out.
- Create `docs/gate8-freeze-readiness.md`: human-readable Gate 8G boundary and future freeze requirements.
- Create `experiments/cards/E012-gate8-freeze-readiness.md`: non-running card authorizing metadata/tooling only.
- Create `src/ledger_rag_gate8/__init__.py`: package marker for Gate 8 helpers.
- Create `src/ledger_rag_gate8/freeze_readiness.py`: narrow YAML-like parser and freeze readiness summary builder.
- Create `scripts/check_gate8_freeze_readiness.py`: CLI wrapper for the freeze readiness module.
- Create `tests/test_gate8_freeze_readiness.py`: tests for config shape, summary behavior, and CLI exit codes.
- Modify `README.md`: list Gate 8G docs/config/script.
- Modify `docs/main-comparison-readiness.md`: add Gate 8G freeze readiness command and lockout wording.
- Modify `configs/gate8/main_v1_readiness.yaml`: reference freeze readiness config and command while preserving `authorized_to_run: false`.

---

### Task 1: Add Gate 8G Metadata, Docs, And Card

**Files:**
- Create: `configs/gate8/freeze_readiness.yaml`
- Create: `docs/gate8-freeze-readiness.md`
- Create: `experiments/cards/E012-gate8-freeze-readiness.md`

- [ ] **Step 1: Create freeze readiness config**

Create `configs/gate8/freeze_readiness.yaml` with:

```yaml
version: 1
gate: gate8_main_comparison
stage: gate8g_freeze_readiness
status: readiness_in_progress
authorized_to_run: false
purpose: execution_preflight_readiness
run_matrix: configs/gate8/main_v1_run_matrix.yaml
provider_decision: configs/gate8/provider_decision.yaml
source_snapshot_registry: snapshots/main_v1/source_snapshots.json

provider_freeze_selected: false
provider_pricing_checked_on_run_date: false
provider_docs_checked_on_run_date: false
terms_checked_on_run_date: false
api_key_or_runtime_available: false

prompt_versions_locked: false
generation_config_locked: false
prompt_registry: unset
generation_config_registry: unset

cost_budget_approved: false
cost_budget_note: unset

execution_card: unset
reproducibility_review_complete: false
execution_authorized: false

blockers:
  - provider_unselected
  - provider_pricing_not_checked_on_run_date
  - provider_docs_not_checked_on_run_date
  - terms_not_checked_on_run_date
  - api_key_or_runtime_unverified
  - prompt_versions_unlocked
  - generation_config_unlocked
  - cost_budget_unapproved
  - execution_card_missing
  - reproducibility_review_unfinished
  - run_matrix_non_executable
  - provider_decision_non_executable
  - source_snapshots_not_promoted
```

- [ ] **Step 2: Create freeze readiness doc**

Create `docs/gate8-freeze-readiness.md` with:

```markdown
# Gate 8 Freeze Readiness

Gate 8G adds an execution-preflight check for the future main comparison. It does not select a provider, check live prices, finalize prompts, call models, run baselines, compute metrics, create result artifacts, or pass Gate 8.

## Current State

The current Gate 8G metadata keeps execution locked:

- `authorized_to_run: false`
- `provider_freeze_selected: false`
- `prompt_versions_locked: false`
- `generation_config_locked: false`
- `cost_budget_approved: false`
- `execution_authorized: false`

This is intentional. The project now has source snapshots and local lexical indexes, but main execution still needs provider, prompt, budget, and reproducibility decisions.

## Future Freeze Requirements

Before any main baseline command can run, the project must record:

- provider name and model id
- official pricing source checked on the run date
- official model documentation checked on the run date
- terms or data-retention note checked on the run date
- API key or local runtime availability note
- prompt version ids for all comparable baselines
- generation config version id
- approved cost budget note
- execution card with exact commands and output paths
- reproducibility review covering paths, seeds, configs, and ignored artifact destinations

## CLI Contract

The local checker reads:

- `configs/gate8/freeze_readiness.yaml`
- `configs/gate8/main_v1_run_matrix.yaml`
- `configs/gate8/provider_decision.yaml`

Default mode is inspect-only:

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml
```

Strict mode is for execution authorization checks:

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml --require-ready
```

Strict mode is expected to fail until provider, prompt, budget, execution card, and reproducibility metadata are locked.

## Prohibited In Gate 8G

- model calls
- embedding calls
- reranker calls
- provider selection
- price claims without official run-date verification
- prompt finalization
- baseline execution
- metric computation
- result artifact creation
- source snapshot status promotion
- retrieval index rebuilds

Gate 8G exists to make the remaining execution blockers explicit and machine-checkable.
```

- [ ] **Step 3: Create E012 card**

Create `experiments/cards/E012-gate8-freeze-readiness.md` with:

```markdown
# E012 Gate 8 Freeze Readiness

## Purpose

Create a local execution-preflight readiness check for provider, prompt, budget, and run authorization metadata. This card authorizes metadata and validation tooling only.

## Authorized Scope

- create `configs/gate8/freeze_readiness.yaml`
- create `docs/gate8-freeze-readiness.md`
- create `scripts/check_gate8_freeze_readiness.py`
- create standard-library-only readiness helper code
- add tests for default and strict readiness behavior
- update README and Gate 8 readiness references

## Prohibited Actions

- model calls
- embedding calls
- reranker calls
- provider selection
- live pricing claims
- prompt finalization
- baseline execution
- retrieval evaluation
- metric computation
- result artifact creation
- source snapshot status promotion to `ready`

## Expected Outputs

- `configs/gate8/freeze_readiness.yaml`
- `docs/gate8-freeze-readiness.md`
- `src/ledger_rag_gate8/freeze_readiness.py`
- `scripts/check_gate8_freeze_readiness.py`
- `tests/test_gate8_freeze_readiness.py`
- README and readiness doc references

## Success Criteria

- default freeze readiness command exits `0`
- default freeze readiness output reports `freeze_ready: false`
- strict freeze readiness command exits nonzero
- blockers include provider, prompt, budget, execution, run matrix, and provider decision lockouts
- no datasets, indexes, model calls, provider calls, or result artifacts are created

## Cost Class

Local metadata and tests only. No model, API, provider, or cloud cost is authorized.
```

- [ ] **Step 4: Verify metadata/docs/card**

Run:

```powershell
Test-Path configs\gate8\freeze_readiness.yaml
Test-Path docs\gate8-freeze-readiness.md
Test-Path experiments\cards\E012-gate8-freeze-readiness.md
Select-String -Path configs\gate8\freeze_readiness.yaml,docs\gate8-freeze-readiness.md,experiments\cards\E012-gate8-freeze-readiness.md -Pattern 'authorized_to_run: false|provider_freeze_selected: false|prompt_versions_locked: false|cost_budget_approved: false|execution_authorized: false|Prohibited'
```

Expected: three `True` lines and matches showing execution remains locked.

- [ ] **Step 5: Commit Gate 8G metadata docs**

Run:

```powershell
git add configs/gate8/freeze_readiness.yaml docs/gate8-freeze-readiness.md experiments/cards/E012-gate8-freeze-readiness.md
git commit -m "docs: add gate8g freeze readiness metadata"
```

---

### Task 2: Add Freeze Readiness Tests First

**Files:**
- Create: `tests/test_gate8_freeze_readiness.py`

- [ ] **Step 1: Create failing tests**

Create `tests/test_gate8_freeze_readiness.py` with:

```python
import json
import subprocess
import sys
from pathlib import Path

from ledger_rag_gate8.freeze_readiness import (
    REQUIRED_FREEZE_FIELDS,
    build_freeze_readiness_summary,
    load_freeze_inputs,
    load_simple_yaml,
)


ROOT = Path(__file__).resolve().parents[1]
FREEZE_CONFIG = ROOT / "configs" / "gate8" / "freeze_readiness.yaml"
RUN_MATRIX = ROOT / "configs" / "gate8" / "main_v1_run_matrix.yaml"
PROVIDER_DECISION = ROOT / "configs" / "gate8" / "provider_decision.yaml"
CLI = ROOT / "scripts" / "check_gate8_freeze_readiness.py"


def test_freeze_config_has_required_fields():
    config = load_simple_yaml(FREEZE_CONFIG)

    assert REQUIRED_FREEZE_FIELDS <= set(config)
    assert config["authorized_to_run"] is False
    assert config["provider_freeze_selected"] is False
    assert config["prompt_versions_locked"] is False
    assert config["cost_budget_approved"] is False
    assert config["execution_authorized"] is False


def test_load_freeze_inputs_uses_config_references():
    inputs = load_freeze_inputs(FREEZE_CONFIG)

    assert inputs.freeze_config["run_matrix"] == "configs/gate8/main_v1_run_matrix.yaml"
    assert inputs.freeze_config["provider_decision"] == "configs/gate8/provider_decision.yaml"
    assert inputs.run_matrix["authorized_to_run"] is False
    assert inputs.provider_decision["selected"] is False
    assert inputs.provider_decision["run_authorized"] is False


def test_default_summary_is_valid_but_not_ready():
    inputs = load_freeze_inputs(FREEZE_CONFIG)
    summary = build_freeze_readiness_summary(inputs)

    assert summary["gate"] == "gate8_main_comparison"
    assert summary["stage"] == "gate8g_freeze_readiness"
    assert summary["freeze_ready"] is False
    assert summary["authorized_to_run"] is False
    assert summary["validation_errors"] == []
    assert "provider_unselected" in summary["blockers"]
    assert "prompt_versions_unlocked" in summary["blockers"]
    assert "cost_budget_unapproved" in summary["blockers"]
    assert "run_matrix_not_authorized" in summary["blockers"]
    assert "provider_decision_not_authorized" in summary["blockers"]


def test_summary_reports_checked_config_paths():
    inputs = load_freeze_inputs(FREEZE_CONFIG)
    summary = build_freeze_readiness_summary(inputs)

    assert summary["checked_configs"]["freeze_config"].endswith("configs/gate8/freeze_readiness.yaml")
    assert summary["checked_configs"]["run_matrix"].endswith("configs/gate8/main_v1_run_matrix.yaml")
    assert summary["checked_configs"]["provider_decision"].endswith("configs/gate8/provider_decision.yaml")


def test_simple_yaml_parser_reads_top_level_scalars_and_lists(tmp_path):
    config = tmp_path / "sample.yaml"
    config.write_text(
        "\n".join(
            [
                "enabled: false",
                "name: unset",
                "count: 3",
                "blockers:",
                "  - first_blocker",
                "  - second_blocker",
                "nested:",
                "  child: ignored",
            ]
        ),
        encoding="utf-8",
    )

    parsed = load_simple_yaml(config)

    assert parsed["enabled"] is False
    assert parsed["name"] == "unset"
    assert parsed["count"] == 3
    assert parsed["blockers"] == ["first_blocker", "second_blocker"]
    assert parsed["nested"] == []


def test_cli_default_mode_exits_zero_and_reports_not_ready():
    result = subprocess.run(
        [sys.executable, str(CLI), "--freeze-config", str(FREEZE_CONFIG)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)

    assert payload["freeze_ready"] is False
    assert payload["authorized_to_run"] is False
    assert payload["validation_errors"] == []
    assert payload["blockers"]


def test_cli_require_ready_exits_nonzero_while_blockers_remain():
    result = subprocess.run(
        [sys.executable, str(CLI), "--freeze-config", str(FREEZE_CONFIG), "--require-ready"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["freeze_ready"] is False
    assert "provider_unselected" in payload["blockers"]
```

- [ ] **Step 2: Run tests to verify they fail before implementation**

Run:

```powershell
python -m pytest tests/test_gate8_freeze_readiness.py -v
```

Expected: collection/import failure because `ledger_rag_gate8.freeze_readiness` and the CLI do not exist yet.

Do not commit failing tests by themselves.

---

### Task 3: Implement Freeze Readiness Module And CLI

**Files:**
- Create: `src/ledger_rag_gate8/__init__.py`
- Create: `src/ledger_rag_gate8/freeze_readiness.py`
- Create: `scripts/check_gate8_freeze_readiness.py`
- Test: `tests/test_gate8_freeze_readiness.py`

- [ ] **Step 1: Create package marker**

Create `src/ledger_rag_gate8/__init__.py` with:

```python
"""Gate 8 readiness helpers for the Ledger-RAG project."""
```

- [ ] **Step 2: Implement freeze readiness helper**

Create `src/ledger_rag_gate8/freeze_readiness.py` with:

```python
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
            "freeze_config": str(inputs.freeze_path.relative_to(ROOT)),
            "run_matrix": str(inputs.run_matrix_path.relative_to(ROOT)),
            "provider_decision": str(inputs.provider_decision_path.relative_to(ROOT)),
        },
        "validation_errors": validation_errors,
    }
```

- [ ] **Step 3: Implement CLI**

Create `scripts/check_gate8_freeze_readiness.py` with:

```python
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_gate8.freeze_readiness import build_freeze_readiness_summary, load_freeze_inputs


def main():
    parser = argparse.ArgumentParser(description="Check Gate 8 freeze readiness.")
    parser.add_argument(
        "--freeze-config",
        required=True,
        help="Path to configs/gate8/freeze_readiness.yaml.",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit nonzero if Gate 8 freeze readiness is blocked.",
    )
    args = parser.parse_args()

    inputs = load_freeze_inputs(args.freeze_config)
    summary = build_freeze_readiness_summary(inputs)
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.require_ready and not summary["freeze_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run freeze readiness tests**

Run:

```powershell
python -m pytest tests/test_gate8_freeze_readiness.py -v
```

Expected: 7 passed.

- [ ] **Step 5: Run CLI checks manually**

Run:

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml --require-ready
```

Expected: first command exits `0` with `"freeze_ready": false`; second command exits `1` with blockers.

- [ ] **Step 6: Commit tests and implementation**

Run:

```powershell
git add src/ledger_rag_gate8/__init__.py src/ledger_rag_gate8/freeze_readiness.py scripts/check_gate8_freeze_readiness.py tests/test_gate8_freeze_readiness.py
git commit -m "feat: add gate8g freeze readiness checker"
```

---

### Task 4: Wire Gate 8G Into Project Readiness Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/main-comparison-readiness.md`
- Modify: `configs/gate8/main_v1_readiness.yaml`

- [ ] **Step 1: Update README project structure**

In `README.md`, add these bullets near the existing Gate 8 docs/config/script bullets:

```markdown
- `docs/gate8-freeze-readiness.md` - Gate 8G provider, prompt, budget, and execution freeze rules
- `configs/gate8/freeze_readiness.yaml` - non-executable freeze readiness metadata
- `scripts/check_gate8_freeze_readiness.py` - local execution-preflight readiness checker
```

- [ ] **Step 2: Update main comparison readiness doc**

In `docs/main-comparison-readiness.md`, add this section after the Gate 8F paragraph and before `## Prohibited Actions In This Layer`:

````markdown
Gate 8G adds an execution-preflight freeze readiness check:

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml
```

Strict mode remains blocked until provider, prompt, budget, execution card, and reproducibility metadata are locked:

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml --require-ready
```

This check is metadata-only. It does not select a provider, check live prices, write prompts, run baselines, compute metrics, create result artifacts, or pass Gate 8.
````

- [ ] **Step 3: Update readiness matrix references**

In `configs/gate8/main_v1_readiness.yaml`, add these top-level entries near the existing `run_matrix` and `provider_decision` entries:

```yaml
freeze_readiness: configs/gate8/freeze_readiness.yaml
freeze_readiness_check:
  command: python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml
  strict_command: python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml --require-ready
  strict_mode_expected_exit_before_freeze: 1
```

Add these blockers to `not_ready` if absent:

```yaml
  - freeze_readiness_unlocked
  - provider_prompt_budget_not_frozen
```

Keep `authorized_to_run: false`.

- [ ] **Step 4: Verify docs and metadata references**

Run:

```powershell
Select-String -Path README.md,docs\main-comparison-readiness.md,configs\gate8\main_v1_readiness.yaml -Pattern 'gate8-freeze-readiness|freeze_readiness.yaml|check_gate8_freeze_readiness|freeze_readiness_unlocked|provider_prompt_budget_not_frozen'
```

Expected: matches in all three files.

- [ ] **Step 5: Commit wiring docs**

Run:

```powershell
git add README.md docs/main-comparison-readiness.md configs/gate8/main_v1_readiness.yaml
git commit -m "docs: wire gate8g freeze readiness"
```

---

### Task 5: Final Verification

**Files:**
- Verify all Gate 8G files and existing Gate 8 readiness tests.

- [ ] **Step 1: Verify required files exist**

Run:

```powershell
Test-Path configs\gate8\freeze_readiness.yaml
Test-Path docs\gate8-freeze-readiness.md
Test-Path experiments\cards\E012-gate8-freeze-readiness.md
Test-Path src\ledger_rag_gate8\freeze_readiness.py
Test-Path scripts\check_gate8_freeze_readiness.py
Test-Path tests\test_gate8_freeze_readiness.py
```

Expected: six `True` lines.

- [ ] **Step 2: Run placeholder and report-link scan**

Run:

```powershell
Select-String -Path docs\*.md,docs\superpowers\*.md,docs\superpowers\*\*.md,experiments\cards\*.md,README.md,configs\gate8\*.yaml,tests\test_gate8_freeze_readiness.py,scripts\check_gate8_freeze_readiness.py,src\ledger_rag_gate8\*.py -Pattern 'TB[D]|TO[D]O|turn[0-9]+'
```

Expected: no matches.

- [ ] **Step 3: Run Gate 8G tests and existing Gate 8 readiness tests**

Run:

```powershell
python -m pytest tests/test_gate8_freeze_readiness.py tests/test_gate8_snapshot_readiness.py tests/test_gate8_lexical_index.py -v
```

Expected: all tests pass.

- [ ] **Step 4: Verify default freeze readiness output**

Run:

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml
```

Expected: JSON includes `"freeze_ready": false`, `"authorized_to_run": false`, and blockers for provider, prompt, budget, execution, run matrix, and provider decision.

- [ ] **Step 5: Verify strict freeze readiness remains blocked**

Run:

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml --require-ready; if ($LASTEXITCODE -ne 0) { Write-Output "STRICT_FREEZE_EXIT=$LASTEXITCODE"; exit 0 } else { Write-Output "STRICT_FREEZE_EXIT=0" }
```

Expected: JSON reports `"freeze_ready": false`, followed by `STRICT_FREEZE_EXIT=1`.

- [ ] **Step 6: Verify source snapshot readiness remains not passed**

Run:

```powershell
python scripts/check_gate8_snapshot_readiness.py --registry snapshots/main_v1/source_snapshots.json
```

Expected: JSON reports `"gate8_ready": false` and `source_ready_count` remains `3`.

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
- Do not add API keys or secrets.
- Do not alter `snapshots/main_v1/source_snapshots.json`.
- Do not rebuild retrieval indexes.
- Do not create files under `artifacts/`.
- Do not promote Gate 8 to passed.

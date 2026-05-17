# Gate 8M Provider Budget Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add non-executable provider and budget preflight metadata for GPT-5.4 and DeepSeek-V4-Pro so the project can decide a smoke-run provider later without accidentally authorizing API calls.

**Architecture:** Add separate provider candidate and budget config files, plus a stdlib-only checker that validates candidate shape and budget scope. Keep this independent from the existing Gate 8K provider evidence checker so OpenAI candidate evidence remains intact while Gate 8M compares two providers and confirms execution remains blocked.

**Tech Stack:** Python standard library, existing simple YAML parsing helpers, YAML-like config files, Markdown docs, pytest.

---

## File Structure

- Create `configs/gate8/provider_candidates.yaml`: two provider candidates, both non-executable.
- Create `configs/gate8/budget_preflight.yaml`: smoke and main budget scope, no execution authorization.
- Create `src/ledger_rag_gate8/provider_budget_preflight.py`: loader, candidate parser, budget parser, readiness summary.
- Create `scripts/check_gate8_provider_budget_preflight.py`: CLI wrapper with default and strict modes.
- Create `tests/test_gate8_provider_budget_preflight.py`: fixture and CLI coverage.
- Create `docs/gate8-provider-comparison.md`: human-readable GPT-5.4 vs DeepSeek-V4-Pro comparison.
- Create `experiments/cards/E018-gate8m-provider-budget-preflight.md`: non-running readiness card.
- Modify `configs/gate8/main_v1_readiness.yaml`: reference new configs and checker.
- Modify `README.md`: mention Gate 8M provider/budget preflight state.

## Task 1: Write Failing Provider Budget Tests

**Files:**
- Create: `tests/test_gate8_provider_budget_preflight.py`

- [ ] **Step 1: Add test file with expected public API**

Create `tests/test_gate8_provider_budget_preflight.py` with:

```python
import json
import subprocess
import sys
from pathlib import Path

from ledger_rag_gate8.provider_budget_preflight import (
    EXPECTED_PROVIDER_IDS,
    build_provider_budget_preflight_summary,
    load_provider_budget_preflight_inputs,
    parse_budget_lists,
    parse_provider_candidates,
)


ROOT = Path(__file__).resolve().parents[1]
PROVIDER_CANDIDATES = ROOT / "configs" / "gate8" / "provider_candidates.yaml"
BUDGET_PREFLIGHT = ROOT / "configs" / "gate8" / "budget_preflight.yaml"
CLI = ROOT / "scripts" / "check_gate8_provider_budget_preflight.py"


def test_provider_candidates_contain_expected_models():
    inputs = load_provider_budget_preflight_inputs(PROVIDER_CANDIDATES, BUDGET_PREFLIGHT)

    assert {candidate["id"] for candidate in inputs.provider_candidates} == EXPECTED_PROVIDER_IDS
    assert all(candidate["candidate_locked"] is True for candidate in inputs.provider_candidates)
    assert all(candidate["final_selected"] is False for candidate in inputs.provider_candidates)
    assert all(candidate["authorized_to_run"] is False for candidate in inputs.provider_candidates)


def test_default_summary_reports_preflight_ready_but_execution_blocked():
    summary = build_provider_budget_preflight_summary(
        load_provider_budget_preflight_inputs(PROVIDER_CANDIDATES, BUDGET_PREFLIGHT)
    )

    assert summary["gate"] == "gate8_main_comparison"
    assert summary["provider_budget_preflight_ready"] is True
    assert summary["execution_authorized"] is False
    assert summary["selected_provider"] == "unset"
    assert summary["candidate_ids"] == ["deepseek_v4_pro", "openai_gpt_5_4"]
    assert summary["candidate_blockers"] == []
    assert "execution_not_authorized" in summary["execution_blockers"]


def test_budget_preflight_has_smoke_budget_and_deferred_main_budget():
    inputs = load_provider_budget_preflight_inputs(PROVIDER_CANDIDATES, BUDGET_PREFLIGHT)

    assert inputs.budget_preflight["smoke_run_budget_usd"] == 10
    assert inputs.budget_preflight["main_run_budget_usd"] == "unset_requires_later_approval"
    assert inputs.budget_preflight["retry_buffer_fraction"] == "0.30"
    assert inputs.budget_includes
    assert inputs.budget_excludes


def test_parse_provider_candidates_reads_list_of_maps(tmp_path):
    path = tmp_path / "provider_candidates.yaml"
    path.write_text(
        "\n".join(
            [
                "provider_candidates:",
                "  - id: openai_gpt_5_4",
                "    provider: openai",
                "    model: gpt-5.4",
                "    candidate_locked: true",
                "    final_selected: false",
                "    authorized_to_run: false",
                "  - id: deepseek_v4_pro",
                "    provider: deepseek",
                "    model: deepseek-v4-pro",
                "    candidate_locked: true",
                "    final_selected: false",
                "    authorized_to_run: false",
            ]
        ),
        encoding="utf-8",
    )

    candidates = parse_provider_candidates(path)

    assert candidates == [
        {
            "id": "openai_gpt_5_4",
            "provider": "openai",
            "model": "gpt-5.4",
            "candidate_locked": True,
            "final_selected": False,
            "authorized_to_run": False,
        },
        {
            "id": "deepseek_v4_pro",
            "provider": "deepseek",
            "model": "deepseek-v4-pro",
            "candidate_locked": True,
            "final_selected": False,
            "authorized_to_run": False,
        },
    ]


def test_parse_budget_lists_reads_include_exclude_sections(tmp_path):
    path = tmp_path / "budget_preflight.yaml"
    path.write_text(
        "\n".join(
            [
                "budget_includes:",
                "  - generator_input_tokens",
                "  - verifier_output_tokens",
                "budget_excludes:",
                "  - local_lexical_index_construction",
            ]
        ),
        encoding="utf-8",
    )

    includes, excludes = parse_budget_lists(path)

    assert includes == ["generator_input_tokens", "verifier_output_tokens"]
    assert excludes == ["local_lexical_index_construction"]


def test_accidental_candidate_authorization_blocks_preflight(tmp_path):
    candidates = tmp_path / "provider_candidates.yaml"
    budget = tmp_path / "budget_preflight.yaml"
    candidates.write_text(PROVIDER_CANDIDATES.read_text(encoding="utf-8").replace("authorized_to_run: false", "authorized_to_run: true", 1), encoding="utf-8")
    budget.write_text(BUDGET_PREFLIGHT.read_text(encoding="utf-8"), encoding="utf-8")

    summary = build_provider_budget_preflight_summary(load_provider_budget_preflight_inputs(candidates, budget))

    assert summary["provider_budget_preflight_ready"] is False
    assert "candidate_authorized_openai_gpt_5_4" in summary["candidate_blockers"]


def test_cli_default_mode_exits_zero_and_reports_preflight_ready():
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--provider-candidates",
            str(PROVIDER_CANDIDATES),
            "--budget-preflight",
            str(BUDGET_PREFLIGHT),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)

    assert payload["provider_budget_preflight_ready"] is True
    assert payload["execution_authorized"] is False
    assert payload["selected_provider"] == "unset"


def test_cli_require_ready_exits_nonzero_while_execution_is_blocked():
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--provider-candidates",
            str(PROVIDER_CANDIDATES),
            "--budget-preflight",
            str(BUDGET_PREFLIGHT),
            "--require-ready",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["provider_budget_preflight_ready"] is True
    assert payload["execution_authorized"] is False
```

- [ ] **Step 2: Run tests and verify expected failure**

Run:

```powershell
python -m pytest tests/test_gate8_provider_budget_preflight.py -v
```

Expected: collection fails because `ledger_rag_gate8.provider_budget_preflight` does not exist.

## Task 2: Add Provider and Budget Configs

**Files:**
- Create: `configs/gate8/provider_candidates.yaml`
- Create: `configs/gate8/budget_preflight.yaml`

- [ ] **Step 1: Add provider candidates config**

Create `configs/gate8/provider_candidates.yaml`:

```yaml
version: 1
gate: gate8_main_comparison
stage: gate8m_provider_budget_preflight
status: readiness_in_progress
authorized_to_run: false
purpose: non_executable_dual_provider_candidate_registry
selected_provider: unset
execution_authorized: false
pricing_recheck_required_on_run_date: true

provider_candidates:
  - id: openai_gpt_5_4
    provider: openai
    model: gpt-5.4
    candidate_locked: true
    final_selected: false
    authorized_to_run: false
    official_model_url: https://openai.com/index/introducing-gpt-5-4/
    official_pricing_url: https://openai.com/index/introducing-gpt-5-4/
    pricing_checked_at: 2026-05-17
    input_usd_per_1m_tokens: 2.50
    cached_input_usd_per_1m_tokens: 0.25
    output_usd_per_1m_tokens: 15.00
    context_window_note: standard_api_context_must_be_rechecked_before_run
    max_output_note: model_output_limit_must_be_rechecked_before_run
    json_output_support: expected_supported_recheck_before_run
    tool_call_support: expected_supported_recheck_before_run
    terms_or_data_policy_note: official_terms_and_data_policy_must_be_rechecked_before_run
    risk_notes: higher_cost_better_credibility_candidate
    recommended_role: small_sample_credibility_comparison
  - id: deepseek_v4_pro
    provider: deepseek
    model: deepseek-v4-pro
    candidate_locked: true
    final_selected: false
    authorized_to_run: false
    official_model_url: https://api-docs.deepseek.com/quick_start/pricing
    official_pricing_url: https://api-docs.deepseek.com/quick_start/pricing
    pricing_checked_at: 2026-05-17
    input_usd_per_1m_tokens: 0.435
    cached_input_usd_per_1m_tokens: 0.003625
    output_usd_per_1m_tokens: 0.87
    context_window_note: one_million_tokens_reported_by_official_pricing_page_recheck_before_run
    max_output_note: three_hundred_eighty_four_thousand_tokens_reported_by_official_pricing_page_recheck_before_run
    json_output_support: official_pricing_page_marks_supported_recheck_before_run
    tool_call_support: official_pricing_page_marks_supported_recheck_before_run
    terms_or_data_policy_note: official_terms_and_data_policy_must_be_rechecked_before_run
    risk_notes: discounted_price_window_and_provider_external_validity_require_reporting
    recommended_role: cost_controlled_smoke_and_possible_main_candidate

blockers:
  - selected_provider_unset
  - execution_not_authorized
  - api_key_or_runtime_unverified
  - run_date_pricing_not_rechecked
```

- [ ] **Step 2: Add budget preflight config**

Create `configs/gate8/budget_preflight.yaml`:

```yaml
version: 1
gate: gate8_main_comparison
stage: gate8m_budget_preflight
status: readiness_in_progress
authorized_to_run: false
execution_authorized: false
currency: USD
smoke_run_budget_usd: 10
main_run_budget_usd: unset_requires_later_approval
retry_buffer_fraction: 0.30
budget_owner_approval: pending
pricing_recheck_required_on_run_date: true

budget_includes:
  - generator_input_tokens
  - generator_output_tokens
  - verifier_input_tokens
  - verifier_output_tokens
  - repeated_calls_across_six_baseline_families
  - retry_calls
  - json_repair_calls
  - provider_tool_costs_if_enabled_later

budget_excludes:
  - local_lexical_retrieval_index_construction
  - local_dataset_source_snapshots
  - local_result_storage
  - literature_pdfs
  - project_docs
  - ignored_local_caches

blockers:
  - main_run_budget_unapproved
  - selected_provider_unset
  - execution_not_authorized
  - run_date_pricing_not_rechecked
  - api_key_or_runtime_unverified
```

- [ ] **Step 3: Run tests again**

Run:

```powershell
python -m pytest tests/test_gate8_provider_budget_preflight.py -v
```

Expected: still fails because implementation module and CLI are missing.

## Task 3: Implement Provider Budget Preflight Module

**Files:**
- Create: `src/ledger_rag_gate8/provider_budget_preflight.py`

- [ ] **Step 1: Add module implementation**

Create `src/ledger_rag_gate8/provider_budget_preflight.py`:

```python
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


def _candidate_blockers(candidates):
    blockers = []
    ids = {candidate.get("id") for candidate in candidates if candidate.get("id")}
    missing_ids = EXPECTED_PROVIDER_IDS - ids
    extra_ids = ids - EXPECTED_PROVIDER_IDS
    if missing_ids:
        blockers.append("provider_candidates_missing_expected_ids")
    if extra_ids:
        blockers.append("provider_candidates_have_unexpected_ids")

    final_selected_count = 0
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
    candidate_blockers = _candidate_blockers(inputs.provider_candidates)
    budget_blockers = _budget_blockers(budget, inputs.budget_includes, inputs.budget_excludes)
    execution_blockers = []
    selected_provider = provider_registry.get("selected_provider", "unset")
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
```

- [ ] **Step 2: Run focused tests**

Run:

```powershell
python -m pytest tests/test_gate8_provider_budget_preflight.py -v
```

Expected: CLI tests fail because script is missing; module-level tests should pass if configs were created.

## Task 4: Add CLI Wrapper

**Files:**
- Create: `scripts/check_gate8_provider_budget_preflight.py`

- [ ] **Step 1: Add CLI script**

Create `scripts/check_gate8_provider_budget_preflight.py`:

```python
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ledger_rag_gate8.provider_budget_preflight import (
    build_provider_budget_preflight_summary,
    load_provider_budget_preflight_inputs,
)


def main():
    parser = argparse.ArgumentParser(description="Check Gate 8 provider/budget preflight readiness.")
    parser.add_argument("--provider-candidates", required=True, help="Path to provider_candidates.yaml.")
    parser.add_argument("--budget-preflight", required=True, help="Path to budget_preflight.yaml.")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit nonzero unless execution is authorized as well as preflight-valid.",
    )
    args = parser.parse_args()

    inputs = load_provider_budget_preflight_inputs(args.provider_candidates, args.budget_preflight)
    summary = build_provider_budget_preflight_summary(inputs)
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.require_ready and not summary["execution_authorized"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run focused tests**

Run:

```powershell
python -m pytest tests/test_gate8_provider_budget_preflight.py -v
```

Expected: all tests in this file pass.

## Task 5: Add Docs, Card, and Readiness References

**Files:**
- Create: `docs/gate8-provider-comparison.md`
- Create: `experiments/cards/E018-gate8m-provider-budget-preflight.md`
- Modify: `configs/gate8/main_v1_readiness.yaml`
- Modify: `README.md`

- [ ] **Step 1: Add provider comparison doc**

Create `docs/gate8-provider-comparison.md`:

```markdown
# Gate 8 Provider Comparison

Gate 8M compares provider candidates for later smoke and main runs. It does not select a final provider, authorize API calls, or pass Gate 8.

## Candidates

| Candidate | Role | Cost profile | Main risk |
| --- | --- | --- | --- |
| OpenAI GPT-5.4 | small-sample credibility comparison | higher cost | full-run cost can grow quickly |
| DeepSeek-V4-Pro | cost-controlled smoke and possible main run | lower current listed cost | discounted pricing and output behavior must be checked before execution |

## Budget Interpretation

The budget includes generator tokens, verifier tokens, repeated calls across six baseline families, retry calls, JSON repair calls, and provider tool costs if a later gate enables tools.

The budget excludes local lexical retrieval index construction, local source snapshots, local result storage, literature PDFs, project docs, and ignored local caches.

## Current Recommendation

Use DeepSeek-V4-Pro as the first smoke-run candidate because it is cheaper and can test JSON, citation, and verifier behavior at low cost. Use GPT-5.4 later as a small-sample credibility comparison if the DeepSeek smoke run is stable.

## Execution Boundary

Provider choice affects external validity and must be reported with all results. Pricing, model limits, terms, and API/runtime availability must be rechecked on the actual run date. No provider is authorized for execution by this document.
```

- [ ] **Step 2: Add non-running experiment card**

Create `experiments/cards/E018-gate8m-provider-budget-preflight.md`:

```markdown
# E018 Gate 8M Provider Budget Preflight

## Status

Non-running readiness card. This card does not authorize API calls, model output generation, dataset downloads, baseline runs, or result artifacts.

## Purpose

Validate that GPT-5.4 and DeepSeek-V4-Pro provider candidates plus the initial smoke-run budget are recorded before a later execution gate.

## Scope

- Provider candidates: OpenAI GPT-5.4 and DeepSeek-V4-Pro
- Smoke budget: 10 USD
- Main budget: requires later approval
- Selected provider: unset
- Execution authorization: false

## Commands

Inspect-only:

```powershell
python scripts/check_gate8_provider_budget_preflight.py --provider-candidates configs/gate8/provider_candidates.yaml --budget-preflight configs/gate8/budget_preflight.yaml
```

Strict execution readiness, expected to fail:

```powershell
python scripts/check_gate8_provider_budget_preflight.py --provider-candidates configs/gate8/provider_candidates.yaml --budget-preflight configs/gate8/budget_preflight.yaml --require-ready
```

## Failure Criteria

- Either provider candidate is missing.
- Any candidate is marked authorized to run.
- Smoke budget is missing or nonpositive.
- Budget include/exclude scope is empty.
- Strict mode succeeds before explicit execution authorization.
```

- [ ] **Step 3: Update main readiness config**

Add top-level references near existing provider fields:

```yaml
provider_candidates: configs/gate8/provider_candidates.yaml
budget_preflight: configs/gate8/budget_preflight.yaml
```

Add a check block:

```yaml
provider_budget_preflight_check:
  command: python scripts/check_gate8_provider_budget_preflight.py --provider-candidates configs/gate8/provider_candidates.yaml --budget-preflight configs/gate8/budget_preflight.yaml
  strict_command: python scripts/check_gate8_provider_budget_preflight.py --provider-candidates configs/gate8/provider_candidates.yaml --budget-preflight configs/gate8/budget_preflight.yaml --require-ready
  preflight_expected_after_gate8m: true
  strict_mode_expected_exit_after_gate8m: 1
```

Add not-ready blockers:

```yaml
  - selected_provider_unset
  - provider_budget_execution_unauthorized
  - smoke_run_not_yet_authorized
```

- [ ] **Step 4: Update README**

Update the Gate 8 status paragraph to include:

```markdown
Gate 8M records GPT-5.4 and DeepSeek-V4-Pro as provider candidates and defines a 10 USD smoke-run budget preflight, but selected provider, API/runtime availability, run-date pricing, and execution authorization remain unset.
```

## Task 6: Final Verification and Commit

**Files:**
- All files changed in Tasks 1-5

- [ ] **Step 1: Run focused tests**

Run:

```powershell
python -m pytest tests/test_gate8_provider_budget_preflight.py -v
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

Run:

```powershell
python -m pytest -v
```

Expected: all tests pass.

- [ ] **Step 3: Run default preflight checker**

Run:

```powershell
python scripts/check_gate8_provider_budget_preflight.py --provider-candidates configs/gate8/provider_candidates.yaml --budget-preflight configs/gate8/budget_preflight.yaml
```

Expected JSON includes:

```json
{
  "provider_budget_preflight_ready": true,
  "execution_authorized": false,
  "selected_provider": "unset"
}
```

- [ ] **Step 4: Run strict preflight checker**

Run:

```powershell
python scripts/check_gate8_provider_budget_preflight.py --provider-candidates configs/gate8/provider_candidates.yaml --budget-preflight configs/gate8/budget_preflight.yaml --require-ready
```

Expected: exit code `1`, with `execution_authorized: false`.

- [ ] **Step 5: Run marker scan**

Run:

```powershell
Select-String -Path docs\*.md,experiments\cards\*.md,README.md,configs\gate8\*.yaml -Pattern '[T]BD|[T]ODO|turn[0-9]+'
```

Expected: no matches.

- [ ] **Step 6: Check status**

Run:

```powershell
git status --short --ignored
```

Expected: tracked Gate 8M files only plus existing ignored caches, artifacts, datasets, and PDFs.

- [ ] **Step 7: Commit**

Run:

```powershell
git add configs\gate8\provider_candidates.yaml configs\gate8\budget_preflight.yaml src\ledger_rag_gate8\provider_budget_preflight.py scripts\check_gate8_provider_budget_preflight.py tests\test_gate8_provider_budget_preflight.py docs\gate8-provider-comparison.md experiments\cards\E018-gate8m-provider-budget-preflight.md configs\gate8\main_v1_readiness.yaml README.md
git commit -m "feat: add gate8m provider budget preflight"
```

Expected: commit succeeds.


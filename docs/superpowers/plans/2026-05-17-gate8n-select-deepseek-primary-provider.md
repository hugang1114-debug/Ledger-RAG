# Gate 8N Select DeepSeek Primary Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Select DeepSeek-V4-Pro as the primary provider for the first smoke run while keeping execution unauthorized.

**Architecture:** Update the existing Gate 8M provider candidate registry and checker instead of adding a new subsystem. The checker will require exactly one final-selected provider, require it to match `selected_provider`, and still reject any execution authorization.

**Tech Stack:** Python standard library, existing simple YAML parser, YAML-like config files, Markdown docs, pytest.

---

## File Structure

- Modify `configs/gate8/provider_candidates.yaml`: set `selected_provider: deepseek_v4_pro`, set DeepSeek `final_selected: true`, keep all authorization fields false.
- Modify `src/ledger_rag_gate8/provider_budget_preflight.py`: validate selected-provider semantics.
- Modify `tests/test_gate8_provider_budget_preflight.py`: update expected selected provider and add invalid-selection tests.
- Modify `docs/gate8-provider-comparison.md`: document DeepSeek as primary and GPT-5.4 as optional credibility check.
- Modify `configs/gate8/main_v1_readiness.yaml`: reflect selected provider while keeping execution blockers.
- Modify `README.md`: update Gate 8 status.
- Create `experiments/cards/E019-gate8n-select-deepseek-primary-provider.md`: non-running selection card.

## Task 1: Update Tests for DeepSeek Selection

**Files:**
- Modify: `tests/test_gate8_provider_budget_preflight.py`

- [ ] **Step 1: Update current expected selection assertions**

Change `test_provider_candidates_contain_expected_models` to assert exactly one final-selected candidate:

```python
    selected = [candidate for candidate in inputs.provider_candidates if candidate["final_selected"] is True]
    assert [candidate["id"] for candidate in selected] == ["deepseek_v4_pro"]
```

Change `test_default_summary_reports_preflight_ready_but_execution_blocked`:

```python
    assert summary["selected_provider"] == "deepseek_v4_pro"
    assert summary["selected_candidate_id"] == "deepseek_v4_pro"
```

Change `test_cli_default_mode_exits_zero_and_reports_preflight_ready`:

```python
    assert payload["selected_provider"] == "deepseek_v4_pro"
    assert payload["selected_candidate_id"] == "deepseek_v4_pro"
```

- [ ] **Step 2: Add invalid selected-provider regression**

Add:

```python
def test_selected_provider_must_match_final_selected_candidate(tmp_path):
    candidates = tmp_path / "provider_candidates.yaml"
    budget = tmp_path / "budget_preflight.yaml"
    text = PROVIDER_CANDIDATES.read_text(encoding="utf-8").replace(
        "selected_provider: deepseek_v4_pro",
        "selected_provider: openai_gpt_5_4",
    )
    candidates.write_text(text, encoding="utf-8")
    budget.write_text(BUDGET_PREFLIGHT.read_text(encoding="utf-8"), encoding="utf-8")

    summary = build_provider_budget_preflight_summary(load_provider_budget_preflight_inputs(candidates, budget))

    assert summary["provider_budget_preflight_ready"] is False
    assert "selected_provider_final_selected_mismatch" in summary["candidate_blockers"]
```

- [ ] **Step 3: Add multiple final-selected regression**

Add:

```python
def test_multiple_final_selected_candidates_block_preflight(tmp_path):
    candidates = tmp_path / "provider_candidates.yaml"
    budget = tmp_path / "budget_preflight.yaml"
    text = PROVIDER_CANDIDATES.read_text(encoding="utf-8").replace(
        "  - id: openai_gpt_5_4\n    provider: openai\n    model: gpt-5.4\n    candidate_locked: true\n    final_selected: false",
        "  - id: openai_gpt_5_4\n    provider: openai\n    model: gpt-5.4\n    candidate_locked: true\n    final_selected: true",
    )
    candidates.write_text(text, encoding="utf-8")
    budget.write_text(BUDGET_PREFLIGHT.read_text(encoding="utf-8"), encoding="utf-8")

    summary = build_provider_budget_preflight_summary(load_provider_budget_preflight_inputs(candidates, budget))

    assert summary["provider_budget_preflight_ready"] is False
    assert "multiple_provider_candidates_final_selected" in summary["candidate_blockers"]
```

- [ ] **Step 4: Run focused tests and verify red state**

Run:

```powershell
python -m pytest tests/test_gate8_provider_budget_preflight.py -v
```

Expected: failures because config/checker still reports `selected_provider: unset` and no selected candidate id.

## Task 2: Update Provider Candidate Metadata

**Files:**
- Modify: `configs/gate8/provider_candidates.yaml`

- [ ] **Step 1: Set selected provider and DeepSeek final selection**

Update top-level fields:

```yaml
stage: gate8n_select_deepseek_primary_provider
selected_provider: deepseek_v4_pro
execution_authorized: false
```

Keep OpenAI:

```yaml
final_selected: false
recommended_role: optional_small_sample_credibility_check
```

Set DeepSeek:

```yaml
final_selected: true
recommended_role: primary_smoke_and_main_v1_candidate
```

Update blockers:

```yaml
blockers:
  - execution_not_authorized
  - api_key_or_runtime_unverified
  - run_date_pricing_not_rechecked
  - smoke_run_not_yet_authorized
```

- [ ] **Step 2: Run focused tests**

Run:

```powershell
python -m pytest tests/test_gate8_provider_budget_preflight.py -v
```

Expected: remaining failures for missing checker fields/validation.

## Task 3: Update Checker Semantics

**Files:**
- Modify: `src/ledger_rag_gate8/provider_budget_preflight.py`

- [ ] **Step 1: Change candidate blocker signature**

Change:

```python
def _candidate_blockers(candidates):
```

to:

```python
def _candidate_blockers(candidates, selected_provider):
```

- [ ] **Step 2: Track selected candidate id**

Inside `_candidate_blockers`, add:

```python
    selected_candidate_ids = []
```

Inside the candidate loop:

```python
        if candidate.get("final_selected") is True:
            final_selected_count += 1
            selected_candidate_ids.append(candidate_id)
```

After the loop:

```python
    if final_selected_count == 0:
        blockers.append("no_provider_candidate_final_selected")
    if selected_provider not in EXPECTED_PROVIDER_IDS:
        blockers.append("selected_provider_not_expected_candidate")
    if final_selected_count == 1 and selected_provider != selected_candidate_ids[0]:
        blockers.append("selected_provider_final_selected_mismatch")
```

Keep the existing multiple-selected blocker.

- [ ] **Step 3: Return selected candidate id in summary**

In `build_provider_budget_preflight_summary`, call:

```python
    candidate_blockers = _candidate_blockers(inputs.provider_candidates, selected_provider)
```

Add:

```python
    selected_candidate_ids = [
        candidate.get("id")
        for candidate in inputs.provider_candidates
        if candidate.get("final_selected") is True
    ]
    selected_candidate_id = selected_candidate_ids[0] if len(selected_candidate_ids) == 1 else "unset"
```

Add return key:

```python
        "selected_candidate_id": selected_candidate_id,
```

- [ ] **Step 4: Keep execution blocked**

Do not remove:

```python
    if not execution_authorized:
        execution_blockers.append("execution_not_authorized")
```

- [ ] **Step 5: Run focused tests**

Run:

```powershell
python -m pytest tests/test_gate8_provider_budget_preflight.py -v
```

Expected: PASS.

## Task 4: Update Docs, Readiness Matrix, and Card

**Files:**
- Modify: `docs/gate8-provider-comparison.md`
- Modify: `configs/gate8/main_v1_readiness.yaml`
- Modify: `README.md`
- Create: `experiments/cards/E019-gate8n-select-deepseek-primary-provider.md`

- [ ] **Step 1: Update provider comparison doc**

Add:

```markdown
## Gate 8N Primary Selection

DeepSeek-V4-Pro is selected as the primary provider for the first smoke run and likely main-v1 run. GPT-5.4 remains an optional small-sample credibility check, not a required provider for the first comparable run.

All six baseline families must use DeepSeek-V4-Pro for the first comparable run unless a later gate explicitly changes the provider decision. Results should be reported as DeepSeek-conditioned until cross-provider checks are completed.
```

- [ ] **Step 2: Update main readiness matrix**

Change or add:

```yaml
provider_selection:
  primary_provider: deepseek_v4_pro
  optional_credibility_provider: openai_gpt_5_4
  execution_authorized: false
```

Keep not-ready blockers:

```yaml
  - provider_budget_execution_unauthorized
  - smoke_run_not_yet_authorized
```

Remove `selected_provider_unset` from `not_ready`.

- [ ] **Step 3: Update README**

Update Gate 8 status paragraph to include:

```markdown
Gate 8N selects DeepSeek-V4-Pro as primary provider for the first smoke/main-v1 path, with GPT-5.4 retained as optional credibility-check evidence. API/runtime availability, run-date pricing, smoke-run authorization, and execution authorization remain unset.
```

- [ ] **Step 4: Add E019 card**

Create `experiments/cards/E019-gate8n-select-deepseek-primary-provider.md`:

```markdown
# E019 Gate 8N Select DeepSeek Primary Provider

## Status

Non-running readiness card. This card does not authorize API calls, API key checks, model output generation, dataset downloads, baseline runs, or result artifacts.

## Purpose

Record DeepSeek-V4-Pro as the primary provider for the first smoke run and likely main-v1 run while keeping execution blocked.

## Scope

- Primary provider: DeepSeek-V4-Pro
- Optional credibility-check provider: GPT-5.4
- Smoke budget ceiling: 10 USD
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

- DeepSeek-V4-Pro is not the selected provider.
- More than one provider is final-selected.
- Any provider is marked authorized to run.
- Strict mode succeeds before explicit smoke-run authorization.
```

## Task 5: Final Verification and Commit

**Files:**
- All files changed in Tasks 1-4

- [ ] **Step 1: Run focused tests**

Run:

```powershell
python -m pytest tests/test_gate8_provider_budget_preflight.py -v
```

Expected: PASS.

- [ ] **Step 2: Run full tests**

Run:

```powershell
python -m pytest -v
```

Expected: all tests pass.

- [ ] **Step 3: Run default provider budget checker**

Run:

```powershell
python scripts/check_gate8_provider_budget_preflight.py --provider-candidates configs/gate8/provider_candidates.yaml --budget-preflight configs/gate8/budget_preflight.yaml
```

Expected JSON includes:

```json
{
  "provider_budget_preflight_ready": true,
  "execution_authorized": false,
  "selected_provider": "deepseek_v4_pro",
  "selected_candidate_id": "deepseek_v4_pro"
}
```

- [ ] **Step 4: Run strict provider budget checker**

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

Expected: tracked Gate 8N files only plus existing ignored caches, artifacts, datasets, and PDFs.

- [ ] **Step 7: Commit**

Run:

```powershell
git add configs\gate8\provider_candidates.yaml src\ledger_rag_gate8\provider_budget_preflight.py tests\test_gate8_provider_budget_preflight.py docs\gate8-provider-comparison.md configs\gate8\main_v1_readiness.yaml README.md experiments\cards\E019-gate8n-select-deepseek-primary-provider.md
git commit -m "feat: select deepseek as gate8 primary provider"
```

Expected: commit succeeds.


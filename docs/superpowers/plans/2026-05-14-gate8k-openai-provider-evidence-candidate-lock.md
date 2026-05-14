# Gate 8K OpenAI Provider Evidence Candidate Lock Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record OpenAI `gpt-5.4-mini` as the Gate 8 provider/model candidate with official evidence while keeping all main comparison execution locked.

**Architecture:** Extend the existing Gate 8 provider evidence checker with a candidate-readiness layer separate from execution readiness. Update tracked provider metadata and docs to show candidate evidence is reviewed, while API runtime, budget, prompt/config freeze, baseline runs, and result artifacts remain blocked.

**Tech Stack:** Python standard library, existing YAML-like config parser, Markdown, pytest, local Gate 8 readiness CLIs. No SDK calls, API calls, dataset downloads, model calls, or result artifacts.

---

## File Structure

- Modify `src/ledger_rag_gate8/provider_evidence_readiness.py`: add candidate-evidence constants and candidate readiness summary fields.
- Modify `tests/test_gate8_provider_evidence_readiness.py`: add candidate-state tests and update current-registry expectations after metadata is locked.
- Modify `configs/gate8/provider_evidence_registry.yaml`: record OpenAI `gpt-5.4-mini` candidate evidence from official URLs.
- Modify `configs/gate8/provider_decision.yaml`: mirror OpenAI candidate metadata while keeping `selected: false` and `run_authorized: false`.
- Modify `configs/gate8/main_v1_readiness.yaml`: reference Gate 8K candidate state while preserving non-executable blockers.
- Modify `docs/model-provider-readiness.md`: explain candidate lock versus final provider selection.
- Modify `docs/gate8-provider-evidence-readiness.md`: document candidate-readiness behavior.
- Modify `docs/main-comparison-readiness.md`: list Gate 8K as provider-evidence candidate lock.
- Create `experiments/cards/E016-gate8k-openai-provider-evidence-candidate-lock.md`: non-running card for this metadata gate.

---

### Task 1: Add Candidate Readiness Tests

**Files:**
- Modify: `tests/test_gate8_provider_evidence_readiness.py`

- [ ] **Step 1: Write failing candidate readiness tests**

Add these helpers near `_write_ready_registry` in `tests/test_gate8_provider_evidence_readiness.py`:

```python
CANDIDATE_REVIEWED_EVIDENCE_IDS = {
    "official_pricing_source",
    "official_model_docs_source",
    "official_terms_privacy_source",
    "model_id_version_source",
    "context_window_source",
    "output_limit_source",
    "rate_limit_or_throughput_source",
}


def _write_candidate_registry(path):
    lines = [
        "version: 1",
        "gate: gate8_main_comparison",
        "stage: gate8k_openai_provider_evidence_candidate_lock",
        "status: readiness_in_progress",
        "authorized_to_run: false",
        "purpose: non_executable_provider_evidence_registry",
        "provider_evidence_candidate_locked: true",
        "provider_candidate_selected: true",
        "candidate_provider: openai",
        "candidate_model: gpt-5.4-mini",
        "candidate_model_snapshot: gpt-5.4-mini-2026-03-17",
        "provider_evidence_locked: false",
        "provider_selected: false",
        "provider: unset",
        "model: unset",
        "candidate_checked_at: 2026-05-14",
        "candidate_recheck_required_on_run_date: true",
        "context_window_tokens: 400000",
        "max_output_tokens: 128000",
        "evidence_slots:",
    ]
    urls = {
        "official_pricing_source": "https://platform.openai.com/docs/pricing/",
        "official_model_docs_source": "https://developers.openai.com/api/docs/models/gpt-5.4-mini",
        "official_terms_privacy_source": "https://openai.com/policies/service-terms/",
        "model_id_version_source": "https://developers.openai.com/api/docs/models/gpt-5.4-mini",
        "context_window_source": "https://developers.openai.com/api/docs/models/gpt-5.4-mini",
        "output_limit_source": "https://developers.openai.com/api/docs/models/gpt-5.4-mini",
        "rate_limit_or_throughput_source": "https://developers.openai.com/api/docs/models",
    }
    for evidence_id in sorted(CANDIDATE_REVIEWED_EVIDENCE_IDS):
        lines.extend(
            [
                f"  - evidence_id: {evidence_id}",
                "    required_for: provider_candidate_validation",
                f"    official_source_url: {urls[evidence_id]}",
                "    checked_at: 2026-05-14",
                "    evidence_status: reviewed",
                "    reviewer: codex",
                "    notes: official_openai_candidate_source_checked_for_gate8k",
            ]
        )
    for evidence_id in ("api_key_or_runtime_availability_note", "cost_budget_approval_note"):
        lines.extend(
            [
                f"  - evidence_id: {evidence_id}",
                "    required_for: execution_authorization",
                "    official_source_url: unset",
                "    checked_at: unset",
                "    evidence_status: missing",
                "    reviewer: unset",
                "    notes: intentionally_unresolved_until_execution_freeze",
            ]
        )
    lines.extend(
        [
            "blockers:",
            "  - provider_evidence_not_locked",
            "  - provider_not_selected",
            "  - model_not_selected",
            "  - api_key_or_runtime_availability_note_missing",
            "  - cost_budget_approval_note_missing",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_candidate_provider_decision(path):
    path.write_text(
        "\n".join(
            [
                "version: 1",
                "gate: gate8_main_comparison",
                "stage: gate8k_provider_decision_candidate",
                "status: readiness_in_progress",
                "selected: false",
                "provider: unset",
                "model: unset",
                "candidate_provider: openai",
                "candidate_model: gpt-5.4-mini",
                "candidate_model_snapshot: gpt-5.4-mini-2026-03-17",
                "run_authorized: false",
            ]
        ),
        encoding="utf-8",
    )
```

Add this test:

```python
def test_candidate_locked_registry_reports_candidate_ready_but_not_execution_ready(tmp_path):
    registry = tmp_path / "provider_evidence_registry.yaml"
    provider_decision = tmp_path / "provider_decision.yaml"
    _write_candidate_registry(registry)
    _write_candidate_provider_decision(provider_decision)

    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(registry, provider_decision)
    )

    assert summary["provider_candidate_ready"] is True
    assert summary["provider_evidence_ready"] is False
    assert summary["provider_candidate_selected"] is True
    assert summary["candidate_provider"] == "openai"
    assert summary["candidate_model"] == "gpt-5.4-mini"
    assert summary["candidate_model_snapshot"] == "gpt-5.4-mini-2026-03-17"
    assert summary["missing_candidate_evidence_ids"] == []
    assert summary["missing_evidence_ids"] == [
        "api_key_or_runtime_availability_note",
        "cost_budget_approval_note",
    ]
    assert "provider_evidence_not_locked" in summary["blockers"]
    assert "provider_decision_not_authorized" in summary["blockers"]
```

Add this mismatch test:

```python
def test_candidate_decision_must_match_registry_candidate(tmp_path):
    registry = tmp_path / "provider_evidence_registry.yaml"
    provider_decision = tmp_path / "provider_decision.yaml"
    _write_candidate_registry(registry)
    _write_candidate_provider_decision(provider_decision)
    text = provider_decision.read_text(encoding="utf-8").replace(
        "candidate_model: gpt-5.4-mini",
        "candidate_model: gpt-5.5",
    )
    provider_decision.write_text(text, encoding="utf-8")

    summary = build_provider_evidence_readiness_summary(
        load_provider_evidence_inputs(registry, provider_decision)
    )

    assert summary["provider_candidate_ready"] is False
    assert "provider_decision_candidate_model_mismatch" in summary["blockers"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_gate8_provider_evidence_readiness.py::test_candidate_locked_registry_reports_candidate_ready_but_not_execution_ready tests/test_gate8_provider_evidence_readiness.py::test_candidate_decision_must_match_registry_candidate -v
```

Expected: both tests fail because `provider_candidate_ready`, candidate summary fields, and candidate mismatch blockers do not exist yet.

- [ ] **Step 3: Commit red tests**

```powershell
git add tests\test_gate8_provider_evidence_readiness.py
git commit -m "test: cover gate8k provider candidate readiness"
```

---

### Task 2: Implement Candidate Readiness In The Checker

**Files:**
- Modify: `src/ledger_rag_gate8/provider_evidence_readiness.py`
- Test: `tests/test_gate8_provider_evidence_readiness.py`

- [ ] **Step 1: Add candidate evidence constants**

In `src/ledger_rag_gate8/provider_evidence_readiness.py`, below `EXPECTED_EVIDENCE_IDS`, add:

```python
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
```

- [ ] **Step 2: Add candidate helper functions**

In the same file, below `_slot_by_id`, add:

```python
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
    registry_candidate_provider = registry.get("candidate_provider")
    registry_candidate_model = registry.get("candidate_model")
    registry_candidate_snapshot = registry.get("candidate_model_snapshot")
    decision_candidate_provider = provider_decision.get("candidate_provider")
    decision_candidate_model = provider_decision.get("candidate_model")
    decision_candidate_snapshot = provider_decision.get("candidate_model_snapshot")

    if registry.get("provider_evidence_candidate_locked") is not True:
        blockers.append("provider_evidence_candidate_not_locked")
    if registry.get("provider_candidate_selected") is not True:
        blockers.append("provider_candidate_not_selected")
    if _is_unset(registry_candidate_provider):
        blockers.append("candidate_provider_unset")
    if _is_unset(registry_candidate_model):
        blockers.append("candidate_model_unset")
    if _is_unset(registry_candidate_snapshot):
        blockers.append("candidate_model_snapshot_unset")
    if missing_candidate_ids:
        blockers.append("provider_candidate_missing_sources")
    if unreviewed_candidate_ids:
        blockers.append("provider_candidate_unreviewed")
    if not _is_unset(registry_candidate_provider) and not _is_unset(decision_candidate_provider):
        if registry_candidate_provider != decision_candidate_provider:
            blockers.append("provider_decision_candidate_provider_mismatch")
    if not _is_unset(registry_candidate_model) and not _is_unset(decision_candidate_model):
        if registry_candidate_model != decision_candidate_model:
            blockers.append("provider_decision_candidate_model_mismatch")
    if not _is_unset(registry_candidate_snapshot) and not _is_unset(decision_candidate_snapshot):
        if registry_candidate_snapshot != decision_candidate_snapshot:
            blockers.append("provider_decision_candidate_snapshot_mismatch")
    return blockers
```

- [ ] **Step 3: Extend summary builder**

Inside `build_provider_evidence_readiness_summary`, after `absent_evidence_ids` is calculated, add:

```python
    missing_candidate_ids, unreviewed_candidate_ids = _candidate_missing_evidence_ids(slots_by_id)
    candidate_blockers = _candidate_blockers(
        registry,
        provider_decision,
        missing_candidate_ids,
        unreviewed_candidate_ids,
    )
```

After existing `validation_errors.extend(...)` calls, add:

```python
    if registry.get("provider_evidence_candidate_locked") is True:
        validation_errors.extend(
            _missing_fields(
                registry,
                REQUIRED_CANDIDATE_REGISTRY_FIELDS,
                "provider_evidence_registry",
            )
        )
```

Before final `blockers = _dedupe(blockers)`, add:

```python
    blockers.extend(candidate_blockers)
```

Before the return dictionary, add:

```python
    provider_candidate_ready = (
        not validation_errors
        and registry.get("provider_evidence_candidate_locked") is True
        and registry.get("provider_candidate_selected") is True
        and not candidate_blockers
    )
```

Add these fields to the returned dictionary:

```python
        "provider_candidate_ready": provider_candidate_ready,
        "provider_candidate_selected": registry.get("provider_candidate_selected") is True,
        "provider_evidence_candidate_locked": registry.get("provider_evidence_candidate_locked") is True,
        "candidate_provider": registry.get("candidate_provider", "unset"),
        "candidate_model": registry.get("candidate_model", "unset"),
        "candidate_model_snapshot": registry.get("candidate_model_snapshot", "unset"),
        "missing_candidate_evidence_ids": missing_candidate_ids,
        "unreviewed_candidate_evidence_ids": unreviewed_candidate_ids,
```

- [ ] **Step 4: Run candidate tests**

Run:

```powershell
python -m pytest tests/test_gate8_provider_evidence_readiness.py::test_candidate_locked_registry_reports_candidate_ready_but_not_execution_ready tests/test_gate8_provider_evidence_readiness.py::test_candidate_decision_must_match_registry_candidate -v
```

Expected: both tests pass.

- [ ] **Step 5: Run provider evidence tests**

Run:

```powershell
python -m pytest tests/test_gate8_provider_evidence_readiness.py -v
```

Expected: all provider evidence tests pass.

- [ ] **Step 6: Commit checker implementation**

```powershell
git add src\ledger_rag_gate8\provider_evidence_readiness.py tests\test_gate8_provider_evidence_readiness.py
git commit -m "feat: add gate8k provider candidate readiness"
```

---

### Task 3: Lock OpenAI Candidate Metadata

**Files:**
- Modify: `configs/gate8/provider_evidence_registry.yaml`
- Modify: `configs/gate8/provider_decision.yaml`
- Modify: `tests/test_gate8_provider_evidence_readiness.py`

- [ ] **Step 1: Update current-registry test expectations**

In `test_registry_contains_all_required_evidence_slots`, replace the provider/model state assertions with:

```python
    assert inputs.registry["authorized_to_run"] is False
    assert inputs.registry["provider_evidence_candidate_locked"] is True
    assert inputs.registry["provider_candidate_selected"] is True
    assert inputs.registry["candidate_provider"] == "openai"
    assert inputs.registry["candidate_model"] == "gpt-5.4-mini"
    assert inputs.registry["candidate_model_snapshot"] == "gpt-5.4-mini-2026-03-17"
    assert inputs.registry["provider_evidence_locked"] is False
    assert inputs.registry["provider_selected"] is False
    assert inputs.registry["provider"] == "unset"
    assert inputs.registry["model"] == "unset"
```

In `test_default_summary_is_valid_but_not_ready`, replace the empty-scaffold assertions with:

```python
    assert summary["provider_candidate_ready"] is True
    assert summary["provider_evidence_ready"] is False
    assert summary["authorized_to_run"] is False
    assert summary["provider_selected"] is False
    assert summary["candidate_provider"] == "openai"
    assert summary["candidate_model"] == "gpt-5.4-mini"
    assert summary["candidate_model_snapshot"] == "gpt-5.4-mini-2026-03-17"
    assert summary["missing_candidate_evidence_ids"] == []
    assert summary["missing_evidence_ids"] == [
        "api_key_or_runtime_availability_note",
        "cost_budget_approval_note",
    ]
    assert "provider_evidence_not_locked" in summary["blockers"]
    assert "provider_decision_not_authorized" in summary["blockers"]
```

- [ ] **Step 2: Run updated current-registry tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_gate8_provider_evidence_readiness.py::test_registry_contains_all_required_evidence_slots tests/test_gate8_provider_evidence_readiness.py::test_default_summary_is_valid_but_not_ready -v
```

Expected: tests fail because tracked metadata is still the Gate 8I empty scaffold.

- [ ] **Step 3: Update provider evidence registry**

Replace `configs/gate8/provider_evidence_registry.yaml` with:

```yaml
version: 1
gate: gate8_main_comparison
stage: gate8k_openai_provider_evidence_candidate_lock
status: readiness_in_progress
authorized_to_run: false
purpose: non_executable_provider_evidence_registry
provider_evidence_candidate_locked: true
provider_candidate_selected: true
candidate_provider: openai
candidate_model: gpt-5.4-mini
candidate_model_snapshot: gpt-5.4-mini-2026-03-17
candidate_checked_at: 2026-05-14
candidate_recheck_required_on_run_date: true
context_window_tokens: 400000
max_output_tokens: 128000
provider_evidence_locked: false
provider_selected: false
provider: unset
model: unset

evidence_slots:
  - evidence_id: official_pricing_source
    required_for: provider_cost_validation
    official_source_url: https://platform.openai.com/docs/pricing/
    checked_at: 2026-05-14
    evidence_status: reviewed
    reviewer: codex
    notes: official_pricing_page_recorded_for_candidate_only_recheck_on_run_date
  - evidence_id: official_model_docs_source
    required_for: provider_model_validation
    official_source_url: https://developers.openai.com/api/docs/models/gpt-5.4-mini
    checked_at: 2026-05-14
    evidence_status: reviewed
    reviewer: codex
    notes: official_model_page_records_candidate_model_context_and_output_limits
  - evidence_id: official_terms_privacy_source
    required_for: provider_terms_privacy_validation
    official_source_url: https://openai.com/policies/service-terms/
    checked_at: 2026-05-14
    evidence_status: reviewed
    reviewer: codex
    notes: official_terms_recorded_for_candidate_only_privacy_page_also_recorded_in_docs
  - evidence_id: model_id_version_source
    required_for: model_identity_validation
    official_source_url: https://developers.openai.com/api/docs/models/gpt-5.4-mini
    checked_at: 2026-05-14
    evidence_status: reviewed
    reviewer: codex
    notes: preferred_snapshot_gpt_5_4_mini_2026_03_17_must_be_rechecked_before_run
  - evidence_id: context_window_source
    required_for: context_window_validation
    official_source_url: https://developers.openai.com/api/docs/models/gpt-5.4-mini
    checked_at: 2026-05-14
    evidence_status: reviewed
    reviewer: codex
    notes: candidate_context_window_tokens_400000
  - evidence_id: output_limit_source
    required_for: output_limit_validation
    official_source_url: https://developers.openai.com/api/docs/models/gpt-5.4-mini
    checked_at: 2026-05-14
    evidence_status: reviewed
    reviewer: codex
    notes: candidate_max_output_tokens_128000
  - evidence_id: rate_limit_or_throughput_source
    required_for: run_feasibility_validation
    official_source_url: https://developers.openai.com/api/docs/models
    checked_at: 2026-05-14
    evidence_status: reviewed
    reviewer: codex
    notes: exact_account_rate_limits_and_throughput_must_be_rechecked_before_execution
  - evidence_id: api_key_or_runtime_availability_note
    required_for: runtime_availability_validation
    official_source_url: unset
    checked_at: unset
    evidence_status: missing
    reviewer: unset
    notes: intentionally_unresolved_do_not_store_api_keys_in_repository
  - evidence_id: cost_budget_approval_note
    required_for: cost_budget_validation
    official_source_url: unset
    checked_at: unset
    evidence_status: missing
    reviewer: unset
    notes: intentionally_unresolved_budget_must_be_approved_before_model_calls

blockers:
  - provider_evidence_not_locked
  - provider_not_selected
  - model_not_selected
  - api_key_or_runtime_availability_note_missing
  - cost_budget_approval_note_missing
```

- [ ] **Step 4: Update provider decision metadata**

Edit `configs/gate8/provider_decision.yaml` so the top state includes:

```yaml
version: 1
gate: gate8_main_comparison
stage: gate8k_provider_candidate_decision
status: readiness_in_progress
selected: false
provider: unset
model: unset
candidate_provider: openai
candidate_model: gpt-5.4-mini
candidate_model_snapshot: gpt-5.4-mini-2026-03-17
candidate_checked_at: 2026-05-14
candidate_recheck_required_on_run_date: true
model_version_or_date: unset
pricing_checked_at: unset
pricing_source: unset
model_docs_checked_at: unset
model_docs_source: unset
terms_checked_at: unset
terms_source: unset
context_window: unset
max_output_tokens: unset
rate_limit_note: unset
data_retention_note: unset
api_key_required: true
api_key_present: false
prompt_versions_locked: false
generation_config_locked: false
cost_budget_approved: false
run_authorized: false
provider_evidence_registry: configs/gate8/provider_evidence_registry.yaml
```

Keep the existing `required_future_evidence`, `disallowed_evidence`, and `prompt_config_requirements` sections, but remove any duplicate top-level scalar keys that conflict with the block above.

- [ ] **Step 5: Run metadata tests**

Run:

```powershell
python -m pytest tests/test_gate8_provider_evidence_readiness.py -v
```

Expected: all provider evidence tests pass, default summary is candidate-ready but not execution-ready.

- [ ] **Step 6: Commit metadata lock**

```powershell
git add configs\gate8\provider_evidence_registry.yaml configs\gate8\provider_decision.yaml tests\test_gate8_provider_evidence_readiness.py
git commit -m "chore: lock openai provider candidate evidence"
```

---

### Task 4: Update Gate 8K Docs, Card, And Readiness Matrix

**Files:**
- Modify: `README.md`
- Modify: `docs/model-provider-readiness.md`
- Modify: `docs/gate8-provider-evidence-readiness.md`
- Modify: `docs/main-comparison-readiness.md`
- Modify: `configs/gate8/main_v1_readiness.yaml`
- Create: `experiments/cards/E016-gate8k-openai-provider-evidence-candidate-lock.md`

- [ ] **Step 1: Update readiness matrix**

In `configs/gate8/main_v1_readiness.yaml`, add or update a provider-candidate section:

```yaml
provider_candidate:
  status: candidate_locked
  provider: openai
  model: gpt-5.4-mini
  model_snapshot: gpt-5.4-mini-2026-03-17
  evidence_registry: configs/gate8/provider_evidence_registry.yaml
  checked_at: 2026-05-14
  execution_authorized: false
  recheck_required_on_run_date: true
```

Keep existing provider/model execution blockers such as `model_provider_unselected`, `cost_budget_unapproved`, `prompt_versions_unlocked`, and execution authorization blockers.

- [ ] **Step 2: Create non-running experiment card**

Create `experiments/cards/E016-gate8k-openai-provider-evidence-candidate-lock.md`:

```markdown
# E016 Gate 8K OpenAI Provider Evidence Candidate Lock

## Status

Non-running readiness card. This card records provider evidence metadata only.

## Purpose

Lock OpenAI `gpt-5.4-mini` as the first Gate 8 provider/model candidate while keeping main comparison execution unauthorized.

## Scope

- Record official OpenAI source URLs checked on 2026-05-14.
- Record candidate provider/model/snapshot metadata.
- Keep API key availability and cost budget unresolved.
- Keep `run_authorized: false`.

## Not Authorized

- No model calls.
- No baseline runs.
- No prompt/config freeze.
- No budget approval.
- No result artifacts.
- No final Gate 8 passage.

## Verification Commands

```powershell
python -m pytest tests/test_gate8_provider_evidence_readiness.py -v
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --require-ready
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml --require-ready
```

Strict provider and freeze checks are expected to fail until runtime, budget, prompt/config, and execution authorization are locked.
```

- [ ] **Step 3: Update provider docs**

In `docs/model-provider-readiness.md`, add a `Gate 8K Candidate` section:

```markdown
## Gate 8K Candidate

Gate 8K records OpenAI `gpt-5.4-mini` as the first provider/model candidate. This is a candidate lock, not a final execution decision.

The candidate evidence records official OpenAI URLs for pricing, model documentation, terms, context window, output limit, and throughput planning. API key availability and cost budget approval remain unresolved.

`provider_decision.yaml` therefore keeps `selected: false` and `run_authorized: false`. Prices, model availability, limits, and terms must be rechecked on the actual run date before execution can be authorized.
```

In `docs/gate8-provider-evidence-readiness.md`, add:

```markdown
## Gate 8K Candidate State

The checker now distinguishes candidate readiness from execution readiness. After Gate 8K, default inspection may report `provider_candidate_ready: true`, while strict readiness still reports `provider_evidence_ready: false`.

This means official candidate evidence exists, but model calls remain blocked by unresolved runtime availability, cost budget approval, final provider selection, prompt/config freeze, and execution authorization.
```

In `docs/main-comparison-readiness.md`, add one sentence to the provider blocker section:

```markdown
Gate 8K locks an OpenAI `gpt-5.4-mini` candidate, but Gate 8 remains blocked until the candidate is rechecked on the run date and promoted through the execution freeze.
```

- [ ] **Step 4: Update README**

In `README.md`, add:

```markdown
- `experiments/cards/E016-gate8k-openai-provider-evidence-candidate-lock.md` - non-running provider candidate evidence card
```

Update the Gate 8 readiness paragraph to mention:

```markdown
Provider candidate evidence is partially locked for OpenAI `gpt-5.4-mini`, but provider execution, API/runtime availability, budget, prompt/config freeze, and main baselines remain unauthorized.
```

- [ ] **Step 5: Run docs scan**

Run:

```powershell
Select-String -Path docs\*.md,experiments\cards\*.md,README.md,configs\gate8\*.yaml,snapshots\main_v1\*.json -Pattern ('TB' + 'D|TO' + 'DO|turn[0-9]+')
```

Expected: no matches.

- [ ] **Step 6: Commit docs/card/readiness updates**

```powershell
git add README.md docs\model-provider-readiness.md docs\gate8-provider-evidence-readiness.md docs\main-comparison-readiness.md configs\gate8\main_v1_readiness.yaml experiments\cards\E016-gate8k-openai-provider-evidence-candidate-lock.md
git commit -m "docs: document gate8k provider candidate lock"
```

---

### Task 5: Final Verification

**Files:**
- No new files. Verification only.

- [ ] **Step 1: Run full tests**

```powershell
python -m pytest -v
```

Expected: all tests pass.

- [ ] **Step 2: Run provider evidence default check**

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml
```

Expected: exit `0`, `provider_candidate_ready: true`, `provider_evidence_ready: false`.

- [ ] **Step 3: Run strict provider check and preserve expected failure**

```powershell
python scripts/check_gate8_provider_evidence_readiness.py --registry configs/gate8/provider_evidence_registry.yaml --require-ready; if ($LASTEXITCODE -ne 0) { "STRICT_PROVIDER_EXIT=$LASTEXITCODE"; exit 0 } else { "STRICT_PROVIDER_EXIT=0"; exit 1 }
```

Expected: wrapper exits `0`, printed strict exit is `1`, blockers include runtime availability, budget approval, provider decision not authorized, and provider evidence not locked.

- [ ] **Step 4: Run strict freeze check and preserve expected failure**

```powershell
python scripts/check_gate8_freeze_readiness.py --freeze-config configs/gate8/freeze_readiness.yaml --require-ready; if ($LASTEXITCODE -ne 0) { "STRICT_FREEZE_EXIT=$LASTEXITCODE"; exit 0 } else { "STRICT_FREEZE_EXIT=0"; exit 1 }
```

Expected: wrapper exits `0`, printed strict exit is `1`, `freeze_ready: false`.

- [ ] **Step 5: Confirm Gate 8J remains ready**

```powershell
python scripts/check_gate8_snapshot_readiness.py --registry snapshots/main_v1/source_snapshots.json --require-ready
python scripts/check_gate8_snapshot_index_promotion.py --registry snapshots/main_v1/source_snapshots.json --readiness-config configs/gate8/main_v1_readiness.yaml --require-promotable
```

Expected: both commands exit `0`.

- [ ] **Step 6: Scan placeholders and status**

```powershell
Select-String -Path docs\*.md,experiments\cards\*.md,README.md,configs\gate8\*.yaml,snapshots\main_v1\*.json -Pattern ('TB' + 'D|TO' + 'DO|turn[0-9]+')
git status --short --ignored
```

Expected: scan returns no matches. Git status shows no tracked changes, only ignored caches, datasets, artifacts, and PDFs.

---

## Self-Review Checklist

- Spec coverage: candidate evidence, official URLs, unresolved API key/budget, non-execution boundary, checker behavior, docs/card, and tests are all covered.
- Placeholder scan: this plan contains no placeholder markers or report-local links.
- Type consistency: candidate keys are consistently named `provider_candidate_selected`, `provider_evidence_candidate_locked`, `candidate_provider`, `candidate_model`, and `candidate_model_snapshot`.
- Scope: no task authorizes model calls, baseline runs, prompt freeze, budget approval, result artifacts, or final Gate 8 passage.

# Gate 8L Prompt Generation Config Candidate Freeze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create auditable candidate prompt files and generation config metadata for all six Gate 5 baselines while keeping Gate 8 execution unauthorized.

**Architecture:** Store exact prompt text as tracked Markdown files, record prompt file hashes in `configs/gate8/prompt_registry.yaml`, and record shared candidate generation constraints in `configs/gate8/generation_config_registry.yaml`. Extend the existing stdlib-only readiness checker so candidate readiness can pass while final execution readiness remains blocked.

**Tech Stack:** Python standard library, existing simple YAML parser, Markdown docs, YAML-like tracked config files, pytest.

---

## File Structure

- Create `prompts/gate8/main_v1/vanilla_rag.md`: candidate prompt for Vanilla RAG.
- Create `prompts/gate8/main_v1/hybrid_rag.md`: candidate prompt for Hybrid RAG.
- Create `prompts/gate8/main_v1/citation_only.md`: candidate prompt for Citation-only.
- Create `prompts/gate8/main_v1/validator_only.md`: candidate prompt for Validator-only.
- Create `prompts/gate8/main_v1/ledger_only.md`: candidate prompt for Ledger-only.
- Create `prompts/gate8/main_v1/ledger_validator.md`: candidate prompt for Ledger + Validator.
- Modify `configs/gate8/prompt_registry.yaml`: replace reserved prompt slots with candidate prompt metadata.
- Modify `configs/gate8/generation_config_registry.yaml`: replace reserved generation slots with candidate generation metadata.
- Modify `src/ledger_rag_gate8/prompt_config_readiness.py`: add candidate readiness validation, prompt hash validation, and accidental authorization rejection.
- Modify `tests/test_gate8_prompt_config_readiness.py`: cover candidate readiness and blocked final readiness.
- Modify `docs/gate8-prompt-config-readiness.md`: document Gate 8L candidate semantics.
- Modify `configs/gate8/main_v1_readiness.yaml`: reference Gate 8L candidate freeze status and expected strict failure.
- Modify `README.md`: mention Gate 8L prompt/config candidate freeze as the current readiness layer.
- Create `experiments/cards/E017-gate8l-prompt-generation-config-candidate-freeze.md`: non-running experiment card.

## Candidate Prompt Text

Use this common response contract in every prompt file:

```text
Return a JSON object with these keys:
- global_answer: string
- atomic_claims: array of objects with claim_id, text, and citations
- refusal: boolean
- refusal_reason: string
```

Use these baseline-specific citation policies:

- `vanilla_rag`: citations may be empty because the baseline has no required citation mechanism.
- `hybrid_rag`: citations may be empty because the baseline tests retrieval strength without a verifier or ledger.
- `citation_only`: citations must reference retrieved evidence ids.
- `validator_only`: citations may reference retrieved evidence ids when available, but verifier verdicts are produced after generation.
- `ledger_only`: citations must reference ledger span ids.
- `ledger_validator`: citations must reference ledger span ids and remain compatible with later verifier verdicts.

## Task 1: Write Failing Prompt Registry Tests

**Files:**
- Modify: `tests/test_gate8_prompt_config_readiness.py`

- [ ] **Step 1: Add tests for candidate prompt file and hash requirements**

Add these imports:

```python
import hashlib
```

Add this helper near the existing constants:

```python
PROMPT_DIR = ROOT / "prompts" / "gate8" / "main_v1"
```

Add these tests:

```python
def test_candidate_prompt_files_exist_for_all_baselines():
    expected_files = {f"{family}.md" for family in EXPECTED_BASELINE_FAMILIES}

    assert {path.name for path in PROMPT_DIR.glob("*.md")} == expected_files


def test_default_summary_reports_candidate_ready_but_final_not_ready():
    summary = build_prompt_config_readiness_summary(load_prompt_config_inputs(PROMPT_REGISTRY, GENERATION_CONFIG))

    assert summary["prompt_config_candidate_ready"] is True
    assert summary["prompt_config_ready"] is False
    assert summary["authorized_to_run"] is False
    assert summary["candidate_blockers"] == []
    assert "prompt_registry_not_authorized" in summary["blockers"]
    assert "generation_config_registry_not_authorized" in summary["blockers"]


def test_prompt_hashes_match_registry_entries():
    inputs = load_prompt_config_inputs(PROMPT_REGISTRY, GENERATION_CONFIG)

    for slot in inputs.prompt_slots:
        prompt_path = ROOT / slot["prompt_file"]
        digest = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
        assert slot["prompt_sha256"] == digest
```

- [ ] **Step 2: Run tests and verify they fail for missing implementation**

Run:

```powershell
python -m pytest tests/test_gate8_prompt_config_readiness.py -v
```

Expected: failures mention missing `prompts/gate8/main_v1` files or missing `prompt_config_candidate_ready`.

## Task 2: Add Candidate Prompt Files

**Files:**
- Create: `prompts/gate8/main_v1/vanilla_rag.md`
- Create: `prompts/gate8/main_v1/hybrid_rag.md`
- Create: `prompts/gate8/main_v1/citation_only.md`
- Create: `prompts/gate8/main_v1/validator_only.md`
- Create: `prompts/gate8/main_v1/ledger_only.md`
- Create: `prompts/gate8/main_v1/ledger_validator.md`

- [ ] **Step 1: Create the prompt directory**

Run:

```powershell
New-Item -ItemType Directory -Force prompts\gate8\main_v1
```

Expected: directory exists.

- [ ] **Step 2: Add the six prompt files**

Use `apply_patch` to add six Markdown files. Each file should include these sections with baseline-specific content:

```markdown
# Gate 8 Main v1 <Baseline Name> Prompt Candidate

You answer one question using only the evidence provided in the current run.

## Evidence Rules

Use only evidence items included in the prompt. Do not invent sources, ids, titles, spans, or facts.

## Output Contract

Return a JSON object with these keys:

- global_answer: string
- atomic_claims: array of objects with claim_id, text, and citations
- refusal: boolean
- refusal_reason: string

## Insufficient Evidence

If the provided evidence does not support an answer, set refusal to true, make global_answer an insufficient-evidence statement, return no unsupported factual claims, and explain the missing evidence in refusal_reason.

## Baseline Policy

<baseline-specific policy from the Candidate Prompt Text section>
```

For `ledger_validator.md`, use this baseline policy:

```markdown
Use ledger span ids for every factual atomic claim. Each citation must reference one or more provided ledger span ids. The answer must remain compatible with later support, refute, or insufficient verifier verdicts.
```

- [ ] **Step 3: Run prompt file existence test**

Run:

```powershell
python -m pytest tests/test_gate8_prompt_config_readiness.py::test_candidate_prompt_files_exist_for_all_baselines -v
```

Expected: PASS.

## Task 3: Add Candidate Readiness Logic

**Files:**
- Modify: `src/ledger_rag_gate8/prompt_config_readiness.py`

- [ ] **Step 1: Extend imports and required fields**

Change the imports:

```python
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
```

Add required candidate fields:

```python
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
```

- [ ] **Step 2: Add prompt hash and marker helpers**

Add these functions below `_has_items`:

```python
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
    markers = ["tb" + "d", "to" + "do", "turn"]
    return any(marker in lowered for marker in markers)
```

- [ ] **Step 3: Add candidate blocker builder**

Add this function above `build_prompt_config_readiness_summary`:

```python
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
    for field in ["answer_style", "citation_granularity", "max_evidence_items", "max_atomic_claims", "temperature", "max_output_tokens"]:
        if shared_constraints.get(field) in (None, "unset", ""):
            blockers.append(f"candidate_shared_constraint_unset_{field}")

    for slot in inputs.prompt_slots:
        missing = REQUIRED_CANDIDATE_PROMPT_SLOT_FIELDS - set(slot)
        if missing:
            blockers.append(f"candidate_prompt_slot_missing_fields_{slot.get('baseline_family', 'unknown')}")
            continue
        if slot.get("authorized_to_run") is True:
            blockers.append(f"candidate_prompt_slot_authorized_{slot['baseline_family']}")
        if slot.get("prompt_status") != "candidate_locked":
            blockers.append(f"candidate_prompt_slot_not_locked_{slot['baseline_family']}")
        prompt_path = _repo_path(slot["prompt_file"])
        if not prompt_path.is_file():
            blockers.append(f"candidate_prompt_file_missing_{slot['baseline_family']}")
            continue
        if _sha256_file(prompt_path) != slot.get("prompt_sha256"):
            blockers.append(f"candidate_prompt_hash_mismatch_{slot['baseline_family']}")
        if _contains_disallowed_marker(prompt_path):
            blockers.append(f"candidate_prompt_marker_found_{slot['baseline_family']}")

    for slot in inputs.generation_slots:
        missing = REQUIRED_CANDIDATE_GENERATION_SLOT_FIELDS - set(slot)
        if missing:
            blockers.append(f"candidate_generation_slot_missing_fields_{slot.get('baseline_family', 'unknown')}")
            continue
        if slot.get("authorized_to_run") is True:
            blockers.append(f"candidate_generation_slot_authorized_{slot['baseline_family']}")
        if slot.get("config_status") != "candidate_locked":
            blockers.append(f"candidate_generation_slot_not_locked_{slot['baseline_family']}")

    return _dedupe(blockers)
```

- [ ] **Step 4: Add mapping section parser**

Add this parser near `parse_slot_section`:

```python
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
```

- [ ] **Step 5: Include candidate readiness in the summary**

Inside `build_prompt_config_readiness_summary`, after `missing_generation`, add:

```python
    candidate_blockers = _candidate_blockers(inputs, prompt_families, generation_families)
    prompt_config_candidate_ready = not candidate_blockers
```

Add these keys to the returned dictionary:

```python
        "prompt_config_candidate_ready": prompt_config_candidate_ready,
        "candidate_blockers": candidate_blockers,
```

- [ ] **Step 6: Run focused tests**

Run:

```powershell
python -m pytest tests/test_gate8_prompt_config_readiness.py -v
```

Expected: remaining failures are registry value/hash mismatches because configs are still reserved.

## Task 4: Update Prompt and Generation Registries

**Files:**
- Modify: `configs/gate8/prompt_registry.yaml`
- Modify: `configs/gate8/generation_config_registry.yaml`

- [ ] **Step 1: Compute prompt hashes**

Run:

```powershell
Get-ChildItem prompts\gate8\main_v1\*.md | ForEach-Object { $h = Get-FileHash -Algorithm SHA256 $_.FullName; "$($_.BaseName) $($h.Hash.ToLower())" }
```

Expected: six lowercase SHA256 values.

- [ ] **Step 2: Replace prompt registry slots**

Use `apply_patch` to update top-level fields:

```yaml
stage: gate8l_prompt_candidate_freeze
status: readiness_in_progress
authorized_to_run: false
purpose: non_executable_prompt_candidate_registry
prompt_versions_locked: false
prompt_text_frozen: false
candidate_prompt_versions_locked: true
candidate_prompt_text_frozen: true
```

For each prompt slot, use this shape and insert the real hash:

```yaml
  - baseline_family: vanilla_rag
    prompt_version: gate8l_vanilla_rag_v1
    prompt_status: candidate_locked
    prompt_file: prompts/gate8/main_v1/vanilla_rag.md
    prompt_sha256: <real_sha256>
    authorized_to_run: false
    requires_provider_freeze: true
    notes: candidate_prompt_text_locked_execution_unauthorized
```

Keep top-level blockers that prevent final readiness:

```yaml
blockers:
  - final_prompt_versions_unlocked
  - final_prompt_text_not_frozen
  - provider_not_finalized
  - execution_not_authorized
```

- [ ] **Step 3: Replace generation config registry slots**

Use `apply_patch` to update top-level fields:

```yaml
stage: gate8l_generation_config_candidate_freeze
status: readiness_in_progress
authorized_to_run: false
purpose: non_executable_generation_config_candidate_registry
generation_config_locked: false
candidate_generation_config_locked: true
shared_answer_style_locked: false
candidate_shared_answer_style_locked: true
shared_evidence_budget_locked: false
candidate_shared_evidence_budget_locked: true
```

Set `shared_constraints`:

```yaml
shared_constraints:
  answer_style: global_answer_with_atomic_claims
  citation_granularity: evidence_item_or_ledger_span
  max_evidence_items: 8
  max_atomic_claims: 8
  temperature: 0
  seed: unset_provider_support_recheck_required
  max_output_tokens: 2048
  provider_support_recheck_required: true
```

For each generation slot, use:

```yaml
  - baseline_family: vanilla_rag
    generation_config_version: gate8l_vanilla_rag_generation_v1
    config_status: candidate_locked
    authorized_to_run: false
    requires_provider_freeze: true
    notes: candidate_generation_config_locked_execution_unauthorized
```

Keep final-readiness blockers:

```yaml
blockers:
  - final_generation_config_unlocked
  - final_shared_answer_style_unlocked
  - final_shared_evidence_budget_unlocked
  - provider_not_finalized
  - execution_not_authorized
```

- [ ] **Step 4: Run prompt/config tests**

Run:

```powershell
python -m pytest tests/test_gate8_prompt_config_readiness.py -v
```

Expected: update older assertions if they still expect Gate 8H blocker names.

## Task 5: Update Legacy Tests and Add Authorization Regression Tests

**Files:**
- Modify: `tests/test_gate8_prompt_config_readiness.py`

- [ ] **Step 1: Update existing default summary assertions**

Change `test_default_summary_is_valid_but_not_ready` so it expects:

```python
    assert summary["prompt_config_candidate_ready"] is True
    assert summary["prompt_config_ready"] is False
    assert summary["authorized_to_run"] is False
    assert summary["candidate_blockers"] == []
    assert "prompt_registry_not_authorized" in summary["blockers"]
    assert "generation_config_registry_not_authorized" in summary["blockers"]
```

- [ ] **Step 2: Add accidental authorization regression**

Add:

```python
def test_candidate_readiness_rejects_accidental_top_level_authorization(tmp_path):
    prompt_registry = tmp_path / "prompt.yaml"
    generation_config = tmp_path / "generation.yaml"
    prompt_file = tmp_path / "vanilla.md"
    prompt_file.write_text("Safe prompt text with no unresolved markers.", encoding="utf-8")
    digest = hashlib.sha256(prompt_file.read_bytes()).hexdigest()

    prompt_registry.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8l_prompt_candidate_freeze",
                "authorized_to_run: true",
                "prompt_versions_locked: false",
                "prompt_text_frozen: false",
                "candidate_prompt_versions_locked: true",
                "candidate_prompt_text_frozen: true",
                "baseline_prompt_slots:",
                "  - baseline_family: vanilla_rag",
                "    prompt_version: gate8l_vanilla_rag_v1",
                "    prompt_status: candidate_locked",
                f"    prompt_file: {prompt_file}",
                f"    prompt_sha256: {digest}",
                "    authorized_to_run: false",
                "blockers:",
            ]
        ),
        encoding="utf-8",
    )
    generation_config.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8l_generation_config_candidate_freeze",
                "authorized_to_run: false",
                "generation_config_locked: false",
                "candidate_generation_config_locked: true",
                "candidate_shared_answer_style_locked: true",
                "candidate_shared_evidence_budget_locked: true",
                "shared_constraints:",
                "  answer_style: global_answer_with_atomic_claims",
                "  citation_granularity: evidence_item_or_ledger_span",
                "  max_evidence_items: 8",
                "  max_atomic_claims: 8",
                "  temperature: 0",
                "  max_output_tokens: 2048",
                "baseline_generation_slots:",
                "  - baseline_family: vanilla_rag",
                "    generation_config_version: gate8l_vanilla_rag_generation_v1",
                "    config_status: candidate_locked",
                "    authorized_to_run: false",
                "blockers:",
            ]
        ),
        encoding="utf-8",
    )

    summary = build_prompt_config_readiness_summary(load_prompt_config_inputs(prompt_registry, generation_config))

    assert summary["prompt_config_candidate_ready"] is False
    assert "prompt_registry_accidentally_authorized" in summary["candidate_blockers"]
```

- [ ] **Step 3: Run all prompt/config tests**

Run:

```powershell
python -m pytest tests/test_gate8_prompt_config_readiness.py -v
```

Expected: PASS.

## Task 6: Update Docs, Readiness Config, and Experiment Card

**Files:**
- Modify: `docs/gate8-prompt-config-readiness.md`
- Modify: `configs/gate8/main_v1_readiness.yaml`
- Modify: `README.md`
- Create: `experiments/cards/E017-gate8l-prompt-generation-config-candidate-freeze.md`

- [ ] **Step 1: Update Gate 8 prompt/config doc**

Add a Gate 8L section:

```markdown
## Gate 8L Candidate Freeze

Gate 8L adds candidate prompt files and candidate generation constraints. Candidate readiness may pass, but final prompt/config execution readiness remains blocked.

Expected default checker state after Gate 8L:

```json
{
  "prompt_config_candidate_ready": true,
  "prompt_config_ready": false,
  "authorized_to_run": false
}
```

Strict mode is still expected to fail until final provider selection, run-date price and API checks, budget approval, execution card review, and explicit run authorization are recorded.
```

- [ ] **Step 2: Update main readiness config**

In `configs/gate8/main_v1_readiness.yaml`, update `prompt_config_readiness_check` with:

```yaml
  candidate_expected_after_gate8l: true
  final_strict_mode_expected_exit_after_gate8l: 1
```

Update `not_ready` by replacing prompt/config placeholder blockers with final blockers:

```yaml
  - final_prompt_versions_unlocked
  - final_generation_config_unlocked
  - prompt_config_execution_unauthorized
```

- [ ] **Step 3: Update README current status**

Change the Gate 8 paragraph to say:

```markdown
Provider candidate evidence is partially locked for OpenAI `gpt-5.4-mini`, and Gate 8L freezes candidate prompt/config artifacts. Provider execution, API/runtime availability, budget, final prompt/config authorization, and main baselines remain unauthorized.
```

- [ ] **Step 4: Add non-running experiment card**

Create `experiments/cards/E017-gate8l-prompt-generation-config-candidate-freeze.md`:

```markdown
# E017 Gate 8L Prompt Generation Config Candidate Freeze

## Status

Non-running readiness card. This card does not authorize model calls, dataset downloads, baseline runs, or result artifacts.

## Purpose

Freeze candidate prompt text and candidate generation constraints for the six Gate 5 baseline families before final Gate 8 execution approval.

## Scope

- Baselines: Vanilla RAG, Hybrid RAG, Citation-only, Validator-only, Ledger-only, Ledger + Validator
- Datasets: main_v1 source snapshots only
- Provider: candidate OpenAI `gpt-5.4-mini`, execution unauthorized

## Commands

Inspect-only:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml
```

Strict final readiness, expected to fail:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml --require-ready
```

## Failure Criteria

- Any baseline prompt file is missing.
- Any prompt hash mismatches the registry.
- Candidate readiness is false.
- Final readiness is true before explicit execution authorization.
- Any model call or result artifact is produced.
```

## Task 7: Final Verification and Commit

**Files:**
- All files changed in Tasks 1-6

- [ ] **Step 1: Run focused tests**

Run:

```powershell
python -m pytest tests/test_gate8_prompt_config_readiness.py -v
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

Run:

```powershell
python -m pytest -v
```

Expected: all tests pass.

- [ ] **Step 3: Run prompt/config checker in default mode**

Run:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml
```

Expected: JSON includes:

```json
{
  "prompt_config_candidate_ready": true,
  "prompt_config_ready": false,
  "authorized_to_run": false
}
```

- [ ] **Step 4: Run strict prompt/config checker**

Run:

```powershell
python scripts/check_gate8_prompt_config_readiness.py --prompt-registry configs/gate8/prompt_registry.yaml --generation-config configs/gate8/generation_config_registry.yaml --require-ready
```

Expected: exit code `1`, with `prompt_config_ready: false`.

- [ ] **Step 5: Run project marker scan**

Run:

```powershell
Select-String -Path docs\*.md,experiments\cards\*.md,README.md,configs\gate8\*.yaml,prompts\gate8\main_v1\*.md -Pattern '[T]BD|[T]ODO|turn[0-9]+'
```

Expected: no matches.

- [ ] **Step 6: Check ignored/generated files**

Run:

```powershell
git status --short --ignored
```

Expected: tracked source/docs/config/prompt changes only; ignored datasets, artifacts, PDFs, and caches remain ignored.

- [ ] **Step 7: Commit**

Run:

```powershell
git add prompts\gate8\main_v1 configs\gate8\prompt_registry.yaml configs\gate8\generation_config_registry.yaml configs\gate8\main_v1_readiness.yaml src\ledger_rag_gate8\prompt_config_readiness.py tests\test_gate8_prompt_config_readiness.py docs\gate8-prompt-config-readiness.md README.md experiments\cards\E017-gate8l-prompt-generation-config-candidate-freeze.md
git commit -m "feat: freeze gate8l prompt config candidates"
```

Expected: commit succeeds and working tree is clean except ignored files.

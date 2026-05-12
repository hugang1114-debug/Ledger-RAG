# Gate 8F Run Config And Provider Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create non-running Gate 8F run-matrix and provider-readiness metadata without selecting a provider or authorizing main baseline execution.

**Architecture:** Gate 8F is documentation and YAML metadata only. It adds human-readable readiness docs, a non-executable run matrix, provider decision metadata with all execution fields unset, and an experiment card that explicitly forbids model calls, baseline runs, result generation, and status promotion.

**Tech Stack:** Markdown, YAML, PowerShell verification commands, existing Gate 8 source snapshot registry and readiness checker.

---

## File Structure

- Create `docs/gate8-run-config-readiness.md`: explains the non-executable run matrix, dataset/baseline scope, artifact path conventions, and lockout rules.
- Create `docs/model-provider-readiness.md`: explains provider selection criteria, official pricing/terms evidence requirements, prompt/config freeze requirements, and why no provider is selected in this gate.
- Create `configs/gate8/main_v1_run_matrix.yaml`: records the three datasets, six baseline families, metric groups, artifact paths, and `authorized_to_run: false`.
- Create `configs/gate8/provider_decision.yaml`: records provider decision status with `selected: false`, unset provider/model/pricing fields, required future evidence, and disallowed behavior.
- Create `experiments/cards/E011-gate8-run-config-readiness.md`: authorizes metadata creation only.
- Modify `README.md`: add the new docs/config/card to project structure.
- Modify `docs/main-comparison-readiness.md`: add Gate 8F readiness section.
- Modify `configs/gate8/main_v1_readiness.yaml`: reference the new run matrix and provider decision files while keeping `authorized_to_run: false`.

---

### Task 1: Add Gate 8F Readiness Docs

**Files:**
- Create: `docs/gate8-run-config-readiness.md`
- Create: `docs/model-provider-readiness.md`

- [ ] **Step 1: Create run config readiness doc**

Create `docs/gate8-run-config-readiness.md` with:

````markdown
# Gate 8 Run Config Readiness

Gate 8F locks the non-executable shape of the `main_v1` comparison. It does not authorize model calls, retrieval evaluation, baseline execution, metric computation, or paper-result claims.

## Locked Scope

The first main comparison remains limited to:

- HotpotQA dev distractor
- 2WikiMultihopQA dev
- MuSiQue answerable dev

The comparison matrix must include all six Gate 5 baseline families:

- `vanilla_rag`
- `hybrid_rag`
- `citation_only`
- `validator_only`
- `ledger_only`
- `ledger_validator`

Every future executable run must reference:

- the source snapshot id from `snapshots/main_v1/source_snapshots.json`
- the retrieval index manifest path from `snapshots/main_v1/source_snapshots.json`
- the baseline family from `docs/baseline-contract.yaml`
- the metric groups from `docs/metric-contract.yaml`
- a frozen prompt/config version
- a selected provider/model record
- an ignored artifact destination under `artifacts/gate8/main_v1/`

## Non-Executable Matrix

`configs/gate8/main_v1_run_matrix.yaml` is a readiness matrix, not a command source. Its `authorized_to_run` field must remain `false` until a later execution gate locks provider, prompt, budget, and reproducibility review.

The matrix may list a `hybrid_rag` baseline, but hybrid execution remains blocked until a separate dense or hybrid retrieval implementation is locked. The current Gate 8E lexical index is enough for lexical retrieval readiness only.

## Run Lockout

Gate 8F does not clear the final Gate 8 status blocker. Source snapshot registry records remain `source_ready`, not `ready`.

Future execution is blocked while any of these remain true:

- provider is unselected
- official pricing and model documentation have not been checked on the run date
- prompt versions are not frozen
- cost budget is not approved
- execution card does not name exact commands and output paths
- reproducibility review has not confirmed paths, seeds, configs, and artifact destinations

## Artifact Convention

Future run outputs must stay ignored under:

```text
artifacts/gate8/main_v1/
```

Expected subdirectories:

- `runs/`
- `metrics/`
- `logs/`
- `reports/`

Gate 8F creates none of these result files.
````

- [ ] **Step 2: Create provider readiness doc**

Create `docs/model-provider-readiness.md` with:

```markdown
# Model Provider Readiness

Gate 8F defines provider-selection evidence requirements without selecting a provider. Provider availability, model versions, and prices are temporally unstable, so no provider or price may be treated as locked until checked against official sources at execution time.

## Current Decision

Provider selection is not complete:

- `selected: false`
- `provider: unset`
- `model: unset`
- `run_authorized: false`

This is intentional. A later provider and prompt freeze gate must make the selection explicitly.

## Required Future Evidence

Before any main baseline can run, the provider decision record must include:

- official pricing URL checked on the run date
- official model documentation URL checked on the run date
- provider name
- model id and version or release date
- context window
- maximum output limit
- deterministic generation settings
- rate-limit or throughput note
- data retention or privacy note
- API key or local runtime availability note
- approved cost budget note

## Disallowed Evidence

The project must reject:

- stale prices copied from reports or old notes
- undocumented model aliases
- provider claims without official URLs
- hidden API keys in tracked files
- prompt versions described only in prose
- runs that cannot reproduce model id, config, prompt version, and cost assumptions

## Prompt And Config Freeze

Prompt and config readiness requires:

- a stable prompt version id for each baseline family
- a generation config version id
- deterministic settings where supported
- answer style shared across comparable baselines
- max evidence budget shared across comparable baselines
- refusal behavior consistent with `docs/baseline-protocol.md`

Gate 8F documents these requirements but does not write final prompt text.
```

- [ ] **Step 3: Verify docs contain required lockout terms**

Run:

```powershell
Select-String -Path docs\gate8-run-config-readiness.md,docs\model-provider-readiness.md -Pattern 'authorized_to_run|selected: false|run_authorized: false|provider is unselected|official pricing|does not authorize'
```

Expected: output lines proving both docs state non-executable semantics and provider lockout.

- [ ] **Step 4: Commit Gate 8F docs**

Run:

```powershell
git add docs/gate8-run-config-readiness.md docs/model-provider-readiness.md
git commit -m "docs: add gate8f readiness docs"
```

---

### Task 2: Add Gate 8F YAML Metadata

**Files:**
- Create: `configs/gate8/main_v1_run_matrix.yaml`
- Create: `configs/gate8/provider_decision.yaml`

- [ ] **Step 1: Create main v1 run matrix**

Create `configs/gate8/main_v1_run_matrix.yaml` with:

```yaml
version: 1
gate: gate8_main_comparison
stage: gate8f_run_config_readiness
status: readiness_in_progress
authorized_to_run: false
purpose: non_executable_run_matrix
source_snapshot_registry: snapshots/main_v1/source_snapshots.json
baseline_contract: docs/baseline-contract.yaml
metric_contract: docs/metric-contract.yaml
provider_decision: configs/gate8/provider_decision.yaml

datasets:
  - dataset_id: hotpotqa
    name: HotpotQA
    split: dev_distractor
    source_snapshot_id: hotpotqa_dev_distractor_official_78487b5e57e5423c
    source_snapshot_registry_path: snapshots/main_v1/source_snapshots.json
    retrieval_index_path: datasets/retrieval_indexes/main_v1/hotpotqa/dev_distractor/index_manifest.json
    question_source: datasets/source_snapshots/hotpotqa/dev_distractor/processed/questions.jsonl
    artifact_root: artifacts/gate8/main_v1/hotpotqa/dev_distractor
  - dataset_id: 2wikimultihopqa
    name: 2WikiMultihopQA
    split: dev
    source_snapshot_id: 2wikimultihopqa_dev_official_4ad66154ea407847
    source_snapshot_registry_path: snapshots/main_v1/source_snapshots.json
    retrieval_index_path: datasets/retrieval_indexes/main_v1/2wikimultihopqa/dev/index_manifest.json
    question_source: datasets/source_snapshots/2wikimultihopqa/dev/processed/questions.jsonl
    artifact_root: artifacts/gate8/main_v1/2wikimultihopqa/dev
  - dataset_id: musique
    name: MuSiQue
    split: dev
    source_snapshot_id: musique_dev_official_4b485a716c1a4fc6
    source_snapshot_registry_path: snapshots/main_v1/source_snapshots.json
    retrieval_index_path: datasets/retrieval_indexes/main_v1/musique/dev/index_manifest.json
    question_source: datasets/source_snapshots/musique/dev/processed/questions.jsonl
    artifact_root: artifacts/gate8/main_v1/musique/dev

baseline_families:
  - baseline_family: vanilla_rag
    requires_provider: true
    requires_generation: true
    requires_verifier: false
    requires_ledger: false
    retrieval_dependency: lexical_index_ready
    authorized_to_run: false
  - baseline_family: hybrid_rag
    requires_provider: true
    requires_generation: true
    requires_verifier: false
    requires_ledger: false
    retrieval_dependency: blocked_until_hybrid_retrieval_locked
    authorized_to_run: false
  - baseline_family: citation_only
    requires_provider: true
    requires_generation: true
    requires_verifier: false
    requires_ledger: false
    retrieval_dependency: lexical_index_ready
    authorized_to_run: false
  - baseline_family: validator_only
    requires_provider: true
    requires_generation: true
    requires_verifier: true
    requires_ledger: false
    retrieval_dependency: lexical_index_ready
    authorized_to_run: false
  - baseline_family: ledger_only
    requires_provider: true
    requires_generation: true
    requires_verifier: false
    requires_ledger: true
    retrieval_dependency: lexical_index_ready
    authorized_to_run: false
  - baseline_family: ledger_validator
    requires_provider: true
    requires_generation: true
    requires_verifier: true
    requires_ledger: true
    retrieval_dependency: lexical_index_ready
    authorized_to_run: false

metric_groups:
  - retrieval
  - answer_quality
  - attribution
  - system
  - aggregation

shared_run_constraints:
  same_question_list: required
  same_source_snapshot: required
  same_evidence_budget: required
  same_answer_style: required
  same_metric_contract: required
  prompt_versions_locked: false
  provider_selected: false

artifact_paths:
  root: artifacts/gate8/main_v1
  runs: artifacts/gate8/main_v1/runs
  metrics: artifacts/gate8/main_v1/metrics
  logs: artifacts/gate8/main_v1/logs
  reports: artifacts/gate8/main_v1/reports
  created_by_this_config: false

blocked_reasons:
  - provider_unselected
  - prompt_versions_unlocked
  - cost_budget_unapproved
  - hybrid_retrieval_not_locked
  - execution_card_missing
  - reproducibility_review_unfinished
```

- [ ] **Step 2: Create provider decision metadata**

Create `configs/gate8/provider_decision.yaml` with:

```yaml
version: 1
gate: gate8_main_comparison
stage: gate8f_provider_readiness
status: readiness_in_progress
selected: false
provider: unset
model: unset
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

required_future_evidence:
  - official_pricing_url_checked_on_run_date
  - official_model_docs_url_checked_on_run_date
  - provider_name
  - model_id_and_version_or_date
  - context_window
  - max_output_limit
  - deterministic_generation_settings
  - rate_limit_or_throughput_note
  - data_retention_or_privacy_note
  - api_key_or_local_runtime_availability_note
  - approved_cost_budget_note

disallowed_evidence:
  - stale_prices_from_reports_or_old_notes
  - undocumented_model_aliases
  - provider_claims_without_official_urls
  - tracked_api_keys_or_secrets
  - prompt_versions_described_only_in_prose
  - runs_without_reproducible_model_config_prompt_and_cost_assumptions

prompt_config_requirements:
  prompt_version_per_baseline_family: required_later
  generation_config_version: required_later
  deterministic_settings: required_later
  shared_answer_style: required_later
  shared_max_evidence_budget: required_later
  refusal_behavior: must_match_docs_baseline_protocol
```

- [ ] **Step 3: Verify YAML metadata terms**

Run:

```powershell
Select-String -Path configs\gate8\main_v1_run_matrix.yaml,configs\gate8\provider_decision.yaml -Pattern 'authorized_to_run: false|selected: false|run_authorized: false|hotpotqa|2wikimultihopqa|musique|vanilla_rag|hybrid_rag|ledger_validator|official_pricing_url_checked_on_run_date'
```

Expected: output includes all three datasets, six baseline markers by category, provider lockout fields, and official evidence requirements.

- [ ] **Step 4: Commit YAML metadata**

Run:

```powershell
git add configs/gate8/main_v1_run_matrix.yaml configs/gate8/provider_decision.yaml
git commit -m "docs: add gate8f run matrix metadata"
```

---

### Task 3: Update Readiness Index Docs And Experiment Card

**Files:**
- Modify: `README.md`
- Modify: `docs/main-comparison-readiness.md`
- Modify: `configs/gate8/main_v1_readiness.yaml`
- Create: `experiments/cards/E011-gate8-run-config-readiness.md`

- [ ] **Step 1: Update README project structure**

Add these bullets near the existing Gate 8 docs/config bullets:

```markdown
- `docs/gate8-run-config-readiness.md` - non-executable Gate 8 run matrix rules
- `docs/model-provider-readiness.md` - provider selection and current-price evidence rules
- `configs/gate8/main_v1_run_matrix.yaml` - non-executable main v1 dataset/baseline matrix
- `configs/gate8/provider_decision.yaml` - provider decision metadata with execution fields unset
```

- [ ] **Step 2: Update main comparison readiness doc**

Add this section after the Gate 8E section:

````markdown
Gate 8F locks non-executable run matrix and provider-readiness metadata:

```powershell
configs/gate8/main_v1_run_matrix.yaml
configs/gate8/provider_decision.yaml
```

These files may define the future dataset/baseline matrix and provider evidence requirements, but they do not select a provider, freeze prompts, approve budget, run baselines, or pass Gate 8.
````

- [ ] **Step 3: Update Gate 8 readiness config**

In `configs/gate8/main_v1_readiness.yaml`, add references near the existing top-level readiness metadata:

```yaml
run_matrix: configs/gate8/main_v1_run_matrix.yaml
provider_decision: configs/gate8/provider_decision.yaml
```

Add these `not_ready` entries if absent:

```yaml
  - provider_decision_unlocked
  - run_matrix_non_executable
```

Do not change `authorized_to_run: false`.

- [ ] **Step 4: Add E011 experiment card**

Create `experiments/cards/E011-gate8-run-config-readiness.md` with:

````markdown
# E011 Gate 8 Run Config Readiness

## Purpose

Create non-executable Gate 8F run matrix and provider-readiness metadata. This card authorizes metadata creation only.

## Authorized Scope

- document main v1 run matrix rules
- document provider selection evidence requirements
- create `configs/gate8/main_v1_run_matrix.yaml`
- create `configs/gate8/provider_decision.yaml`
- keep provider unselected
- keep run authorization disabled

## Prohibited Actions

- model calls
- embedding calls
- reranker calls
- retrieval evaluation
- baseline execution
- metric computation
- result artifact creation
- provider selection
- price claims without official run-date verification
- source snapshot status promotion to `ready`

## Expected Outputs

- `docs/gate8-run-config-readiness.md`
- `docs/model-provider-readiness.md`
- `configs/gate8/main_v1_run_matrix.yaml`
- `configs/gate8/provider_decision.yaml`
- README and readiness doc references

## Success Criteria

- run matrix lists HotpotQA, 2WikiMultihopQA, and MuSiQue
- run matrix lists all six Gate 5 baseline families
- provider decision keeps `selected: false`
- provider decision keeps `run_authorized: false`
- Gate 8 readiness still reports `gate8_ready: false`

## Cost Class

Documentation and metadata only. No model/API/provider cost is authorized.
````

- [ ] **Step 5: Run documentation scan**

Run:

```powershell
Select-String -Path docs\*.md,docs\superpowers\*.md,docs\superpowers\*\*.md,experiments\cards\*.md,README.md,configs\gate8\*.yaml -Pattern 'TB[D]|TO[D]O|turn[0-9]+'
```

Expected: no output.

- [ ] **Step 6: Commit docs/card/index updates**

Run:

```powershell
git add README.md docs/main-comparison-readiness.md configs/gate8/main_v1_readiness.yaml experiments/cards/E011-gate8-run-config-readiness.md
git commit -m "docs: document gate8f run config readiness"
```

---

### Task 4: Final Verification

**Files:**
- No new files.
- Verify all files from Tasks 1 through 3.

- [ ] **Step 1: Verify required files exist**

Run:

```powershell
Test-Path docs\gate8-run-config-readiness.md
Test-Path docs\model-provider-readiness.md
Test-Path configs\gate8\main_v1_run_matrix.yaml
Test-Path configs\gate8\provider_decision.yaml
Test-Path experiments\cards\E011-gate8-run-config-readiness.md
```

Expected: five `True` lines.

- [ ] **Step 2: Verify matrix and provider lockout fields**

Run:

```powershell
Select-String -Path configs\gate8\main_v1_run_matrix.yaml -Pattern 'hotpotqa|2wikimultihopqa|musique|vanilla_rag|hybrid_rag|citation_only|validator_only|ledger_only|ledger_validator|authorized_to_run: false'
Select-String -Path configs\gate8\provider_decision.yaml -Pattern 'selected: false|provider: unset|model: unset|run_authorized: false|official_pricing_url_checked_on_run_date|prompt_versions_locked: false'
```

Expected: output covers all datasets, all baselines, and provider lockout fields.

- [ ] **Step 3: Verify Gate 8 remains blocked**

Run:

```powershell
python scripts/check_gate8_snapshot_readiness.py --registry snapshots/main_v1/source_snapshots.json
```

Expected: JSON output includes `gate8_ready: false` and only status blockers for the three source snapshots.

- [ ] **Step 4: Run regression tests**

Run:

```powershell
python -m pytest tests/test_gate8_snapshot_readiness.py tests/test_gate8_lexical_index.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Verify no generated result artifacts were staged**

Run:

```powershell
git status --short --ignored
git diff --check
```

Expected: no tracked dirty files after commits; ignored `artifacts/`, `datasets/`, PDFs, caches, and pycache may appear.

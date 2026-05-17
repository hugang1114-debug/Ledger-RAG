# Ledger-RAG Paper Base

This repository is the project base for a Ledger-RAG research paper. The goal is to evaluate whether an external deterministic evidence ledger can improve evidence traceability, auditability, and long-task stability in deep-research agents.

The current phase is project foundation plus readiness planning:

- verify and collect core papers
- define the research boundary
- define experiment progress gates
- create agent rules for future work
- prepare literature metadata
- validate a synthetic offline pilot for artifact shape
- prepare Gate 8 readiness without running main baselines

This repository is not yet a main experiment runner or model implementation. The Gate 7 pilot is synthetic and offline; it validates contract-shaped artifacts only.

## Gate Status

- Gate 1: Project Base Ready - completed
- Gate 2: Literature Verified - completed for the 19-paper core pack
- Gate 3: Research Claim Locked - completed
- Gate 4: Dataset Feasibility Locked - completed
- Gate 5: Baseline Protocol Locked - completed
- Gate 6: Metric Protocol Locked - completed
- Gate 7: Pilot Experiment Passed - completed
- Gate 8: Main Comparison Passed - readiness in progress

The next work item is to prepare main comparison readiness: locked source snapshot rules, a non-executable run matrix, and checks for dataset snapshots, retrieval indexes, model/provider choice, cost budget, and reproducible execution. Provider candidate evidence is partially locked for OpenAI `gpt-5.4-mini`, Gate 8L freezes candidate prompt/config artifacts, Gate 8M records GPT-5.4 and DeepSeek-V4-Pro as provider candidates with a 10 USD smoke-run budget preflight, Gate 8N selects DeepSeek-V4-Pro as the primary provider for the first smoke/main-v1 path, Gate 8O authorizes only a DeepSeek smoke run under the existing 10 USD ceiling, Gate 8P adds and executes a one-question DeepSeek smoke harness, Gate 8Q reviews the smoke artifacts into a tracked hash/cost summary, and Gate 8R locks DeepSeek provider evidence while keeping main execution blocked. GPT-5.4 remains optional credibility-check evidence. Final prompt/config authorization, full execution authorization, and main baselines remain unset. Gate 8 is not passed until real main baselines run on locked source snapshots and produce comparable run and metric records.

## Current Structure

- `AGENTS.md` - rules for future agents and contributors
- `docs/project-boundary.md` - research scope and reality corrections
- `docs/experiment-flow.md` - progress-gated experiment flow
- `docs/research-claim.md` - falsifiable main claim and negative scope
- `docs/claim-to-experiments.md` - mapping from claim components to experiment families
- `docs/dataset-feasibility.md` - dataset shortlist, deferrals, exclusions, and source notes
- `docs/dataset-decision-matrix.yaml` - structured dataset feasibility decisions
- `docs/baseline-protocol.md` - baseline family definitions and comparison rules
- `docs/baseline-contract.yaml` - shared run input/output contract for future baselines
- `docs/metric-protocol.md` - metric definitions, applicability, aggregation, and reporting rules
- `docs/metric-contract.yaml` - structured metric output contract for future runs
- `docs/main-comparison-readiness.md` - Gate 8 readiness requirements and blockers
- `docs/source-snapshot-protocol.md` - immutable source snapshot rules for main comparisons
- `docs/gate8-run-config-readiness.md` - non-executable Gate 8 run matrix rules
- `docs/model-provider-readiness.md` - provider selection and current-price evidence rules
- `docs/gate8-freeze-readiness.md` - Gate 8G provider, prompt, budget, and execution freeze rules
- `docs/gate8-prompt-config-readiness.md` - Gate 8H prompt/config registry rules
- `docs/gate8-provider-evidence-readiness.md` - Gate 8I provider evidence registry readiness rules
- `docs/gate8-snapshot-index-promotion.md` - Gate 8J source snapshot and local index promotion rules
- `docs/gate8-provider-comparison.md` - Gate 8M provider and budget candidate comparison
- `configs/gate8/main_v1_readiness.yaml` - non-executable Gate 8 readiness matrix
- `configs/gate8/main_v1_run_matrix.yaml` - non-executable main v1 dataset/baseline matrix
- `configs/gate8/provider_decision.yaml` - DeepSeek provider decision metadata with execution fields unset
- `configs/gate8/provider_candidates.yaml` - non-executable GPT-5.4 and DeepSeek-V4-Pro candidate registry
- `configs/gate8/budget_preflight.yaml` - non-executable smoke and main budget preflight scope
- `configs/gate8/deepseek_smoke_result_summary.yaml` - tracked summary of reviewed Gate 8P smoke artifacts
- `configs/gate8/provider_evidence_registry.yaml` - non-executable DeepSeek provider evidence registry
- `configs/gate8/freeze_readiness.yaml` - non-executable freeze readiness metadata
- `configs/gate8/prompt_registry.yaml` - non-executable prompt slot registry
- `configs/gate8/generation_config_registry.yaml` - non-executable generation config slot registry
- `snapshots/main_v1/source_snapshots.json` - source snapshot and local retrieval index registry for main v1 datasets
- `experiments/cards/E016-gate8k-openai-provider-evidence-candidate-lock.md` - Gate 8K non-running provider candidate lock card
- `scripts/check_gate8_snapshot_readiness.py` - local metadata readiness checker for Gate 8 snapshots
- `scripts/check_gate8_freeze_readiness.py` - local execution-preflight readiness checker
- `scripts/check_gate8_prompt_config_readiness.py` - local prompt/config registry readiness checker
- `scripts/check_gate8_provider_evidence_readiness.py` - local provider evidence registry readiness checker
- `scripts/check_gate8_provider_budget_preflight.py` - local provider/budget preflight readiness checker
- `experiments/cards/E020-gate8o-deepseek-smoke-run-authorization.md` - smoke-only DeepSeek authorization card
- `experiments/cards/E023-gate8r-deepseek-provider-evidence-lock.md` - DeepSeek provider evidence lock card
- `scripts/check_gate8_snapshot_index_promotion.py` - local snapshot/index promotion readiness checker
- `scripts/promote_gate8_snapshot_indexes.py` - metadata-only snapshot/index promotion command
- `scripts/build_hotpotqa_source_snapshot.py` - official-source HotpotQA dev distractor snapshot builder
- `scripts/build_2wiki_source_snapshot.py` - official-source 2WikiMultihopQA dev snapshot builder
- `scripts/build_musique_source_snapshot.py` - official-source MuSiQue answerable dev snapshot builder
- `scripts/build_gate8_lexical_indexes.py` - local deterministic lexical index builder for Gate 8E readiness
- `scripts/run_gate8p_deepseek_smoke.py` - one-question DeepSeek smoke-run CLI
- `scripts/review_gate8p_smoke_result.py` - smoke artifact reviewer and summary writer
- `fixtures/gate7_offline/pilot.json` - tracked synthetic fixture for the offline pilot
- `src/ledger_rag_pilot/` - standard-library-only offline pilot modules
- `src/ledger_rag_smoke/` - standard-library-only DeepSeek smoke-run helpers
- `literature/manifest.yaml` - verified paper metadata and download records
- `literature/papers/` - local downloaded PDFs, ignored by git
- `experiments/README.md` - experiment card requirements
- `scripts/download_papers.ps1` - official-source paper downloader

## Core Principle

The feasibility report is an input, not a source of truth. Every paper, dataset, benchmark, price, API, and experimental claim must be independently verified before it can support the paper.

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

The next work item is to prepare main comparison readiness: locked source snapshot rules, a non-executable run matrix, and checks for dataset snapshots, retrieval indexes, model/provider choice, cost budget, and reproducible execution. Gate 8 is not passed until real main baselines run on locked source snapshots and produce comparable run and metric records.

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
- `configs/gate8/main_v1_readiness.yaml` - non-executable Gate 8 readiness matrix
- `snapshots/main_v1/source_snapshots.json` - pending source snapshot registry for main v1 datasets
- `scripts/check_gate8_snapshot_readiness.py` - local metadata readiness checker for Gate 8 snapshots
- `scripts/build_hotpotqa_source_snapshot.py` - official-source HotpotQA dev distractor snapshot builder
- `scripts/build_2wiki_source_snapshot.py` - official-source 2WikiMultihopQA dev snapshot builder
- `scripts/build_musique_source_snapshot.py` - official-source MuSiQue answerable dev snapshot builder
- `fixtures/gate7_offline/pilot.json` - tracked synthetic fixture for the offline pilot
- `src/ledger_rag_pilot/` - standard-library-only offline pilot modules
- `literature/manifest.yaml` - verified paper metadata and download records
- `literature/papers/` - local downloaded PDFs, ignored by git
- `experiments/README.md` - experiment card requirements
- `scripts/download_papers.ps1` - official-source paper downloader

## Core Principle

The feasibility report is an input, not a source of truth. Every paper, dataset, benchmark, price, API, and experimental claim must be independently verified before it can support the paper.

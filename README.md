# Ledger-RAG Paper Base

This repository is the project base for a Ledger-RAG research paper. The goal is to evaluate whether an external deterministic evidence ledger can improve evidence traceability, auditability, and long-task stability in deep-research agents.

The current phase is project foundation only:

- verify and collect core papers
- define the research boundary
- define experiment progress gates
- create agent rules for future work
- prepare literature metadata

This repository is not yet an experiment runner or model implementation.

## Current Structure

- `AGENTS.md` - rules for future agents and contributors
- `docs/project-boundary.md` - research scope and reality corrections
- `docs/experiment-flow.md` - progress-gated experiment flow
- `literature/manifest.yaml` - verified paper metadata and download records
- `literature/papers/` - local downloaded PDFs, ignored by git
- `experiments/README.md` - experiment card requirements
- `scripts/download_papers.ps1` - official-source paper downloader

## Core Principle

The feasibility report is an input, not a source of truth. Every paper, dataset, benchmark, price, API, and experimental claim must be independently verified before it can support the paper.


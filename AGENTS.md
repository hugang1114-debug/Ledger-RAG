# Ledger-RAG Project Agent Rules

This file applies to the whole repository.

## Project Purpose

This repository is the research base for a Ledger-RAG paper project. The current phase is not model training or full system implementation. The priority is to build a reproducible research foundation: verified literature, clear project boundaries, experiment gates, and durable metadata.

## Non-Negotiable Rules

- Do not trust the feasibility report as a source of truth. Treat it as an initial hypothesis document.
- Do not use `turn...` links from the report as citations, download URLs, or official sources.
- Do not run experiments without an experiment card under `experiments/cards/`.
- Do not add a result to the paper narrative unless the source, code/config, dataset version, model version, and metric definition are recorded.
- Do not use dynamic web pages, Common Crawl, or high-risk domains as first-version main experiments.
- Do not claim Ledger-RAG is a universal long-context replacement. The first-version claim is evidence traceability, auditability, and long-task stability.
- Do not use reported model/API/cloud prices without re-checking official pricing at execution time.

## Literature Rules

- Prefer official paper sources: ACL Anthology, arXiv, OpenReview, NeurIPS/ICLR proceedings, or the authors' official repository.
- Store downloaded PDFs in `literature/papers/`.
- Keep PDF files local by default. They are ignored by git; track provenance in `literature/manifest.yaml`.
- If a PDF cannot be verified from an official source, record only the landing page and mark the entry as `landing_only`.
- When adding or replacing a paper, update title, year, official URL, PDF URL, local path, download status, SHA256 if downloaded, and notes.

## Experiment Gate Rules

Experiments advance by gates, not dates:

1. Project Base Ready
2. Literature Verified
3. Research Claim Locked
4. Dataset Feasibility Locked
5. Baseline Protocol Locked
6. Metric Protocol Locked
7. Pilot Experiment Passed
8. Main Comparison Passed
9. Ablation / Stress Passed
10. Paper Package Ready

Before running an experiment, create an experiment card that states:

- research question
- dataset and license status
- method variants and baselines
- metrics
- failure criteria
- exact command/config to run
- output paths
- expected cost class

## Scope Defaults

- First-version attribution granularity: atomic claim or sentence level.
- First-version evidence source: static, versioned, replayable snapshots.
- TRACE-style RL or training-level optimization is related work, not a v1 baseline.
- LOCA-bench is a later agent-context stress test, not a first-batch main experiment.
- LongBench-Cite, L-CiteEval, and SUnsET toolchains must be feasibility-checked before they become main experiments.

## File Hygiene

- Keep generated datasets, indexes, model weights, run outputs, and downloaded PDFs out of git unless explicitly approved.
- Keep tracked files focused on protocol, metadata, scripts, and reproducibility notes.
- Prefer small, auditable changes. Update docs when changing scope or gates.


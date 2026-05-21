# From Citation Strings to Evidence Pointers

This repository is now the project base for **a replayable attribution protocol for auditable RAG**. The core question is whether a versioned evidence ledger with stable span identifiers, deterministic citation validation, and semantic claim-to-span checking can reduce invalid citations, improve claim-level attribution coverage, and guarantee offline span replayability in RAG and deep-research agent workflows.

The contribution is attribution validity, auditability, and replayability. It is not a new general-purpose RAG architecture, not a claim that final answer accuracy improves, and not a claim that hallucination is solved.

We do not introduce new model weights. We propose a model-agnostic attribution audit protocol based on replayable evidence pointers, deterministic validation, and calibrated semantic evaluation.

## Current Direction

- Treat generation and audit as separate layers.
- Do not trust model-generated citation IDs.
- Validate citation pointers deterministically against retrieved evidence and ledger spans.
- Evaluate semantic support separately from structural citation validity.
- Preserve Gate 1-8 artifacts as historical diagnostics.
- Treat the current Gate 8 mini-main results as diagnostic evidence only, not paper-grade main comparison evidence.
- Keep lexical support rate as a debugging diagnostic, not a core paper metric.

## System Components vs Evaluation Judges

Baseline methods are systems under test. A semantic verifier is a module inside a system variant when it checks or filters generated claims before final output.

An LLM-as-a-Judge is an offline evaluator used to score outputs from all variants. DeepSeek-V4-Pro is treated as an offline judge unless an experiment explicitly places it inside a system variant. DeepSeek judge labels are machine judge labels, not human gold labels.

Structural metrics are computed deterministically from citation pointers, retrieved evidence, and ledger spans. Semantic metrics are computed offline and separately, currently using the calibrated DeepSeek-V4-Pro LLM-as-a-Judge pipeline for diagnostics.

## Claims We Can Make

- The protocol can improve citation ID validity when deterministic validation is enforced.
- The protocol can improve offline replayability through source snapshot and span hash checks.
- The protocol separates structural citation validation from semantic support validation.
- The protocol is designed to reduce citation laundering compared with citation-only prompting.

## Claims We Cannot Make Yet

- The system improves final answer accuracy.
- The system solves hallucination.
- The ledger is cryptographically tamper-proof.
- DPO or SFT guarantees citation correctness.
- The ledger alone guarantees semantic faithfulness.
- The project replaces long-context models.

## Core Metrics

- Invalid Citation Rate
- Citation ID Validity Rate
- Claim Citation Coverage
- Citation Precision / Entailment Support Rate
- Overclaim Rate
- Span Replay Success Rate
- Snapshot Replay Success Rate
- Refusal Precision
- Cost per audited claim
- Latency per audited claim

## Baseline Methods

- Vanilla RAG
- Citation-only Prompting
- Semantic Verifier Only, No Ledger
- Ledger Pointer Only
- Ledger + Deterministic Validator
- Ledger + Deterministic Validator + Semantic Verifier

## Current Structure

- `AGENTS.md` - contributor rules for the attribution-ledger direction
- `docs/project-boundary.md` - current scope, non-goals, and boundary rules
- `docs/research-claim.md` - falsifiable attribution-protocol claim
- `docs/citation-pointer-schema.md` - formal citation pointer schema and validation checks
- `docs/claim-to-experiments.md` - mapping from claim components to experiment families
- `docs/baseline-protocol.md` - revised baseline families for attribution protocol evaluation
- `docs/baseline-contract.yaml` - shared run input/output contract
- `docs/metric-protocol.md` - core metric definitions and aggregation rules
- `docs/metric-contract.yaml` - structured metric output contract
- `docs/ledger-stress-tests.md` - ledger-specific stress-test designs
- `docs/future-sft-dpo-design.md` - future training plan, intentionally not implemented yet
- `docs/human-annotation-plan.md` - human evaluation and judge calibration plan
- `docs/gate8-main-v1-diagnosis.md` - diagnostic Gate 8 result interpretation
- `docs/gate8-claim-citation-audit.md` - diagnostic citation audit interpretation
- `src/ledger_rag_attribution/` - deterministic citation pointer helpers
- `src/ledger_rag_pilot/` - historical standard-library offline pilot modules
- `src/ledger_rag_main/` - Gate 8 diagnostic mini-run helpers
- `src/ledger_rag_snapshot/` - source snapshot helpers
- `configs/gate8/` - Gate 8 readiness and diagnostic result metadata
- `experiments/cards/` - historical experiment cards
- `snapshots/main_v1/source_snapshots.json` - source snapshot registry

## Gate Status

Gate 1-8 artifacts remain part of the repository as historical diagnostics. Gate 8 mini-main and corrected runs exposed useful attribution failure modes, especially invalid citation IDs and weak citation support, but they are not paper-grade evidence. The next phase should validate the deterministic attribution protocol on small, inspectable examples before spending on larger model runs.

## Core Principle

The model may propose citations, but the audit layer decides whether those citations are valid. Citation ID validity, retrieved-evidence membership, replayability, and semantic entailment are separate checks with separate metrics.

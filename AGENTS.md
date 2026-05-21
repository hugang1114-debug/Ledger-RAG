# Project Direction

This repository is no longer primarily about improving RAG answer accuracy.

The project is now focused on auditable attribution for RAG / deep-research agent workflows.

## Core Research Goal

Build and evaluate a versioned, replayable evidence ledger with stable span identifiers, deterministic citation validation, and semantic claim-to-span attribution checking.

The system should measure and improve:
- citation ID validity
- claim-level citation coverage
- semantic entailment support
- replayability of cited spans
- auditability of generated answers

## Non-Goals

Do not claim:
- this is a new general-purpose RAG architecture
- this improves final answer accuracy unless explicitly proven
- this solves hallucination
- this replaces long-context models
- this is cryptographically tamper-proof unless cryptographic audit logs are implemented
- DPO/SFT guarantees citation correctness

## Engineering Rules

- Do not trust model-generated citation IDs.
- Citation IDs must be checked deterministically.
- Semantic support must be evaluated separately from structural citation validity.
- Lexical overlap may be used for debugging, but not as a core metric.
- Preserve old Gate 1-8 artifacts as historical diagnostics.
- Treat the current Gate 8 mini-main run as diagnostic, not paper-grade evidence.
- Prefer small, testable changes over broad rewrites.
- Every new validator or metric must include minimal tests.

## Required Evaluation Categories

Core metrics:
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
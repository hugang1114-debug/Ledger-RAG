# Project Boundary

## Research Claim

The first-version paper should test this claim:

> In RAG and deep-research agent workflows, moving from free-form citation strings to versioned evidence pointers with deterministic validation and semantic attribution checks can reduce invalid citations, improve claim-level citation coverage, and guarantee offline replay of cited spans.

This is an attribution protocol claim. It is not a claim that final answer accuracy improves, that hallucination is solved, or that the ledger replaces long-context models.

## In Scope

- Evidence ledger design for datasets, sources, snapshots, spans, claims, citations, and verdicts.
- Stable citation pointers with dataset, source, snapshot, span, and span-hash fields.
- Deterministic checks for source existence, snapshot replay, span existence, span hash consistency, and retrieved-evidence membership.
- Semantic claim-to-span support evaluation as a separate layer after structural validation.
- Stress tests for invalid IDs, re-chunking, source version drift, evidence position shift, and conflicting evidence.
- Cost and latency per audited claim.
- Historical Gate 1-8 artifacts as diagnostics.

## Out of Scope for v1

- Claims that Ledger-RAG is a new general-purpose RAG architecture.
- Claims that the protocol improves final answer accuracy unless later experiments prove it.
- Claims that the protocol solves hallucination.
- Claims that the ledger is cryptographically tamper-proof without cryptographic audit logs.
- Training-based guarantees of citation correctness.
- Token-level attribution.
- Dynamic web browsing as a main experiment source.
- High-risk medical, legal, or financial domains.
- Product UI or production-grade agent orchestration.

## Boundary Rules

- Treat generation and audit as separate layers.
- Do not trust model-generated citation IDs.
- Reject, sanitize, or explicitly count invalid citation IDs.
- Keep structural citation validity separate from semantic support.
- Use lexical overlap only as a debugging diagnostic.
- Treat current Gate 8 mini-main results as diagnostic only.
- Do not scale Gate 8 by sample size alone before fixing attribution mechanics.

## Foundation Success Criteria

- The repository documents the attribution protocol and non-goals clearly.
- Citation pointers can be parsed and checked deterministically.
- Minimal validator tests cover invalid IDs, retrieved-evidence membership, hash mismatch, replay behavior, and semantic failure labels.
- Future experiments name the attribution metric they test and the failure condition that would falsify the claim.

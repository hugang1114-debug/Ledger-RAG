# Ledger-RAG Project Boundary

## Research Claim

The first-version paper should test this claim:

> In deep-research agent workflows, moving evidence into a versioned, replayable ledger with stable span identifiers and independent claim verification can improve evidence traceability, auditability, and long-task stability at acceptable engineering cost.

This project should not claim that Ledger-RAG is a universal replacement for long-context models or that it always improves answer accuracy.

## In Scope

- Deterministic evidence ledger design: documents, chunks, spans, claims, citations, verdicts.
- Atomic-claim or sentence-level attribution.
- Static, replayable source snapshots.
- Baselines that isolate retrieval, citation generation, ledger storage, and verification effects.
- Metrics split by retrieval quality, answer quality, attribution quality, and system cost.
- Reproducible metadata: dataset versions, model versions, prompts, configs, seeds, and output paths.

## Out of Scope for v1

- Token-level attribution.
- Training or RL optimization for traceability.
- Dynamic web browsing as a main experiment source.
- High-risk medical, legal, or financial domains.
- Product UI or production-grade agent orchestration.
- Claims based only on the original feasibility report.

## Reality Corrections

- The project should advance by experiment gates, not by a fixed 24-week timeline.
- TRACE is relevant related work but should not be a v1 executable baseline unless its training and reproduction cost is explicitly accepted.
- LOCA-bench is valuable for later agent-context stress testing, but it is not the first main experiment.
- LongBench-Cite, L-CiteEval, and SUnsET may have non-trivial tooling and data assumptions; they require feasibility checks before becoming main experiments.
- Budget estimates must be checked against official pricing at execution time.
- PDF/HTML parsing drift is a core risk. Any span identity design must record source hashes, parser versions, and local span hashes.
- The first reproducible corpus should prefer official static datasets and snapshots over live web data.

## Success Criteria for the Foundation Phase

- Repository contains clear agent rules and project boundaries.
- Core literature is downloaded or marked with a verified official landing page.
- Paper metadata records official provenance.
- Later contributors can see exactly what gate is next before writing code or running experiments.


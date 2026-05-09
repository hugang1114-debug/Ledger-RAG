# Baseline Protocol

Gate 5 locks the comparison protocol. It does not authorize implementation code, dataset downloads, or experiment runs.

## Shared Comparison Rules

All baseline families must use the same dataset split, question list, corpus snapshot, answer style, maximum evidence budget, and reporting schema. A result is not comparable if one method sees a different corpus, a larger evidence budget, a different answer format, or hidden gold evidence that another method does not receive.

All methods may use the question text and the retrieved evidence assigned to that run. A method may use gold supporting facts only in explicitly labeled oracle-retrieval diagnostics. Oracle runs are diagnostic only and cannot be reported as the main comparison.

Refusal behavior must be recorded for every method. A refusal, insufficient-evidence answer, or empty answer must count as a distinct outcome, not as a silent omission. If a method refuses more often than others, the analysis must report refusal rate alongside support and answer-quality metrics.

## Baseline Families

### Vanilla RAG

Vanilla RAG uses BM25 top-k retrieval plus answer generation. It has no explicit ledger persistence, no required citation format, and no verifier gate. If it outputs citations, they are treated as free-form model output unless they can be mapped back to retrieved evidence ids.

Allowed knowledge:

- question text
- ranked BM25 evidence for the run
- answer-style instructions

Not allowed:

- persistent ledger span ids
- semantic verifier feedback
- oracle evidence outside a diagnostic run

### Hybrid RAG

Hybrid RAG uses BM25 plus dense retrieval and reranking before answer generation. It has no explicit ledger persistence and no verifier gate. It exists to prevent the main result from being explained only by stronger retrieval.

Allowed knowledge:

- question text
- ranked hybrid evidence after reranking
- answer-style instructions

Not allowed:

- persistent ledger span ids
- semantic verifier feedback
- extra evidence budget beyond the shared maximum

### Citation-only

Citation-only receives retrieved evidence with evidence ids and must cite those ids in its output. It does not write evidence into a deterministic ledger, and no external verifier gates its answer.

Allowed knowledge:

- question text
- retrieved evidence ids and text
- citation-format instructions

Not allowed:

- semantic verifier feedback
- changing citation ids after generation
- claiming support from evidence not included in the retrieved set

### Validator-only

Validator-only first generates an ordinary RAG answer, then decomposes that answer into claims and checks them with a verifier. It does not use deterministic ledger storage or replayable span hashes.

Allowed knowledge:

- question text
- retrieved evidence text
- post-generation claim decomposition
- verifier labels: support, refute, insufficient

Not allowed:

- persistent ledger span ids
- source hash or replay guarantees
- using verifier results to retrieve new evidence unless the run is explicitly labeled as an iterative variant

### Ledger-only

Ledger-only stores retrieved evidence as replayable ledger spans and requires answers to cite ledger span ids. It performs deterministic citation checks, but it does not run a semantic support verifier.

Allowed knowledge:

- question text
- ledger span ids and quote text
- deterministic checks that cited span ids exist and replay

Not allowed:

- semantic support/refute/insufficient judgments
- post-hoc citation id substitution
- citations to spans outside the run ledger

### Ledger + Validator

Ledger + Validator is the full method. It uses replayable ledger span ids, deterministic citation checks, and semantic verifier verdicts for claim support.

Allowed knowledge:

- question text
- ledger span ids and quote text
- deterministic id/hash/replay checks
- verifier labels: support, refute, insufficient

Not allowed:

- hidden gold evidence in main runs
- dynamic web evidence unless a later gate explicitly authorizes it
- treating verifier acceptance as answer truth without reporting verifier uncertainty and failure modes

## Comparison Invariants

Every main run must record:

- dataset id and split
- question id and question text
- corpus snapshot id
- retrieval config and evidence budget
- generation model and prompt version
- answer text, atomic claims, citations, and verifier verdicts where applicable
- latency, cost, seed, code version, and config version

The six baseline families are comparable only if these fields are present under the shared contract in `docs/baseline-contract.yaml`.


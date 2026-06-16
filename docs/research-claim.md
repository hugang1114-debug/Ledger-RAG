# Research Claim

## Main Claim

The project should be framed as:

> From citation strings to evidence pointers: a replayable attribution protocol for auditable RAG.

The core research question is whether a versioned, replayable evidence ledger with stable span identifiers, deterministic citation validation, and semantic attribution checking can reduce invalid citations, improve claim-level attribution coverage, and guarantee offline span replayability in RAG and agentic research workflows.

## What This Separates

- Structural validity: the citation pointer is well formed, exists in the ledger, matches the source snapshot and span hash, and belongs to the retrieved evidence for the run.
- Semantic support: the cited span entails, partially supports, contradicts, or fails to support the associated claim.
- Generation behavior: the model may produce an answer and proposed citations, but those strings are not trusted until the deterministic audit layer validates them.

## Claims We Can Make

- The protocol improves citation ID validity when deterministic validation is enforced.
- The protocol improves replayability through snapshot and span hash checks.
- The protocol separates citation structure validation from semantic support validation.
- The protocol reduces citation laundering compared with citation-only prompting when invalid or unsupported citations are counted.

## Claims We Cannot Make

- The system improves final answer accuracy unless later experiments prove that separately.
- The system solves hallucination.
- The system is cryptographically tamper-proof unless cryptographic audit logs are implemented.
- DPO or SFT guarantees citation correctness.
- The ledger alone guarantees semantic faithfulness.
- The protocol replaces long-context models.

## Falsifiability

The claim is not supported if citation ID validity does not improve, cited spans cannot be replayed offline, semantic support rates do not improve over citation-only prompting, or gains depend on hidden gold evidence or model self-reported citation validity.

The claim is weakened if the system improves support metrics only by refusing most answers, if deterministic validation breaks under source drift, or if the cost per audited claim makes the protocol impractical.

## Success Criteria

A successful first-version result should show:

- lower Invalid Citation Rate than citation prompting only
- higher Claim Citation Coverage without hiding refusals
- higher Citation Precision / Entailment Support Rate
- measurable Overclaim Rate and reduced citation laundering
- high Span Replay Success Rate and Snapshot Replay Success Rate
- reported Cost per audited claim and Latency per audited claim
- clear human annotation and automatic judge calibration evidence

## Failure Criteria

The paper should report a negative or mixed result if:

- invalid citation IDs remain common after deterministic validation
- replay fails because source snapshots or span hashes do not match
- semantic verifier judgments are unstable against human labels
- the ledger improves citation format but not claim-to-span support
- results rely on lexical support rate as a core metric

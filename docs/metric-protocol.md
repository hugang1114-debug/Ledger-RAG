# Metric Protocol

This protocol defines core metrics for the auditable attribution direction. It does not authorize experiment execution.

## Reporting Principles

Report structural citation validity, semantic support, replayability, refusal behavior, and system cost separately. Do not collapse them into one score.

Structural citation validity must be computed deterministically from run records, retrieved evidence IDs, and ledger spans. Semantic support must be evaluated separately from pointer validity.

For current diagnostic experiments, structural metrics are computed deterministically and semantic metrics are computed offline using the calibrated DeepSeek-V4-Pro LLM-as-a-Judge pipeline. DeepSeek judge labels are machine judge labels, not gold labels.

Refusals must be included in denominators unless a metric explicitly says otherwise. Report refusal precision so conservative systems cannot hide attribution failures by refusing too often.

## System Components vs Evaluation Judges

Semantic Verifier refers to a module inside a system variant. It can influence generated outputs, refusals, or citation filtering.

LLM-as-a-Judge refers to an offline evaluator used to score all system variants after outputs are produced. DeepSeek-V4-Pro is used in this role unless a future experiment explicitly inserts it into a system variant.

These roles must not be conflated. A method name should describe the system under test, not the offline judge used to score it.

## Core Metrics

| Metric | Definition | Denominator | Failure signal |
|---|---|---:|---|
| Invalid Citation Rate | Fraction of emitted citation IDs with malformed, nonexistent, not-retrieved, wrong-snapshot, or wrong-span-hash status. | emitted citations | Model or protocol emits citation strings that cannot be audited. |
| Citation ID Validity Rate | Fraction of emitted citation IDs that pass deterministic structural validation. | emitted citations | Low value means citation IDs are not reliable evidence pointers. |
| Claim Citation Coverage | Fraction of answer claims with at least one structurally valid citation. | answer claims requiring evidence | Low value means claims are under-attributed. |
| Citation Precision / Entailment Support Rate | Fraction of structurally valid cited claim-span pairs judged entailed. | structurally valid claim-citation pairs | Low value means valid pointers are being used to launder unsupported claims. |
| Overclaim Rate | Fraction of claims that are only partially supported, contradictory, or stronger than cited evidence. | answer claims requiring evidence | Captures claims that cite relevant but insufficient evidence. |
| Span Replay Success Rate | Fraction of cited spans reconstructable from the ledger with matching span hash. | cited ledger spans | Low value means cited evidence is not replayable. |
| Snapshot Replay Success Rate | Fraction of cited source snapshots reconstructable with matching snapshot hash. | cited source snapshots | Low value means source version drift breaks auditability. |
| Refusal Precision | Fraction of refusals judged evidence-insufficient by gold labels, human labels, or calibrated verifier. | refusals | Low value means the system refuses instead of auditing hard claims. |
| Cost per audited claim | Total model/API/compute cost divided by audited claims. | audited claims | Reliability gain may be impractical. |
| Latency per audited claim | End-to-end audit latency divided by audited claims. | audited claims | Attribution protocol may be too slow for target workflows. |

## Semantic Support Metrics

Semantic-layer diagnostics are separate from structural citation validity. In current migrated diagnostics, DeepSeek-V4-Pro judge v2 can populate these fields offline:

- `entailment_support_rate`
- `unsupported_citation_rate`
- `partially_supported_rate`
- `contradictory_rate`
- `insufficient_evidence_rate`
- `semantic_evaluation_skip_rate`

Skipped semantic evaluations occur when structural validation failed or span text cannot be resolved. These semantic fields must identify `judge_model` and `judge_prompt_version` when an LLM-as-a-Judge is used. They must not be treated as human-calibrated paper-grade entailment until validated against human annotation.

DeepSeek v1 vs v2 comparisons are prompt stability diagnostics only. They are not judge reliability validation.

## Judge Reliability Plan

Judge reliability requires a separate human calibration study:

- sample 200-250 claim-citation pairs
- collect human labels using the allowed semantic support labels
- compute Human-DeepSeek accuracy, macro-F1, per-class precision/recall, and confusion matrix
- compute Cohen's kappa between human labels and DeepSeek labels
- if two human annotators are available, compute Human-Human Cohen's kappa
- if only one human annotator is available, do not claim Human-Human agreement

## Diagnostic Metrics

Lexical support rate may be used for debugging and triage only. It must not be reported as a core paper metric because token overlap is not semantic entailment.

Other diagnostics may include citation count per claim, weak lexical overlap examples, parser drift counts, and verifier disagreement examples.

## Retrieval and Answer-Quality Metrics

Retrieval metrics such as Recall@k, Precision@k, MRR, and nDCG remain useful for diagnosing whether attribution failures are caused by missing evidence. Answer-quality metrics such as EM and F1 may be reported for comparability, but they do not support the core attribution claim by themselves.

## Aggregation Rules

- Report macro averages across questions and dataset-level breakdowns.
- Keep diagnostic Gate 8 mini-main results separate from future paper-grade results.
- Report confidence intervals when sample size supports them.
- Keep oracle retrieval diagnostics separate from main results.
- Record `not_applicable` or `not_available` with reasons instead of silently dropping missing metrics.

## Metric Gate Rule

A runnable experiment card must list the exact metric denominators, missing-value handling, and whether the metric is structural, semantic, replay, refusal, cost, or diagnostic.

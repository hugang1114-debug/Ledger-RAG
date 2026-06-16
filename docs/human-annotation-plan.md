# Human Annotation Plan

## Goal

Create a small human-labeled evaluation set for claim-citation semantic support and automatic judge calibration.

## Initial Size

Annotate 200-500 claim-citation pairs from attribution runs and stress tests.

Sampling should include:

- valid and invalid citation IDs
- answerable and insufficient-evidence questions
- structurally valid but semantically weak citations
- overclaims
- conflicting-evidence cases
- refusals

## Annotation Setup

- Use double-blind annotation.
- Hide model/baseline identity from annotators.
- Show the claim, cited span text, question, and minimal necessary source context.
- Do not show automatic verifier labels during annotation.

## Labels

- `entailed`: cited span supports the claim.
- `partially_supported`: cited span supports part of the claim or a weaker version.
- `unsupported`: cited span does not support the claim.
- `contradictory`: cited span contradicts the claim.
- `insufficient_evidence`: available cited evidence is not enough to decide.

## Agreement

Report human-human agreement with Cohen's Kappa for two annotators or Krippendorff's Alpha for more than two annotators or missing labels.

Resolve disagreements through adjudication, but keep raw annotator labels for analysis.

## Automatic Judge Calibration

Measure human-LLM agreement for any automatic semantic verifier before using it as a paper metric.

Calibration should report:

- label-wise precision and recall
- confusion matrix
- agreement with adjudicated labels
- examples of verifier false positives and false negatives

## Use in Evaluation

Human labels should calibrate and sanity-check semantic support metrics. They do not replace deterministic citation pointer validation.

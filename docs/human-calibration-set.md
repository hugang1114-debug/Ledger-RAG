# Human Calibration Set

## Annotation Goal

Create a small human-labeled claim-citation dataset for calibrating semantic support evaluators. The current local heuristic verdict is included only as metadata; it is not a gold label and should not be shown as authoritative evidence.

The initial target is 200-500 claim-citation pairs sampled from diagnostic runs and stress tests.

## Export Format

The exporter writes JSONL and CSV rows with:

- `annotation_id`
- `dataset`
- `question_id`
- `baseline`
- `claim_id`
- `claim_text`
- `citation_id`
- `cited_span_text`
- `structural_validity`
- `current_semantic_verdict`
- `current_semantic_confidence`
- `human_label`
- `human_notes`

By default, only structurally valid citation pairs are exported. Use `--include-invalid` only for error-analysis annotation.

## Allowed Human Labels

- `entailed`: the cited span supports the full claim.
- `partially_supported`: the cited span supports part of the claim or a weaker version, but not the full wording.
- `unsupported`: the cited span does not support the claim.
- `contradictory`: the cited span directly conflicts with the claim.
- `insufficient_evidence`: the cited span does not provide enough evidence to decide.

## Annotation Examples

Entailed:

- Claim: "The Ida is used by Yoruba people."
- Span: "The Ida is a sword used by the Yoruba people of West Africa."
- Label: `entailed`

Partially supported:

- Claim: "The Ida is a ceremonial sword used by Yoruba people."
- Span: "The Ida is a sword used by the Yoruba people of West Africa."
- Label: `partially_supported`

Unsupported:

- Claim: "The Ida is used by Finnish sailors."
- Span: "The Ida is a sword used by the Yoruba people of West Africa."
- Label: `unsupported`

Contradictory:

- Claim: "The source says the Ida is not used by Yoruba people."
- Span: "The Ida is a sword used by the Yoruba people of West Africa."
- Label: `contradictory`

Insufficient evidence:

- Claim: "The Ida was first used in the 12th century."
- Span: "The Ida is a sword used by the Yoruba people of West Africa."
- Label: `insufficient_evidence`

## Export Command

```bash
python scripts/export_human_calibration_set.py --run artifacts/gate8/main_v1/runs/example/run_records.jsonl --jsonl-output artifacts/calibration/human_claim_citation_calibration.jsonl --csv-output artifacts/calibration/human_claim_citation_calibration.csv
```

Add `--include-invalid` to include structurally invalid citation pairs for error analysis.

## Human-Human Agreement

Use double-blind annotation. For two annotators, report Cohen's Kappa. For more than two annotators or missing labels, report Krippendorff's Alpha. Keep raw annotator labels and an adjudicated label column in later analysis.

## Evaluator Calibration

After annotation, compare local heuristic, NLI, and LLM judge outputs against human labels using:

- label-wise precision and recall
- macro F1
- confusion matrix
- agreement with adjudicated labels
- examples of false positives and false negatives

Do not treat the local heuristic verdict as paper-grade semantic evidence until it is calibrated against human labels.

## Judge Reliability Plan

DeepSeek v1 vs v2 comparisons are prompt stability diagnostics only. They show how sensitive the machine judge is to prompt wording; they do not validate judge reliability.

To evaluate judge reliability, sample 200-250 claim-citation pairs and collect human labels. Report:

- Human-DeepSeek accuracy
- macro-F1
- per-class precision and recall
- confusion matrix
- Cohen's kappa between human labels and DeepSeek labels

If two human annotators are available, also compute Human-Human Cohen's kappa. If only one human annotator is available, do not claim Human-Human agreement.

## DeepSeek Machine Judge Labels

DeepSeek-V4-Pro can be used to create machine judge labels for triage or judge calibration. These labels are not human gold labels and must not overwrite `human_label`.

DeepSeek-V4-Pro is an offline LLM-as-a-Judge evaluator in this workflow. It is not a baseline method unless a future experiment explicitly places it inside a system variant.

The script reads calibration candidate JSONL and writes a separate file with machine-judge fields:

- `deepseek_status`
- `judge_model`
- `judge_prompt_version`
- `deepseek_label`
- `deepseek_confidence`
- `deepseek_rationale`
- `deepseek_error`

Run a shape-only check without API calls:

```bash
python scripts/label_human_calibration_with_deepseek.py --dry-run
```

Run a small paid batch after setting `DEEPSEEK_API_KEY` in the environment or `.env.local`:

```bash
python scripts/label_human_calibration_with_deepseek.py --limit 20
```

Default outputs:

- `artifacts/calibration/deepseek_judge_labels_v2.jsonl`
- `artifacts/calibration/llm_judge_semantic_labels_v2.csv`

Compare `deepseek_label` against adjudicated human labels later. Do not use `deepseek_label` as paper-grade semantic support until agreement and error patterns have been measured.

The judge prompt version must be recorded in `judge_prompt_version`. Version `deepseek_semantic_judge_v2` uses stricter rules:

- use only the cited span
- do not use outside knowledge
- entity overlap is not support
- related evidence is not entailment
- use `contradictory` only when the span explicitly conflicts with the claim
- for negative claims or evidence-absence claims, prefer `insufficient_evidence` unless the span explicitly proves the opposite
- if numerical, temporal, causal, or performance claims are not explicitly supported, do not label `entailed`
- if only part of the claim is supported, label `partially_supported`

Compare prompt versions for prompt stability diagnostics:

```bash
python scripts/compare_deepseek_judge_versions.py
```

Export a high-risk manual audit subset:

```bash
python scripts/export_manual_audit_subset.py --target-size 50
```

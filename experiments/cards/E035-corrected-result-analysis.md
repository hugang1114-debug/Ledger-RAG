# E035 Corrected Result Analysis

## Status

Completed.

## Purpose

Analyze the corrected first main-result summary without additional model calls.

## Inputs

- `configs/gate8/main_v1_corrected_50x2x3_result_summary.yaml`
- Corrected run artifacts for HotpotQA, 2WikiMultihopQA, and MuSiQue

## Main Result

`ledger_validator` improves citation auditability compared with `vanilla_rag`:

- Claim citation coverage: 0.997041 vs 0.885630
- Invalid citation rate: 0.057692 vs 0.193548

The result does not show a broad answer-quality win. Refusal rates are similar overall, and MuSiQue remains the hardest dataset.

## Output

- `docs/gate8-corrected-result-analysis.md`
- `configs/gate8/main_v1_corrected_analysis_summary.yaml`

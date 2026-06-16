# Gate 8Q Smoke Result Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Review the Gate 8P DeepSeek smoke artifacts and promote only a safe tracked summary with hashes, cost, and pass/fail status.

**Architecture:** Add a stdlib-only result reviewer beside the DeepSeek smoke harness. The reviewer reads ignored artifact JSON files, validates shape and budget, scans for secret patterns, computes SHA256 hashes, and writes a YAML summary that excludes raw provider response text.

**Tech Stack:** Python standard library, pytest, existing ignored Gate 8P artifacts.

---

### Task 1: Failing Tests

**Files:**
- Create: `tests/test_gate8_smoke_result_review.py`

- [x] Write tests for file hashing, artifact review pass, missing artifact failure, over-budget failure, summary redaction, and CLI summary writing.
- [x] Run `python -m pytest tests/test_gate8_smoke_result_review.py -v` and verify failure because `ledger_rag_smoke.result_review` does not exist.

### Task 2: Reviewer And CLI

**Files:**
- Create: `src/ledger_rag_smoke/result_review.py`
- Create: `scripts/review_gate8p_smoke_result.py`

- [x] Implement reviewer helpers and CLI.
- [x] Run `python -m pytest tests/test_gate8_smoke_result_review.py -v` and verify tests pass.

### Task 3: Tracked Summary And Docs

**Files:**
- Create: `configs/gate8/deepseek_smoke_result_summary.yaml`
- Create: `experiments/cards/E022-gate8q-smoke-result-review.md`
- Modify: `README.md`

- [x] Run the reviewer on `artifacts/gate8/smoke/deepseek/latest`.
- [x] Write the tracked summary without raw response content.
- [x] Document that Gate 8Q reviews smoke evidence only and does not pass Gate 8.

### Task 4: Verification

- [x] Run `python -m pytest -v`.
- [x] Run placeholder scan.
- [x] Run secret scan on tracked files.
- [x] Confirm full Gate 8 strict readiness remains blocked.
- [x] Commit and push changes.

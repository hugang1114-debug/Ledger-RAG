# Gate 8P DeepSeek Smoke Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement and run a one-question DeepSeek-V4-Pro smoke call that writes contract-shaped artifacts without unlocking the main Gate 8 comparison.

**Architecture:** Add a focused `ledger_rag_smoke` package for env loading, request construction, provider calling, response parsing, and artifact shaping. Keep the CLI thin and keep tests offline through fake transport and dry-run mode.

**Tech Stack:** Python standard library, existing Gate 7 fixture and retrieval helpers, pytest.

---

### Task 1: Tests

**Files:**
- Create: `tests/test_gate8_deepseek_smoke.py`

- [x] Write failing tests for request shape, JSON extraction, cost estimate, run/metric contracts, fake-transport artifacts, env loading, and CLI dry-run.
- [x] Run `python -m pytest tests/test_gate8_deepseek_smoke.py -v` and verify failure because `ledger_rag_smoke` does not exist.

### Task 2: Smoke Module And CLI

**Files:**
- Create: `src/ledger_rag_smoke/deepseek_smoke.py`
- Create: `src/ledger_rag_smoke/__init__.py`
- Create: `scripts/run_gate8p_deepseek_smoke.py`

- [x] Implement stdlib-only helpers and CLI.
- [x] Run `python -m pytest tests/test_gate8_deepseek_smoke.py -v` and verify tests pass.

### Task 3: Documentation And Experiment Card

**Files:**
- Create: `docs/superpowers/specs/2026-05-17-gate8p-deepseek-smoke-run-design.md`
- Create: `docs/superpowers/plans/2026-05-17-gate8p-deepseek-smoke-run.md`
- Create: `experiments/cards/E021-gate8p-deepseek-smoke-run.md`
- Modify: `README.md`

- [x] Document that Gate 8P is a one-question smoke run and not a paper result.
- [x] Record commands and artifact paths.

### Task 4: Execute And Verify

**Files:**
- Ignored output: `artifacts/gate8/smoke/deepseek/latest/`

- [x] Run dry-run CLI.
- [x] Run one real DeepSeek smoke call.
- [x] Run full test suite.
- [x] Check that no secrets are tracked.
- [x] Commit and push changes.

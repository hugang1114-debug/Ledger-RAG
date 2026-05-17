# Gate 8P DeepSeek Smoke Run Design

## Purpose

Gate 8P performs one real DeepSeek-V4-Pro smoke call after Gate 8O authorization. It validates API key availability, OpenAI-compatible chat request shape, JSON answer shape, citation fields, cost estimation, and artifact writing.

This is not a main comparison, not a six-baseline run, and not a paper result.

## Scope

In scope:

- Use the tracked Gate 7 synthetic fixture for one question.
- Retrieve two local fixture evidence spans with deterministic lexical retrieval.
- Call DeepSeek once with `deepseek-v4-pro`.
- Request JSON output with `global_answer`, `atomic_claims`, and `citations`.
- Write inspectable artifacts under ignored `artifacts/gate8/smoke/deepseek/latest/`.
- Estimate cost from DeepSeek usage fields and checked Gate 8O prices.

Out of scope:

- Running main-v1 datasets.
- Running all six baseline families.
- Running semantic verifier or metric scoring for research claims.
- Storing API keys in tracked files.
- Treating smoke output as evidence for the paper claim.

## Architecture

`src/ledger_rag_smoke/deepseek_smoke.py` contains pure helpers for env loading, prompt/request construction, DeepSeek HTTP calls, response parsing, run record construction, metric record construction, and artifact writing.

`scripts/run_gate8p_deepseek_smoke.py` is the CLI entry point. It reads `DEEPSEEK_API_KEY` from the process environment or `.env.local`, supports `--dry-run`, and writes artifacts only under caller-provided output directories.

The tests use a fake transport and dry-run mode so test runs never call DeepSeek.

## Artifact Contract

The real smoke run writes:

- `request.json`
- `response.json`
- `run_record.json`
- `metric_record.json`
- `cost_estimate.json`

`request.json` excludes authentication headers. `response.json` is a raw provider response and must stay ignored under `artifacts/`.

## Safety Rules

- The CLI exits before network calls if no API key is available.
- The request artifact never contains the API key.
- The output directory remains ignored by git.
- The smoke run uses one question by default.
- Full Gate 8 strict readiness remains locked after the smoke run.

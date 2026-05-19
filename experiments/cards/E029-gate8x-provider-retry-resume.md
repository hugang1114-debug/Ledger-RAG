# E029 Gate 8X Provider Retry Resume

## Status

Implemented runner support. This card does not authorize a new main experiment.

## Purpose

Make HotpotQA mini runs resilient to transient provider disconnects by adding bounded per-call retries and resume-from-existing-artifacts support.

## Scope

- Runner: `scripts/run_gate8t_hotpotqa_mini_run.py`
- Module: `src/ledger_rag_main/hotpotqa_mini_run.py`
- Dataset: HotpotQA mini-run path only
- Provider: `deepseek / deepseek-v4-pro`

## New Controls

- `--max-provider-attempts`: maximum attempts for each provider call
- `--resume-from`: artifact directory whose successful `run_records.jsonl` entries should be reused

## Non-Goals

- No new DeepSeek calls were required for this implementation.
- No full main experiment is authorized by this card.
- No raw provider output or secrets are tracked.

## Verification

Relevant tests cover retry after transient provider failures, resume skipping of existing successful run records, and combined token/cost accounting for resumed runs.

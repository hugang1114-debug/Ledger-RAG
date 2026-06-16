# E032 Gate 8 Run Progress Visibility

## Status

Implemented.

## Purpose

Make long Gate 8 runs observable while they are running, without changing model prompts or experiment semantics.

## Behavior

- Prints one progress line after each baseline request is skipped, succeeds, or fails.
- Writes `progress.json` under each ignored dataset artifact directory.
- Records dataset id, split, question index, question count, baseline, success count, failure count, skipped count, estimated cost, and status.

## Example

```text
[musique] 48/50 q | baseline=ledger_validator | ok=96 fail=0 skipped=0 | cost=$0.089000 | status=running
```

## Non-Goals

- No DeepSeek calls are required by this change.
- No raw model output or secrets are tracked.
- No experiment results are changed.

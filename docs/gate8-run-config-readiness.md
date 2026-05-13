# Gate 8 Run Config Readiness

Gate 8F locks the non-executable shape of the `main_v1` comparison. It does not authorize model calls, retrieval evaluation, baseline execution, metric computation, or paper-result claims.

## Locked Scope

The first main comparison remains limited to:

- HotpotQA dev distractor
- 2WikiMultihopQA dev
- MuSiQue answerable dev

The comparison matrix must include all six Gate 5 baseline families:

- `vanilla_rag`
- `hybrid_rag`
- `citation_only`
- `validator_only`
- `ledger_only`
- `ledger_validator`

Every future executable run must reference:

- the source snapshot id from `snapshots/main_v1/source_snapshots.json`
- the retrieval index manifest path from `snapshots/main_v1/source_snapshots.json`
- the baseline family from `docs/baseline-contract.yaml`
- the metric groups from `docs/metric-contract.yaml`
- a frozen prompt/config version
- a selected provider/model record
- an ignored artifact destination under `artifacts/gate8/main_v1/`

## Non-Executable Matrix

`configs/gate8/main_v1_run_matrix.yaml` is a readiness matrix, not a command source. Its `authorized_to_run` field must remain `false` until a later execution gate locks provider, prompt, budget, and reproducibility review.

The matrix may list a `hybrid_rag` baseline, but hybrid execution remains blocked until a separate dense or hybrid retrieval implementation is locked. The current Gate 8E lexical index is enough for lexical retrieval readiness only.

## Run Lockout

Gate 8F does not clear the final Gate 8 status blocker. Source snapshot registry records remain `source_ready`, not `ready`.

Future execution is blocked while any of these remain true:

- provider is unselected
- official pricing and model documentation have not been checked on the run date
- prompt versions are not frozen
- cost budget is not approved
- execution card does not name exact commands and output paths
- reproducibility review has not confirmed paths, seeds, configs, and artifact destinations

## Artifact Convention

Future run outputs must stay ignored under:

```text
artifacts/gate8/main_v1/
```

Expected subdirectories:

- `runs/`
- `metrics/`
- `logs/`
- `reports/`

Gate 8F creates none of these result files.

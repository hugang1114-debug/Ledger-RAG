# E011 Gate 8 Run Config Readiness

## Purpose

Create non-executable Gate 8F run matrix and provider-readiness metadata. This card authorizes metadata creation only.

## Authorized Scope

- document main v1 run matrix rules
- document provider selection evidence requirements
- create `configs/gate8/main_v1_run_matrix.yaml`
- create `configs/gate8/provider_decision.yaml`
- keep provider unselected
- keep run authorization disabled

## Prohibited Actions

- model calls
- embedding calls
- reranker calls
- retrieval evaluation
- baseline execution
- metric computation
- result artifact creation
- provider selection
- price claims without official run-date verification
- source snapshot status promotion to `ready`

## Expected Outputs

- `docs/gate8-run-config-readiness.md`
- `docs/model-provider-readiness.md`
- `configs/gate8/main_v1_run_matrix.yaml`
- `configs/gate8/provider_decision.yaml`
- README and readiness doc references

## Success Criteria

- run matrix lists HotpotQA, 2WikiMultihopQA, and MuSiQue
- run matrix lists all six Gate 5 baseline families
- provider decision keeps `selected: false`
- provider decision keeps `run_authorized: false`
- Gate 8 readiness still reports `gate8_ready: false`

## Cost Class

Documentation and metadata only. No model/API/provider cost is authorized.

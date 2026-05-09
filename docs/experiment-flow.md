# Experiment Flow

Ledger-RAG experiments advance by evidence gates, not calendar milestones.

## Gate 1: Project Base Ready

Required artifacts:

- `AGENTS.md`
- `README.md`
- `docs/project-boundary.md`
- `docs/experiment-flow.md`
- `literature/manifest.yaml`
- `experiments/README.md`

Exit condition: a future contributor can understand the project boundary and rules without reading the original feasibility report.

## Gate 2: Literature Verified

Required artifacts:

- core paper PDFs downloaded from official sources when available
- manifest entries for papers that are landing-page only
- notes for any source that differs from the feasibility report

Exit condition: every paper used in the paper narrative has a verified official source.

## Gate 3: Research Claim Locked

Required artifacts:

- one paragraph main claim
- one paragraph negative scope
- one table mapping claim components to experiments

Exit condition: the paper claim is narrow enough to test and falsify.

## Gate 4: Dataset Feasibility Locked

Required artifacts:

- dataset license notes
- download method
- expected storage
- evaluation script availability
- known reproduction risks

Exit condition: the main dataset list is realistic, legal to use, and runnable.

## Gate 5: Baseline Protocol Locked

Required baseline families:

- Vanilla RAG
- Hybrid RAG
- Citation-only
- Validator-only
- Ledger-only
- Ledger + Validator

Exit condition: each baseline has the same input/output contract and an experiment card.

## Gate 6: Metric Protocol Locked

Metric groups:

- retrieval: Recall@k, Precision@k, MRR, nDCG
- answer quality: EM/F1, ROUGE-L where appropriate, claim-level correctness, FActScore where feasible
- attribution: citation precision/recall, support rate, unsupported-claim rate, overclaim rate
- system: p50/p95 latency, cost/query, peak memory, index size, ledger size

Exit condition: metrics are defined before running comparisons.

## Gate 7: Pilot Experiment Passed

Run only a small sample first.

Exit condition: ingestion, retrieval, generation, verification, and evaluation all produce inspectable artifacts.

## Gate 8: Main Comparison Passed

Exit condition: all main baselines and the full Ledger-RAG variant are run using locked configs and source snapshots.

## Gate 9: Ablation / Stress Passed

Required stress areas:

- retrieval oracle vs real retrieval
- ledger-only vs verifier-only vs full system
- evidence position
- noise and conflict evidence
- parser/hash stability

Exit condition: improvements can be attributed to specific system components.

## Gate 10: Paper Package Ready

Required artifacts:

- tables
- figures
- error analysis
- reproducibility checklist
- limitations section
- appendix material for schema, prompts, configs, and licenses

Exit condition: the paper package can be reviewed independently of local run history.


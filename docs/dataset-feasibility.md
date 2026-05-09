# Dataset Feasibility

Gate 4 locks dataset feasibility only. It does not approve dataset downloads, model runs, or experiment cards.

## Decision Summary

Use a staged dataset portfolio:

- Main v1 multi-hop datasets: HotpotQA, 2WikiMultihopQA, MuSiQue.
- Attribution pilot datasets: HAGRID, ExpertQA.
- Long-context citation datasets deferred until tooling checks: LongBench, LongBench-Cite, L-CiteEval, SUnsET.
- License or reproduction deferred: ASQA, QAMPARI.
- Excluded from v1: Common Crawl, dynamic web browsing, high-risk medical/legal/financial datasets.

This keeps the first experiments static, replayable, and close to Ledger-RAG's core claim: traceability, auditability, long-task stability, and engineering cost.

## Main v1 Datasets

| Dataset | Why included | Source and license notes | Download and evaluation notes | Reproduction risks |
|---|---|---|---|---|
| HotpotQA | Multi-hop QA with supporting facts, directly useful for retrieval isolation and traceability. | Official homepage states CC BY-SA 4.0 and provides train/dev/test downloads plus processed Wikipedia under the same license: https://hotpotqa.github.io/ | Download from official homepage. Official evaluation script is linked from the homepage. Use distractor/dev first; fullwiki corpus is optional and larger. | CC BY-SA propagation must be noted. Fullwiki setting requires corpus handling and may mix retrieval quality with ledger effects. |
| 2WikiMultihopQA | Multi-hop QA with reasoning/evidence structure and an official evaluation script. | Official repository is Apache-2.0: https://github.com/Alab-NII/2wikimultihop | Use repository data and `2wikimultihop_evaluation_v1.1.py` after confirming local paths. | GitHub repo page is the source of truth; download path and split names must be rechecked before any run. |
| MuSiQue | Multi-hop QA with answer and support metrics; useful because it warns about leakage from seed datasets. | Official repository states CC BY 4.0: https://github.com/StonyBrookNLP/musique | Use `bash download_data.sh` or manual Google Drive download. Evaluation uses `evaluate_v1.0.py`. | Must record leakage caution for SQuAD, T-REx, Natural Questions, MLQA, and Zero Shot RE seed data. Tooling includes older dependency assumptions. |

## Attribution Pilot Datasets

| Dataset | Why included | Source and license notes | Download and evaluation notes | Reproduction risks |
|---|---|---|---|---|
| HAGRID | Small attribution-oriented dataset with human judgments for informativeness and attributability. | Official repository is Apache-2.0: https://github.com/project-miracl/hagrid | Load through Hugging Face dataset `miracl/hagrid`. Use as an attribution pilot, not a main answer-quality benchmark. | Repository says baselines are coming soon, so metric protocol must be defined locally. |
| ExpertQA | Expert-curated questions and claim-evidence attribution judgments, useful for auditability and verifier analysis. | Official repository is MIT licensed: https://github.com/chaitanyamalaviya/ExpertQA | Data and evaluation scripts are in the repository; autoAIS, QAFactEval, FActScore-style paths exist. | Some evidence entries can be URL-only. Fetching URL evidence can break replayability unless snapshots are created. |

## Deferred Long-Context Datasets

| Dataset | Reason to defer | Tooling notes |
|---|---|---|
| LongBench | Strong long-context reference, but not citation-specific by default. | Official repo loads data from Hugging Face and includes evaluation scripts: https://github.com/THUDM/LongBench |
| LongBench-Cite | Closest long-context citation benchmark in the LongCite ecosystem. | Official LongCite repo provides data/code under `LongBench-Cite/`, but evaluation uses GPT-4o as judge, so cost/model dependency must be approved first: https://github.com/THUDM/LongCite |
| L-CiteEval | Long-context citation benchmark spanning multiple task families. | Official repo uses Hugging Face dataset `Jonaszky123/L-CiteEval` and scripts for citation/correctness evaluation: https://github.com/LCM-Lab/L-CITEEVAL |
| SUnsET | Highly relevant to unstructured evidence attribution and lost-in-the-middle behavior. | Official repo releases data through Hugging Face dataset `dwright37/SUnsET` and includes training/inference/evaluation scripts: https://github.com/dwright37/unstructured-evidence-sunset |

These are research-relevant but not first-batch main datasets. They should become Gate 7+ candidates only after toolchain, cost, judge-model, and storage checks are written in experiment cards.

## License or Reproduction Deferred

| Dataset | Reason to defer |
|---|---|
| ASQA | Official Google Research repo provides dataset download and evaluation code, and TensorFlow Datasets reports small download size, but the data includes ambiguous QA/Wikipedia-derived content and does not directly test claim-to-span ledger replay. Use later if long-form QA coverage is needed. Source: https://github.com/google-research/language/tree/master/language/asqa |
| QAMPARI | Official repository is CC0-1.0 and has many-answer QA, but it is not primarily an attribution dataset and needs a separate decision on how many-answer precision/recall maps to Ledger-RAG claim support. Source: https://github.com/samsam3232/qampari |

## Excluded from v1

- Common Crawl: too broad for first-version reproducibility, licensing, and replay guarantees.
- Dynamic web browsing: live pages break stable source hashes and repeatable span replay.
- Medical, legal, financial datasets: high-risk domains need source-trust and compliance policy beyond this project phase.

## Gate 4 Exit Rule

Gate 4 is satisfied when the dataset matrix is committed and later experiment cards can reference a dataset decision without re-deciding scope. Gate 4 does not authorize downloads.


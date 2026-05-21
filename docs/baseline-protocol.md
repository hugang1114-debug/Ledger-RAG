# Baseline Protocol

This protocol defines attribution baselines. It does not authorize new provider calls or large-scale execution.

## Shared Rules

All baseline families must use the same dataset split, question list, source snapshot, retrieval budget, answer format, and reporting schema. Oracle evidence may be used only in explicitly labeled diagnostics.

Refusals must be recorded. A method cannot improve attribution metrics by silently omitting hard claims or refusing without evidence-insufficiency justification.

Do not call the current `hybrid_rag` prompt-policy slot a real dense hybrid baseline unless dense retrieval or reranking is implemented and recorded.

## System Components vs Evaluation Judges

Baseline methods are systems under test. They may include answer generation, citation prompting, ledger pointer emission, deterministic validation, or an internal semantic verifier module.

Evaluation judges are scoring tools used offline after system outputs are produced. An LLM-as-a-Judge, including DeepSeek-V4-Pro when used for evaluation, is not a baseline method and must not be listed as a system variant unless it is explicitly part of the system being tested.

- Semantic Verifier: a module inside a system variant that checks or filters generated claims before final system output.
- LLM-as-a-Judge: an offline evaluator used to score all variants after generation.
- These roles must not be conflated.

## Baseline Families

### Vanilla RAG

Answer generation over retrieved evidence without required citations, ledger pointers, deterministic validation, or semantic verifier feedback.

### Citation-only Prompting

The model receives retrieved evidence IDs and is prompted to cite them. Citation IDs are model output and must be audited after generation.

### Semantic Verifier Only, No Ledger

Generated claims and citations are checked by a semantic verifier module without ledger pointers or deterministic pointer validation. This baseline tests whether semantic verification alone can handle fake citation IDs, source version drift, span hash mismatch, snapshot replay, and not-in-retrieved-evidence citations. It is expected to detect semantic mismatch but not guarantee citation ID validity or replayability.

### Ledger Pointer Only

Retrieved evidence is represented as citation pointers with source snapshot and span hash fields. No deterministic rejection or semantic support verdict is applied after generation.

### Ledger + Deterministic Validator

Citation pointers are checked for source existence, snapshot hash, span existence, span hash, and retrieved-evidence membership. Semantic support is not judged in this baseline.

### Ledger + Deterministic Validator + Semantic Verifier

The full system variant. It performs deterministic pointer validation first, then uses an internal semantic verifier module to check claim-to-span support separately. Offline LLM-as-a-Judge scoring may still be used to evaluate this variant, but the judge is not part of the method name.

### Future Work: Ledger-Trained Model With SFT/DPO

A later-stage model trained to prefer valid and conservative citation behavior. This is future work unless implemented and evaluated. It cannot replace deterministic validation.

## Comparison Invariants

Every main run must record:

- dataset ID, split, question ID, and question text
- source snapshot ID/hash
- retrieval config and retrieved evidence IDs
- ledger pointer strings where applicable
- deterministic validation status per citation
- internal semantic verifier status per claim-citation pair where applicable
- offline evaluation judge metadata where semantic metrics are computed by an LLM-as-a-Judge
- refusal label and refusal rationale
- latency, cost, seed, code version, prompt version, and config version

## Non-Comparable Conditions

- different question list or source snapshot
- different evidence budget
- hidden gold evidence in main runs
- missing deterministic validation for citation-capable baselines
- reporting lexical support rate as a core attribution metric
- calling a lexical prompt-policy baseline dense hybrid retrieval
- listing an offline judge such as DeepSeek-V4-Pro as a baseline method

# Future SFT/DPO Design

This document is a future-work plan only. Do not implement SFT or DPO until the deterministic protocol works and the semantic evaluator has been calibrated against human labels.

The current paper is model-agnostic: "We do not introduce new model weights. We propose a model-agnostic attribution audit protocol based on replayable evidence pointers, deterministic validation, and calibrated semantic evaluation."

## Preconditions

Training may start only after:

- deterministic citation validation works
- semantic support evaluation works
- ledger-specific stress tests exist
- a small human-labeled evaluation set is planned
- diagnostic baseline results show which citation behaviors training might target
- human calibration shows that semantic evaluation is reliable enough to measure training effects

## Preference-Pair Categories

| Category | Rejected behavior | Preferred behavior |
|---|---|---|
| Invalid citation trap | Answer cites nonexistent, malformed, or not-retrieved citation IDs. | Answer cites only valid retrieved ledger pointers or refuses. |
| Semantically wrong citation trap | Answer cites a structurally valid span that does not support the claim. | Answer cites an entailing span or weakens the claim. |
| Overclaim trap | Answer makes a stronger claim than cited evidence supports. | Answer states a conservative claim matching the cited span. |
| Missing citation trap | Answer makes factual claims without citations. | Every evidence-requiring claim has at least one valid pointer. |
| Evidence-insufficient refusal trap | Answer fabricates support when retrieved evidence is insufficient. | Answer refuses with an evidence-insufficient label. |
| Correct citation with conservative answer | Answer cites valid evidence but adds unsupported details. | Answer cites valid evidence and avoids unsupported details. |

## Non-Guarantee

SFT or DPO can improve model behavior but cannot guarantee citation correctness. Deterministic validation must remain the enforcement layer for citation ID validity, and semantic checking must remain a separate evaluation layer.

SFT/DPO must remain future work unless new model weights are actually trained, evaluated, and compared against the model-agnostic protocol. Do not present SFT/DPO as part of the current contribution.

## Evaluation Before Training

Before training, create a small held-out set with human labels for:

- entailed
- partially supported
- unsupported
- contradictory
- insufficient evidence

Training success should be measured against deterministic validation status and human-calibrated semantic support, not lexical overlap.

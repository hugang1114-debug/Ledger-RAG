# Model Provider Readiness

Gate 8F defines provider-selection evidence requirements without selecting a provider. Provider availability, model versions, and prices are temporally unstable, so no provider or price may be treated as locked until checked against official sources at execution time.

## Current Decision

Provider selection is not complete:

- `selected: false`
- `provider: unset`
- `model: unset`
- `run_authorized: false`

This is intentional. A later provider and prompt freeze gate must make the selection explicitly.

Gate 8I adds `configs/gate8/provider_evidence_registry.yaml` as the tracked place for official provider evidence. Provider selection remains unset, and the registry starts incomplete and non-executable until a future execution gate reviews official sources and authorizes model calls.

## Gate 8K Candidate

Gate 8K records OpenAI `gpt-5.4-mini` as the first provider/model candidate. This is a candidate lock, not a final execution decision.

The candidate evidence records official OpenAI URLs for pricing, model documentation, terms, context window, output limit, and throughput planning. API key availability and cost budget approval remain unresolved.

`provider_decision.yaml` therefore keeps `selected: false` and `run_authorized: false`. Prices, model availability, limits, and terms must be rechecked on the actual run date before execution can be authorized.

## Required Future Evidence

Before any main baseline can run, the provider decision record must include:

- official pricing URL checked on the run date
- official model documentation URL checked on the run date
- provider name
- model id and version or release date
- context window
- maximum output limit
- deterministic generation settings
- rate-limit or throughput note
- data retention or privacy note
- API key or local runtime availability note
- approved cost budget note

## Disallowed Evidence

The project must reject:

- stale prices copied from reports or old notes
- undocumented model aliases
- provider claims without official URLs
- hidden API keys in tracked files
- prompt versions described only in prose
- runs that cannot reproduce model id, config, prompt version, and cost assumptions

## Prompt And Config Freeze

Prompt and config readiness requires:

- a stable prompt version id for each baseline family
- a generation config version id
- deterministic settings where supported
- answer style shared across comparable baselines
- max evidence budget shared across comparable baselines
- refusal behavior consistent with `docs/baseline-protocol.md`

Gate 8F documents these requirements but does not write final prompt text.

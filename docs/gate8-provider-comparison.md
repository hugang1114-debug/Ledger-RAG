# Gate 8 Provider Comparison

Gate 8M compares provider candidates for later smoke and main runs. It does not select a final provider, authorize API calls, or pass Gate 8.

## Candidates

| Candidate | Role | Cost profile | Main risk |
| --- | --- | --- | --- |
| OpenAI GPT-5.4 | small-sample credibility comparison | higher cost | full-run cost can grow quickly |
| DeepSeek-V4-Pro | cost-controlled smoke and possible main run | lower current listed cost | discounted pricing and output behavior must be checked before execution |

## Official Source Records

The tracked source-of-record fields live in `configs/gate8/provider_candidates.yaml`.

- OpenAI GPT-5.4: official model and pricing source recorded as `https://openai.com/index/introducing-gpt-5-4/`.
- DeepSeek-V4-Pro: official model and pricing source recorded as `https://api-docs.deepseek.com/quick_start/pricing`.

Prices, model limits, terms, and API/runtime availability must be rechecked on the actual run date.

## Budget Interpretation

The budget includes generator tokens, verifier tokens, repeated calls across six baseline families, retry calls, JSON repair calls, and provider tool costs if a later gate enables tools.

The budget excludes local lexical retrieval index construction, local source snapshots, local result storage, literature PDFs, project docs, and ignored local caches.

## Current Recommendation

Use DeepSeek-V4-Pro as the first smoke-run candidate because it is cheaper and can test JSON, citation, and verifier behavior at low cost. Use GPT-5.4 later as a small-sample credibility comparison if the DeepSeek smoke run is stable.

## Execution Boundary

Provider choice affects external validity and must be reported with all results. No provider is authorized for execution by this document.


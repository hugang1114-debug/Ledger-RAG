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

## Gate 8N Primary Selection

DeepSeek-V4-Pro is selected as the primary provider for the first smoke run and likely main-v1 run. GPT-5.4 remains an optional small-sample credibility check, not a required provider for the first comparable run.

All six baseline families must use DeepSeek-V4-Pro for the first comparable run unless a later gate explicitly changes the provider decision. Results should be reported as DeepSeek-conditioned until cross-provider checks are completed.

## Gate 8O Smoke Authorization

Gate 8O authorizes only a DeepSeek-V4-Pro smoke run under the existing 10 USD ceiling. This authorization does not permit the full main comparison, GPT-5.4 calls, or cross-provider runs.

The smoke run must still recheck official DeepSeek pricing on the actual run date, read `DEEPSEEK_API_KEY` only from local environment or `.env.local`, and produce inspectable contract-shaped artifacts before any result can support the paper.

## Gate 8R Evidence Lock

Gate 8R locks DeepSeek-V4-Pro provider evidence using official DeepSeek source URLs and the reviewed Gate 8Q smoke summary. This makes DeepSeek the evidence-backed primary provider for the next readiness steps.

The lock is not execution authorization. Main runs still require prompt/config freeze, run-date pricing recheck, main budget approval, and an execution card.

## Execution Boundary

Provider choice affects external validity and must be reported with all results. This document records DeepSeek provider selection, smoke authorization, and provider evidence lock, not full Gate 8 execution authorization.

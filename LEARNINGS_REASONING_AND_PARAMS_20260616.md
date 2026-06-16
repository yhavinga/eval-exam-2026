# LEARNINGS — Reasoning & generation-parameter control per model/stack

**Date:** 2026-06-16 · **Related commit:** `6018bd5` (presence_penalty optional/nullable)

## Golden rule
**Per-ENDPOINT `supported_parameters` is authoritative — not the model-level list**, which can show a misleading `[]` even when the endpoint honors the param. Always query the specific provider endpoint
(`/api/v1/models/<slug>/endpoints`).

## Reasoning control by model
- **opus-4.8 (anthropic)** — reasoning supported and graded. `effort=medium` → thinking on. OpenRouter **normalizes** the `top_p`/`top_k` that Anthropic extended-thinking would otherwise reject (probe: medium worked with top_p=0.95 / top_k=20, no error).
- **qwen3.6-27b (wandb/fp8)** — endpoint `supported_parameters = []` → `reasoning`, `presence_penalty`, `top_k` all **silently dropped** by OpenRouter. The model **reasons by default** (~3k-char traces) regardless of `--reasoning-effort`. ⇒ effort/pp are **cosmetic** for qwen (logged, no effect).
- **gemma-4-31b-it** — reasoning **is** controllable:
  - **genai stack** — binary: `thinking_level="minimal"` when off, else default-on. **high ≡ medium** (both map to default-on, scored identically 96.1% gemma-judged); off = minimal.
  - **OpenRouter (wandb-bf16, siliconflow-fp8)** — endpoint `supported_parameters` **includes** `reasoning`. Probe (wandb): `effort=medium` → ~2566 reasoning chars (ON); `effort=none` → **0** (OFF); `enabled=false` → off; **no reasoning param → off by default**. Both providers produced traces on 100% of medium-run answers (5–6k chars).

## eval.py mapping (solve AND judge — both correct)
`{off:"none", low, medium, high, xhigh}.get(effort, "high")` → `extra_body["reasoning"] = {"effort": ...}`
- `--reasoning-effort off` → `"none"` → **genuinely off** (confirmed on gemma wandb).
- Default `--reasoning-effort on` → `"high"` ("on" isn't a key → falls through). **Unspecified = high, not neutral.**
- Reasoning trace captured via `msg.reasoning` / `reasoning_content` and stored.
- Correct for gemma; for models that don't expose reasoning (qwen) the param is sent but dropped → **logged effort is cosmetic** there.
- ⚠️ For gemma, `medium` vs `high` on OpenRouter is probably the same (binary, like genai) — treat as possibly-equivalent.

## presence_penalty
- **Anthropic's API has no `presence_penalty`** → opus `supported_parameters` lacks it → OpenRouter **drops** it. Value (0 / 1.5 / 2) or unset = identical output for opus. The **genai** backend also ignores it (not in `GenerateContentConfig`).
- **Change (`6018bd5`)**: `--presence-penalty` is now **optional** (default unset, only sent when passed); `runs.presence_penalty` made **nullable** (schema + table-rebuild migration; all 31 runs / 775 answers / 2025 judgements preserved; backup `eval.db.bak-pre-nullable-pp`); run-dedup uses NULL-safe `IS`. Records "absent" honestly instead of a fabricated 1.5.

## Output-token caps (check before solving!)
`max_completion_tokens` (the OUTPUT limit) is **separate from the context window** — **gpt-4o = 16384** (the 65536 default would error), opus-4.8 = 128000. ⚠️ For gemma-4-31b-it / qwen3.6-27b, **262144 (256K) is the *input context*, not the output cap**: the real output limit swings by provider — as low as **8192 (gemma/Venice) or 16384 (gemma/DeepInfra)**, while wandb/siliconflow merely report it equal to context. Always check the specific endpoint (our runs used 32768, safely within the providers we ran).

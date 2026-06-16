# LEARNINGS — OpenRouter image-context integrity

**Date:** 2026-06-16 · **Status:** Issue A not reproducing since 2026-06-14; Issue B fixed (commit `65f1f4a`)

## TL;DR
Two independent ways images failed to reach the solving model:
- **(A) Provider-side** — OpenRouter silently dropped images past a cumulative ~8-per-request cap (transient, ~June 9–10; gone now).
- **(B) Code-side** — our resume path replaced already-answered questions with text-only stubs (no images) — now fixed.

The benchmark deliberately carries every prior question's images forward within a topic, so it is uniquely exposed to both.

## Issue A — OpenRouter cumulative image cap (provider-side)
**Symptom.** Total images per request capped at ~8, counting **all** images across the accumulating conversation (not just the current message). Beyond 8:
- **Loud** (Mistral): HTTP 400 `Total number of images exceeds the maximum allowed of 8` (code 3051).
- **Silent** (gemma-4-31b-it, gpt-4o, gpt-4o-mini): images #9+ dropped, no error; the model then says "no image for question X" or hallucinates.

**Why it bit us.** Cumulative image count crosses 8 at the long-topic tail: **Q07=9, Q15=10, Q24=9, Q25=12**.

**Blast radius (eval ~2026-06-09/10).** Every tested OpenRouter provider for gemma-4-31b-it hit it on Q07/Q24/Q25 — default routing (14/14 runs), siliconflow-fp8 (7/7), novita-bf16, parasail-fp8, chutes-fp4 (1/1 each). **Quant-independent** (bf16/fp8/fp4 all affected) ⇒ it's an OpenRouter/transport condition, not a provider or quantization issue.

**Immune.** Local LMStudio and the **genai** direct Google API (neither routes through OpenRouter).

**Current status — NOT reproducing since 2026-06-14.** Fresh runs (gemma wandb/siliconflow, opus, gpt-4o, gemini) delivered every image, **0 missing-image complaints** even on Q25 (12 images).

**External corroboration.**
- GitHub `openclaw#19099` — cumulative images in chat history → 400 "max 8" (Mistral); root cause is the agent re-sending all prior images each turn.
- GitHub `openclaw#45867` — OpenRouter snapshot-fallback **silently drops images, no error/warning**.
- GitHub `kilocode#720` — analogous "27 > 20" cap.
- OpenRouter docs: image limits "vary per provider and per model" — no published number.

**Detection signature.** Scan stored answers for `geen afbeelding`, `details van vraag X`, `no image`, etc. on the high-image questions. ⚠️ Catches **loud** complaints only — silent hallucinations leave no text trace.

## Issue B — resume path dropped image context (code-side, FIXED `65f1f4a`)
**Bug.** `cmd_solve`'s resume branch re-inserted already-answered questions as text-only stubs (`[Vraag N was al beantwoord]`) — no images, not even the prompt. A *resumed* run therefore gave later questions less visual context than a *fresh* run → results depended on whether the process was interrupted (non-reproducible).

**Fix.** Reconstruct the full user turn (images + `Vraag {n}: {prompt}`) identical to a fresh solve, then the stored answer as the assistant/model turn — for both the genai and openai paths.

**Validated.**
- Before/after on the real `cmd_solve`: resumed Q07 request went **1 image → 9 images**, byte-identical to a fresh run.
- Confirmed in production: when a genai batch lost wifi mid-run, re-firing the same commands cleanly resumed — completed runs skipped, partial runs (5: 2/25, 8: 4/25) picked up mid-topic with full image context, no duplicates or rework.

## Mitigation going forward
1. **Never prune images** — carrying them forward is the benchmark's independent variable.
2. **Pick providers that deliver all images**; verify post-hoc by scanning answers for missing-image complaints.
3. **The judge now flags it** (`[MISSING_IMAGE=ja]` → `IMPORTANT Qx..Qz reported to have missing images`) — see `LEARNINGS_JUDGES`.
4. **Re-run any data captured during a cap window** — the silent case is undetectable, so re-solving is the only safe remedy. (We did this: dropped the corrupted siliconflow runs and re-solved.)
5. **Mistral genuinely cannot exceed 8 images** → document as a model limitation, don't fight it.

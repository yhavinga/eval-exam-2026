# 20260617 — gold re-judge (gpt-5.4) of in-scope routes

**Goal:** Put gemma-4-31b and qwen-3.6-dense routes onto a single trustworthy
scale by re-judging existing answers with the gold judge (`openai/gpt-5.4`,
reasoning medium), so cross-provider/quant comparisons aren't confounded by
which judge happened to score each route.

**Why:** before this, `gpt-5.4` had only scored the genai gemma temperature sweep.
Every OpenRouter route + the lone qwen run was scored only by weaker/lenient
judges (gemini-3.5-flash low, gemma self-judge, grok), so their %s were not
comparable. The *answers* already existed — only re-judging was needed.

## What was judged

`judge-count=1`, gaps only (no second pass, nothing already gpt-5.4-judged touched).
All routes below had **zero** prior gpt-5.4 coverage; each answer got exactly one gold judgement.

| route | stack | n runs | answers |
|-------|-------|--------|---------|
| `google/gemma-4-31b-it:wandb-bf16` (medium) | openrouter | 7 | 175 |
| `google/gemma-4-31b-it:siliconflow-fp8` (medium) | openrouter | 7 | 175 |
| `qwen/qwen3.6-27b:wandb-fp8` (medium) | openrouter | 1 | 25 |
| `gemma-4-31b-it` (high / off) genai | genai | 1+1 | 50 |
| `:novita-bf16` / `:parasail-fp8` / `:chutes-fp4` (medium) | openrouter | 1 each | 75 |

The genai gemma `medium` runs were already gold-judged (the temperature sweep) and
were **not** re-touched.

## Data-quality caveat (important)

Three singleton routes raised **"missing images"** during judging — the original
*solves* never received the image for some questions, so those answers were generated
blind and their scores are artifacts, **excluded** from all conclusions:

- `:parasail-fp8` — Q07, Q24, Q25
- `:chutes-fp4` — Q07, Q25
- `:novita-bf16` — Q07

They need **re-solving** before they mean anything. wandb-bf16, siliconflow-fp8,
qwen and genai were all **clean**.

## Results (gold scale = openai/gpt-5.4, reasoning medium)

All rows below are **temp 1.0, reasoning=medium, top_p 0.95, top_k 20** (max_tokens
32768 genai / 32000 openrouter — negligible). Caveat: "medium" is *binary thinking-on*
on genai but a graded effort on OpenRouter — same label, possibly different mechanism.

### Accuracy + generation speed, gemma-4-31b

| route | gold mean% | n | s/question (avg) | s/question (median) |
|-------|-----------|---|------------------|---------------------|
| genai (Google) | ~90.8 | 4 | 87.6 | 66.4 |
| `:wandb-bf16` | 89.8 | 7 | **36.5** | **29.3** |
| `:siliconflow-fp8` | 86.1 | 7 | 63.7 | 46.4 |

- **wandb-bf16 ≈ genai on accuracy (89.8 vs 90.8, within noise) and ~2.4× faster.**
- **siliconflow-fp8 ~3.7 pt lower** than wandb-bf16 (provider+quant confounded) and slower.
- Speed caveat: latencies were measured on different days and genai ran on the **free tier**
  (rate-limited), so treat the speed gap as indicative, not a controlled benchmark.

### qwen-3.6-27b dense — first gold point

`qwen3.6-27b:wandb-fp8`, medium, t1.0, **89.5%** (n=1, fp8, pp=1.5). Right in gemma's
band; a real gold baseline now exists (still n=1 — the effort ladder is how to flesh it out).

### gemma reasoning on genai (t1.0)

off=89.5 (n=1), medium=90.8 (n=4), high=93.4 (n=1) — flat within noise. Note medium
and high are the **same** config on genai (binary thinking), so that 2.6 pt is pure
run noise. Thinking barely moves this near-ceiling exam.

## Provenance

- Per-route judge logs: [`logs/`](logs/) (`judge_<n>_<slug>_<effort>.log`).
- DB backup before judging: `natuurkunde/eval.db.bak-pre-20260617-gold-rejudge`.
- ~500 new `openai/gpt-5.4` judgements added to `eval.db`.
- Excluded from gold judging: the unpinned `google/gemma-4-31b-it` route (OpenRouter
  load-balances it across providers per request → a provider mixture, footnote-only).

# VWO physics eval — findings so far (as of 2026-06-17)

Scope of interest: two **dense** models — `gemma-4-31b-it` and `qwen-3.6-27b` —
served via Google **genai**, OpenRouter providers (notably **wandb**), and
eventually a local **vLLM** box. The gold judge is **`openai/gpt-5.4`** (reasoning
medium); all headline numbers below are on that scale.

## Experiments

| dir | what | status |
|-----|------|--------|
| [`20260617-gemma4-temp/`](20260617-gemma4-temp/) | gemma-4-31b temperature sweep 0.0–1.0 on genai (thinking on), 3×/cell | complete |
| [`20260617-gold-rejudge/`](20260617-gold-rejudge/) | gpt-5.4 re-judge of all in-scope OpenRouter/qwen routes onto one scale | complete |
| [`20260621-glm-judge/`](20260621-glm-judge/) | GLM (z.ai) as a judge vs gold gpt-5.4 — 400 paired genai-gemma answers | complete |
| [`20260622-gemma-goldproxy/`](20260622-gemma-goldproxy/) | does gemma's gold-alignment survive without self-judging? (qwen + wandb) | complete |
| [`20260623-glm46-judge/`](20260623-glm46-judge/) | glm-4.6v as a judge vs glm-4.5v and gold — same 400 paired genai-gemma answers | complete |

## Headline findings

1. **Temperature doesn't matter for gemma accuracy.** 0.0→1.0 all sit 88–91% with
   overlapping CIs and no trend. The only signal: **temp=0.0 is the *noisiest*** (sd
   3.95 vs ≤1.5), not the most stable — greedy decoding still diverges with thinking on.

2. **wandb-bf16 ≈ genai on accuracy, and ~2.4× faster → wandb-bf16 is the gemma serving choice.**
   89.8% vs 90.8% (within noise) but 36.5 s vs 87.6 s per question. Where you serve
   gemma doesn't change *what* it scores; it changes *how fast*.

3. **siliconflow-fp8 is ~4 pt lower and slower** than wandb-bf16 (86.1%, 63.7 s).
   Provider and quant are confounded (siliconflow only ships fp8, wandb only bf16),
   so this is "fp8-as-served-by-siliconflow", not a clean quantization law.

4. **qwen-3.6-dense has its first gold point: 89.5%** (n=1, wandb-fp8) — squarely in
   gemma's band. It is otherwise unmeasured.

5. **Reasoning barely moves this exam.** gemma off/medium/high on genai are flat within
   noise (and medium==high are the *same* config there — genai gemma thinking is binary).
   The exam is near-ceiling for these models (~90% of 76 points).

### Serving scorecard — gemma-4-31b (gold, medium, t1.0)

| route | accuracy | speed (s/q) | verdict |
|-------|----------|-------------|---------|
| openrouter **wandb-bf16** | 89.8% | **36.5** | best overall |
| genai (Google) | 90.8% | 87.6 | accuracy-equiv, slow (free tier) |
| openrouter siliconflow-fp8 | 86.1% | 63.7 | cheaper but ~4 pt down |

## Methodology lessons (read before the next sweep)

- **Judge choice was the biggest confound.** Different judges grade differently
  (gemini-3.5-flash is lenient; gemma self-judge harsher), so any cross-route % must be
  on **one** judge. Fix: gold-re-judge existing answers — cheap, no new solves.
- **GLM (z.ai) is not a gold judge** (`20260621-glm-judge/`, `20260623-glm46-judge/`).
  GLM-5.2 is text-only — can't judge an image exam at all. The vision GLM `glm-4.5v`
  runs ~+4.4 pt lenient vs gpt-5.4 (higher in all 16 runs) *and* shares grok's
  equivalent-method blind spot (4 clear errors on the disputed set, tying grok). The
  newer `glm-4.6v` is a near-clone (+4.7 pt, 88% identical scores) that *fixes* the
  blind spot but over-credits harder elsewhere — the better of the two GLMs, still not
  gold-grade. z.ai's latest vision model, `glm-5v-turbo`, is plan-gated (pay-as-you-go
  only) and untested. gpt-5.4 stays the gold judge.
- **Judges are noisy too.** gemini-3.5-flash scored *identical* answers 97.4% vs 92.1%
  on a repeat pass (5.3 pt swing). Single-pass judging carries real variance; trust
  deltas, not third-decimal precision.
- **"reasoning=medium" is not one thing.** Binary thinking-on on genai (medium==high==on,
  off==minimal); a graded effort on OpenRouter; binary `enable_thinking` on vLLM/lmstudio.
  Compare like-for-like and verify the model actually thinks the same.
- **provider/quant live in the model slug, not the columns.** `runs.provider` /
  `runs.quantization` are NULL; the route is `...:wandb-bf16`. A `sweep` grid must
  enumerate literal slugs as the `model` axis or the deficit query won't count existing runs.
- **`presence_penalty` is ignored on the genai path** (it is applied on OpenRouter).
- **n=3 is underpowered for run-mean tests** (gold within-cell sd ≈ 2.2 pt). Prefer
  **paired per-question** analysis (same 25 items per route) to resolve ~2 pt deltas at n=3–5.
- Solves resume cleanly after transient `503` / disconnect blips — just re-run the same command.

## Open questions / roadmap

1. **qwen-3.6-dense reasoning-effort ladder** (off/low/medium/high/xhigh) — the highest-info
   experiment; qwen has *graded* effort that gemma-on-genai can't show. Watch the pp=1.5
   anti-loop guard and xhigh vs max_tokens truncation; sanity-run first.
2. **siliconflow-fp8 ~4 pt gap** — paired per-question follow-up to separate quant from provider.
3. **Re-solve the 3 contaminated routes** (`:novita-bf16`, `:parasail-fp8`, `:chutes-fp4`)
   that had missing-image (blind) answers, to make the quant ladder honest.
4. **Local vLLM on the z390 (dual RTX 3090 + NVLink, 48 GB).** Fits gemma/qwen at fp8 or
   int4 (tensor-parallel); the "does my own box match cloud?" rung. Note: only binary
   reasoning on that path.
5. **Controlled latency benchmark** (same time window, genai on a *paid* key) to make the
   wandb-vs-genai speed number rigorous rather than indicative.

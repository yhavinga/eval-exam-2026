# 20260622 — does gemma's gold-alignment survive without self-judging?

**Goal:** On the controlled bake-off (run 33), `gemma-4-31b-it` was the cheap judge
best aligned with gold `gpt-5.4` on the 7 disputed questions (5/7, beating flash's
3/7). But run 33 is **gemma grading its own answers**. This checks whether that edge
is real or a self-judge artifact, by re-running gemma as a judge on answers it did
**not** author and that gpt-5.4 has already scored.

**Headline:** The edge does **not** survive. On non-self answers gemma ties flash
overall (~90%) and *loses* to flash on exactly the questions that matter (the
partial-credit ones). gemma also runs consistently lenient where flash is centered.
So the run-33 5/7 was substantially flattered by self-judging. No cheap judge solos
the hard cases — which is the empirical case for an escalate-on-disagreement cascade.

## What was judged

gemma judged with the **same config as the run-33 self-judge** — `gemma-4-31b-it`,
genai, reasoning **high**, temp 1.0 (`judge_stack=genai`) — on two answer sets gpt-5.4
already graded:

| answer set | model relation to gemma | n | note |
|------------|-------------------------|---|------|
| `qwen/qwen3.6-27b:wandb-fp8` run 1 | **different model** (clean) | 25 | removes the self-judge concern entirely |
| `google/gemma-4-31b-it:wandb-bf16` runs 1–3 | **same weights, different serving** | 75 | weaker: same conceptual blind spots |

100 judgements, 0 errors, 0 unparsed. Gold = `openai/gpt-5.4` (openrouter, medium);
flash = `gemini-3.5-flash` (openrouter, low) is the competing free judge.

## Results — alignment with gpt-5.4

| metric (non-self) | **gemma** vs gpt-5.4 | **flash** vs gpt-5.4 |
|-------------------|----------------------|----------------------|
| overall per-question match (100 Q) | **90%** | **90%** |
| signed bias (judge − gpt) | **+0.10** (lenient) | **−0.02** (neutral) |
| match on hard / partial-credit Q (23) | **57%** (13/23) | **74%** (17/23) |
| match on panel-disputed gpt≠flash (10) | 60% (6/10, as tie-breaker) | — |

Per set:

| set | gemma overall | gemma bias | gemma hard | flash overall | flash bias | flash hard |
|-----|---------------|-----------|------------|---------------|-----------|------------|
| qwen (clean, n=25) | 88% | +0.12 | 3/6 | 84% | 0.00 | 3/6 |
| wandb (same wts, n=75) | 91% | +0.09 | 10/17 (59%) | 92% | −0.03 | 14/17 (82%) |

Reference — run 33 (gemma's **own** answers): gemma 5/7 (71%) on the disputed set,
flash 3/7. That gap is what fails to replicate.

## Reading it

- **Overall alignment holds (~90%) but is not special** — flash equals it. gemma's
  apparent run-33 superiority was the self-judge agreeing with gold on the hard parts
  of *its own* answers.
- **On the questions that matter, flash beats gemma** (74% vs 57% on partial-credit
  questions). The hard-case edge inverts once gemma isn't its own examiner.
- The wandb half is **same-weights** judging, where a self-correlation advantage for
  gemma should *help* it — and flash still wins there (82% vs 59% hard). That makes
  the conclusion stronger, not weaker.
- **gemma is structurally lenient (+0.10), flash is centered (~0).** For an *absolute*
  number a neutral judge beats a lenient one, so flash is the marginally better single
  free judge; for *ranking* they're interchangeable.
- **No free judge soloes the hard ~25%** (~60% agreement with gold on disputed
  questions). Where two cheap judges disagree, each is only ~60% right against gold —
  so disagreement is the correct, and only, escalation trigger.

## Caveats

- Small hard-question samples (qwen n_hard=6; combined n_hard=23). Directional, not
  precise — but the wandb half (n=75) carries the weight and points the same way.
- "hard" = gpt-5.4 awarded partial credit (score < max), a judge-independent proxy for
  "grading judgment mattered"; the panel-disputed cut (gpt≠flash) is the flash-dependent
  analog of run-33's "disputed".
- gemma genai reasoning is binary thinking-on at `high`; gpt-5.4/flash use graded
  effort. Same label, possibly different mechanism — but gemma's config is identical to
  run 33, so the run33-vs-here comparison for gemma is apples-to-apples.

## Provenance

- Judge logs: [`logs/`](logs/) (qwen + wandb).
- DB backup before judging: `natuurkunde/eval.db.bak-pre-20260622-gemma-align`.
- 100 new `gemma-4-31b-it` (genai, high, temp 1.0) judgements in `eval.db`.
- Commands:
  `python eval.py judge --judge-model gemma-4-31b-it --judge-base-url genai
  --judge-stack genai --temperature 1.0 --reasoning-effort high --answer-model
  qwen/qwen3.6-27b:wandb-fp8 --solve-runs 1 --solve-reasoning medium --judge-count 1`
  (and the same with `--answer-model google/gemma-4-31b-it:wandb-bf16 --solve-runs 1,2,3`).

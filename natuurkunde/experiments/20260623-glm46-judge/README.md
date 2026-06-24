# 20260623 — GLM-4.6v as a judge (z.ai), vs glm-4.5v and gold gpt-5.4

**Goal:** A newer vision GLM, `glm-4.6v`, became reachable on the z.ai Coding Plan.
Re-run the `20260621-glm-judge` measurement on it — same 400 answers, same gold
reference — and ask whether the newer model is a better judge than `glm-4.5v`, or at
least sheds its failure modes.

**Headline:** No upgrade as an absolute scorer. In aggregate `glm-4.6v` is a **near
clone of `glm-4.5v`** — 88.3% identical scores, net +0.01 pt/q between them — with the
same lenient ceiling (~+4.5 pt over gold). It has exactly one genuine, qualitative
gain: it **no longer carries grok's equivalent-method blind spot** (it credits the
mathematically-equivalent Beer–Lambert derivation that 4.5v and grok both docked). But
it over-credits harder elsewhere, so net leniency is unchanged. Cheap ranking
cross-check at best; `gpt-5.4` stays the gold judge.

## What changed since 20260621 (model availability is the real correction)

The `20260621-glm-judge` writeup claimed `glm-4.5v` was "the only vision-capable GLM on
the plan." That was wrong. Probing the coding endpoint directly with a real image (a
vision model tokenizes the image into hundreds of prompt tokens; a text-only model
silently drops it) gives a sharper map. The endpoint distinguishes three states by
error code, which is what makes the probe conclusive:

| model | endpoint response | meaning |
|-------|-------------------|---------|
| `glm-4.5v`, `glm-4.6v`, `glm-4.6v-flash` | HTTP 200, `prompt_tokens≈346` on a 512² image, reads it | **vision works** |
| `glm-5-turbo`, `glm-4.6` | HTTP 400 code 1210 `content.type invalid, allowed: ['text']` | **text-only** |
| `glm-5v`, `glm-5.1v`, `glm-5.2v` | HTTP 400 code 1211 `Unknown Model` | **does not exist** |
| `glm-5v-turbo` | HTTP 429 code 1311 `subscription plan does not yet include access` | **real, plan-gated** |

So z.ai's *latest* vision model, `glm-5v-turbo` (released 2026-04-01, a vision-coding
base model), exists but is gated off the Coding Plan — the 1311 code is a billing tier,
not the 1211 "unknown model" returned for ids that don't exist. It is pay-as-you-go
only ($1.20/M in, $4.00/M out), and the Coding Plan key has no metered balance, so it
could not be measured here. The newest vision GLM actually callable on the plan is
`glm-4.6v` — which is what this experiment judges. (`glm-4.6v-flash` is also free and
vision-capable, an untested cheaper option.)

## What was judged

Identical to 20260621 so every number is comparable: `judge-count=1`, **genai
`gemma-4-31b-it`, reasoning=medium, runs 1–3 = 400 answers**, judged at reasoning
**medium**, temperature 1.0, tagged `judge_stack=zai`. `gpt-5.4` and `glm-4.5v` already
cover exactly these 400, so each `glm-4.6v` score pairs 1:1 with both. The set includes
the run-33 bake-off (answer_ids 793–817), where ground truth is established. **400
scored, 0 errors.**

**Operational note (cost a re-run otherwise):** the z.ai/OpenAI code path has no
retry/backoff — that logic lives only on the genai branch. So a rate-limit reply
becomes a hard error, not a wait-and-retry. At `--concurrency 20` the opening burst
drew ~24% HTTP 429 (code 1302 `Rate limit reached`); **`--concurrency 8` ran clean**.
And `judgements` has no unique constraint, so an errored (null-score) row must be
deleted before re-judging or the retry inserts a duplicate. The working pattern is a
loop of {delete null rows → judge (the runner skips any answer that already has a
non-null score)} until all 400 land.

## Results — glm-4.6v

### Aggregate (400 paired), against gold and against glm-4.5v

| metric | **glm-4.6v** vs gold | glm-4.5v vs gold | glm-4.6v vs glm-4.5v |
|--------|----------------------|------------------|----------------------|
| exact per-question agreement | **79.5%** (318/400) | 77.3% (309/400) | **88.3%** (353/400) |
| mean signed diff | **+0.142 pt/q** | +0.133 pt/q | **+0.01 pt/q** |
| MAE | **0.228** | 0.273 | — |
| higher / equal / lower | **69 / 318 / 13** | 71 / 309 / 20 | 25 / 353 / 22 |
| overall % (same answers) | **94.7% vs 90.0%** (+4.7) | 94.3% vs 89.9% (+4.4) | — |
| higher in every answer-run | **yes** (+5.3 / +4.8 / +3.9) | yes (all 16) | — |

Diff distribution (glm-4.6v − gold): −2: 4 · −1: 9 · 0: 318 · +1: 64 · +2: 5. The
leniency is one-directional — 73 over-credits to 13 under-credits (5.3:1, vs 4.5v's
3.6:1). Marginally tighter than 4.5v on agreement and MAE, marginally more lenient on
level; the +0.01 pt/q against 4.5v says the two are, for scoring purposes, the **same
instrument**.

### Ground truth — run 33's 7 disputed questions

Same fixed 25 answers as the bake-off; truth from the blind multi-adjudicator review
(Q08 3-or-4 and Q18 1-or-2 count as defensible).

| Q | truth | glm-4.5v | **glm-4.6v** | gpt-5.4 | gemma | flash | grok |
|---|-------|----------|--------------|---------|-------|-------|------|
| Q02 | **1** | 2 ✗ | **2 ✗** | 1 ✓ | 1 ✓ | 2 ✗ | 0 ✗ |
| Q08 | 3 (4 ok) | 4 ~ | **4 ~** | 3 ✓ | 4 ~ | 4 ~ | 4 ~ |
| Q18 | 1–2 | 1 ~ | **3 ✗** | 2 ~ | 2 ~ | 2 ~ | 1 ~ |
| Q19 | 2 | 2 ✓ | **2 ✓** | 2 ✓ | 2 ✓ | 1 ✗ | 2 ✓ |
| Q21 | **2** | 3 ✗ | **3 ✗** | 2 ✓ | 3 ✗ | 0 ✗ | 3 ✗ |
| Q24 | **2** | 1 ✗ | **2 ✓** | 2 ✓ | 2 ✓ | 2 ✓ | 0 ✗ |
| Q25 | **2** | 3 ✗ | **2 ✓** | 2 ✓ | 2 ✓ | 2 ✓ | 3 ✗ |
| **clear errors / 7** | | **4** | **3** | **0** | 1 | 3 | 4 |

Run-33 total: **glm-4.6v 75/76 (98.7%)** — the most lenient total of any judge measured
(glm-4.5v 73, flash-v1 74, gemma 73, gpt-5.4 71, grok 70; true ≈ 69–70). 4.6v reaches
near-full marks while making three clear errors, **all over-credits** — it has no
compensating under-credit at all, unlike 4.5v whose Q24 under-credit partly masked its
leniency in the total.

### Where 4.6v differs from 4.5v on the disputes

- **It sheds the equivalent-method blind spot (Q24, Q25).** This is the one real
  improvement. On Q24 — Beer–Lambert `I=I₀e^(−μx)` being mathematically identical to the
  halveringsdikte formula — `glm-4.5v` wrote "wiskundig equivalent" and docked the point
  anyway, the same rule-3.3 violation that disqualifies grok. `glm-4.6v` awards the
  point. It also stops over-reading Q25 to full marks.
- **It introduces a new over-credit (Q18).** Where 4.5v scored 1 (low end of the
  defensible 1–2), 4.6v awards the full 3 — outside the defensible range. The blind spot
  it fixed is replaced by leniency it didn't have, which is why the aggregate barely
  moves.
- **The shared errors persist (Q02, Q21).** Both over-read the Q02 placeholder-scale
  reasoning and the Q21 ">90°-vs-90°" trap. These are the lenient-cluster failures, not
  the rule-3.3 ones.

## Verdict

1. **`glm-4.6v` is the better GLM judge of the two** — newer, free on the plan, lower
   MAE, higher agreement, one fewer clear error, and no rule-3.3 blind spot. If a GLM
   judge is ever wanted, prefer it over `glm-4.5v`.
2. **But it is not gold-grade and not an absolute scorer.** Same ~+4.5 pt lenient
   ceiling, three clear errors all in the over-credit direction, the highest run-33 total
   on record. Use it for **ranking** cross-checks only.
3. **`gpt-5.4` remains the gold judge** — still the only judge with zero clear errors on
   the disputed set. This experiment reinforces it.
4. **The latest vision GLM (`glm-5v-turbo`) is untested** — plan-gated, pay-as-you-go
   only. Whether the 5V generation breaks the leniency pattern is an open question that
   needs a metered top-up to answer.

## Provenance

- Judge log: [`judge_glm-4.6v_gemma-4-31b-it_genai_medium.log`](judge_glm-4.6v_gemma-4-31b-it_genai_medium.log).
- 400 new `glm-4.6v` judgements (`judge_stack=zai`, temp 1.0, reasoning medium) in
  `natuurkunde/eval.db`; prior state is the parent commit.
- Run-33 bake-off set = answer_ids 793–817 (one answer per question, ans_run 2);
  identified by reproducing the committed glm-4.5v and gpt-5.4 columns exactly (7/7).
- Command (per loop iteration):
  `python eval.py judge --judge-model glm-4.6v --judge-base-url
  https://api.z.ai/api/coding/paas/v4 --judge-stack zai --temperature 1.0
  --reasoning-effort medium --answer-model gemma-4-31b-it --solve-runs 1,2,3
  --solve-reasoning medium --judge-count 1 --concurrency 8`

# 20260621 — GLM as a judge (z.ai), vs gold gpt-5.4

**Goal:** Test whether a GLM model from the z.ai Coding Plan is useful as a judge,
and how it compares to the gold judge (`openai/gpt-5.4`, reasoning medium).

**Headline:** No — not gold-grade. The requested **GLM-5.2 is text-only and cannot
judge this image-based exam at all**; the only vision-capable GLM on the plan,
**`glm-4.5v`**, is a **lenient** judge (~+4.4 pt vs gpt-5.4) that *also* carries
grok's equivalent-method blind spot. Use gpt-5.4; glm-4.5v is at best a cheap
ranking cross-check.

## Setup (what was wired in)

- **Endpoint:** OpenAI-compatible, `https://api.z.ai/api/coding/paas/v4` (the *coding*
  path — the metered `/api/paas/v4` returns "Insufficient balance"; the unlimited
  Coding Plan routes through coding). Key in top-level `.env` as `ZAI_API_KEY`.
- **Code:** `eval.py get_api_key()` resolves `"z.ai" in base_url` → `ZAI_API_KEY`;
  `judge_async.py _build_extra_body()` injects `reasoning_effort` for z.ai base_urls
  (GLM returns an *empty* completion if no reasoning control is sent). Invoke with
  `--judge-stack zai --judge-base-url https://api.z.ai/api/coding/paas/v4`.

## Vision probe (why GLM-5.2 was disqualified)

The judge sends the question image + the correctievoorschrift image; there is no text
CV. Direct tests on the coding endpoint:

| model | image handling |
|-------|----------------|
| `glm-5.2` | **text-only** — silently drops image content (`prompt_tokens` 20→55 for a 146 KB image), replies "I can't see an image" |
| `glm-4.6` | rejects: `content.type invalid, allowed values: ['text']` |
| `glm-5v` / `glm-5.2v` | "Unknown Model" |
| **`glm-4.5v`** | **vision works** (`prompt_tokens=909`; read the CV's max points + result) |

So glm-4.5v was used as the GLM judge, reasoning **medium**, temperature 1.0 — matched
to the gold gpt-5.4 config.

## What was judged

`judge-count=1`. **genai `gemma-4-31b-it`, reasoning=medium, runs 1–3 = 400 answers**
(16 complete runs × 25 questions). gpt-5.4 already covers exactly these answers, so
every glm score pairs 1:1 with a gold score. Set includes the multi-judge bake-off
**run 33** (where ground truth is established). **400 scored, 0 errors, 0 unparsed, 0
missing-image flags.**

## Results — glm-4.5v vs gpt-5.4

### Aggregate (400 paired answers)

| metric | value |
|--------|-------|
| exact per-question agreement | **77.3%** (309/400) |
| mean signed diff (glm − gpt) | **+0.133 pt/q** (lenient) |
| MAE | 0.273 |
| glm higher / equal / lower | **71 / 309 / 20** (over-credits 3.6:1) |
| overall % (same answers) | **glm 94.4% vs gpt-5.4 90.0%** (≈ +4.4 pt) |
| per-run delta (16 runs) | **all positive, +1.3 … +11.8** |

Diff distribution (glm − gpt): −2: 8 · −1: 12 · 0: 309 · +1: 61 · +2: 10.
The leniency is systematic — glm reads higher in **every** run, not via a few outliers.

### Ground truth — run 33's 7 disputed questions

Slotted into the existing bake-off (see `LEARNINGS_JUDGES_20260616.md`). Truth from the
blind multi-adjudicator review; Q08 (3-or-4) and Q18 (1-or-2) count as defensible.

| Q | truth | glm-4.5v | gpt-5.4 | gemma | flash | grok |
|---|-------|----------|---------|-------|-------|------|
| Q02 | **1** | 2 ✗ | 1 ✓ | 1 ✓ | 2 ✗ | 0 ✗ |
| Q08 | 3 (4 ok) | 4 ~ | 3 ✓ | 4 ~ | 4 ~ | 4 ~ |
| Q18 | 1–2 | 1 ~ | 2 ~ | 2 ~ | 2 ~ | 1 ~ |
| Q19 | 2 | 2 ✓ | 2 ✓ | 2 ✓ | 1 ✗ | 2 ✓ |
| Q21 | **2** | 3 ✗ | 2 ✓ | 3 ✗ | 0 ✗ | 3 ✗ |
| Q24 | **2** | 1 ✗ | 2 ✓ | 2 ✓ | 2 ✓ | 0 ✗ |
| Q25 | **2** | 3 ✗ | 2 ✓ | 2 ✓ | 2 ✓ | 3 ✗ |
| **clear errors / 7** | | **4** | **0** | 1 | 3 | 4 |

glm-4.5v makes **4 clear errors — tying grok for worst** — despite the 2nd-highest
*total* on run 33 (73/76 = 96.1%, behind only flash-v1's 74). That total is the
**compensating-errors illusion**: over-credits (Q02/Q21/Q25, +3) nearly cancel an
under-credit (Q24, −1).

Run 33 totals (all judges, same 25 answers): flash-v1 74 (97.4%) · **glm-4.5v 73
(96.1%)** · gemma 73 (96.1%) · gpt-5.4 71 (93.4%) · flash-v2 70 · grok-v2 70 · grok-v1
67. glm agrees with flash 88% of the time on run 33 — it sits with the lenient cluster.

### The two failure modes (from glm's own motivations)

- **Lenient over-crediting** (like flash/gemma): accepts Q02's placeholder scale
  reasoning, over-reads the Q21 ">90°-vs-90°" trap, awards full marks on Q25.
- **grok's equivalent-method blind spot** (Q24): glm explicitly writes *"Hoewel de
  formules wiskundig equivalent zijn"* ("although the formulas are mathematically
  equivalent") — then docks the point anyway for not using the CV's literal
  halveringsdikte formula. Directly violates the v2 prompt's rule 3
  (*"reken een gelijkwaardige correcte methode dus NIET fout"*). A rule in the prompt
  only helps a judge that applies it.

## Verdict

1. **GLM-5.2 cannot judge this exam** (text-only). The ask is unmet by 5.2.
2. **glm-4.5v is not a replacement for gpt-5.4.** It is a soft *ceiling* (lenient,
   ~+4.4 pt) and carries the rule-3.3 blind spot — worst-of-both vs the existing bench.
   Keep it, at most, as a cheap **ranking** cross-check; never for absolute scores.
3. **gpt-5.4 remains the gold judge** — this experiment reinforces it (0 clear errors,
   uniquely correct on Q21/Q24).

## Provenance

- Judge log: [`logs/judge_glm-4.5v_gemma-4-31b-it_genai_medium.log`](logs/).
- DB backup before judging: `natuurkunde/eval.db.bak-pre-20260621-glm45v-judge`.
- 400 new `glm-4.5v` judgements (`judge_stack=zai`, temp 1.0, reasoning medium) in `eval.db`.
- Command: `python eval.py judge --judge-model glm-4.5v --judge-base-url
  https://api.z.ai/api/coding/paas/v4 --judge-stack zai --temperature 1.0
  --reasoning-effort medium --answer-model gemma-4-31b-it --solve-runs 1,2,3
  --solve-reasoning medium --judge-count 1 --concurrency 8`

# LEARNINGS — Judges & judge reliability

**Date:** 2026-06-16 · **Related commits:** `0e54f92` (missing-image flag), `bdfbb68` (v2 judge prompt with official scoring rules)

The judge is the measuring instrument of this whole project: every model-performance number is only as trustworthy as the LLM that produced it. This file records what we learned about that instrument — which judges we tried, how they fail, how to combine them, and which one to trust.

## Judge roster (everything we tried)

| Judge model | stack | reasoning | role / notes |
|---|---|---|---|
| **gemini-3.5-flash** | openrouter | low | The workhorse for the model-performance grids. Fast, cheap, reliable for *ranking*; tilts **lenient** on absolute level. |
| **gemma-4-31b-it** | genai + openrouter | high/medium/low | Used both as a neutral judge and as a **self-judge** (it also produced most answer runs). Decent; mildly lenient on figure-description questions. |
| **google/gemma-4-26b-a4b-it** | openrouter | off | A smaller gemma, tried briefly as a cheaper judge (25 answers). Not pursued — no advantage over the 31b. |
| **gpt-4o** | openrouter | off (none) | Used only to *validate the missing-image flag* (it has no graded reasoning mode). |
| **x-ai/grok-4.3** | openrouter | low | Bake-off candidate. Recent/strong general model but the **worst judge on disputes** — see below. |
| **openai/gpt-5.4** | openrouter | medium | The strongest judge found. **Zero clear errors** on the disputed set. Recommended primary. |

Convention: when the same judge_model grades the same answers twice, `run_number=1` is the **v1** prompt and `run_number=2` is the **v2** prompt (`--judge-count 2` without `--force` preserves run #1 and appends run #2). gemma's v2 pass is its own first run on a separate judge_model id.

## The judge prompt: v1 → v2 (BEOORDELINGSREGELS), commit `bdfbb68`

v1 asked the judge to compare an answer against the correctievoorschrift (CV) image with the `[SCORE=]/[MAX=]/[MISSING_IMAGE=]` markers. v2 **embeds a condensed version of the exam board's official general scoring rules** ("algemene regels") into the prompt. The rules that actually bite:

- **Equivalent methods are credited** (rule 3.3 — *"in de geest van het model — reken een gelijkwaardige correcte methode dus NIET fout"*): a physically valid alternative route to a scorepunt's goal must not be marked wrong.
- **The 'completeren' point is withheld** on a calculation error or a wrong final result (vakspecifieke regel 2).
- **An error is penalised once** (no double jeopardy / doorwerkfout, rule 5).
- **Integer scores only** (rule 2) — no half points, which is also why averaging judge scores is illegal (see Mediation).

**Effect of v2.** It did *not* make judges uniformly agree; it made their errors **more idiosyncratic** rather than systematic. On run 33 it pulled flash down (97.4% → 92.1%, i.e. less reflexively lenient) and lifted grok (88.2% → 92.1%). But it did **not** cure grok's core failure mode — grok still zeroes legitimate equivalent methods (Q24/Q02) despite the rule explicitly forbidding it. A rule in the prompt only helps a judge that can apply it.

## The controlled bake-off — run 33

The cleanest experiment we have: **one fixed set of answers** (gemma-4-31b-it, genai, run 33 — 25 questions, 76 points) graded by **four judges, all on the v2 prompt**. Same answers → every score difference is the *judge*, not the run.

**Totals:** gemma 73/76 (96.1%) · gpt-5.4 71/76 (93.4%) · flash 70/76 (92.1%) · grok 70/76 (92.1%).

18 of 25 questions were unanimous (57 pts, taken as correct). The judges disagree on exactly **seven** questions. We established **ground truth** for all seven by blind multi-adjudicator review against the CV images (see *Adjudication method*):

| Q | ground truth | gemma | flash | grok | **gpt-5.4** | what the dispute is |
|---|---|---|---|---|---|---|
| Q02 | **1** | 1 ✓ | 2 ✗ | 0 ✗ | **1 ✓** | student used a placeholder bar length, not the figure's scale → 2nd point not earned |
| Q08 | **3** (4 defensible) | 4 ~ | 4 ~ | 4 ~ | **3 ✓** | "onnauwkeurigheid in de *opgegeven waarde*" = sig-fig precision (±0.5 Ω), not invented resistor tolerance |
| Q18 | **1–2** (both ok) | 2 ~ | 2 ~ | 1 ~ | **2 ~** | misread angle 55° (outside 48–52°); completion point is the strict/lenient swing |
| Q19 | **2** | 2 ✓ | 1 ✗ | 2 ✓ | **2 ✓** | electron penetration depth small → tumour superficial; fully correct answer |
| Q21 | **2** | 3 ✗ | 0 ✗ | 3 ✗ | **2 ✓** | left figure needs **>90°** deflection; student wrote "straight down" (=90°) → 1 of 3 points lost |
| Q24 | **2** | 2 ✓ | 2 ✓ | 0 ✗ | **2 ✓** | Beer–Lambert `I=I₀e^(−μx)` is mathematically identical to the halveringsdikte formula (rule 3.3) |
| Q25 | **2** | 2 ✓ | 2 ✓ | 3 ✗ | **2 ✓** | grok over-credited |

**Verified accuracy scorecard** (treating Q08 3-or-4 and Q18 1-or-2 as defensible either way — only clear, indefensible calls count as errors):

| judge | clear errors / 7 | which |
|---|---|---|
| **gpt-5.4** | **0** | — |
| gemma (self) | 1 | Q21 |
| flash | 3 | Q02, Q19, Q21 |
| grok | 4 | Q02, Q21, Q24, Q25 |

### The headline insight: a correct *total* does not mean an accurate *judge*

The true score of run 33 is **≈69–70/76**. Note that flash (70) and grok (70) land almost exactly on the true total — but **by luck, through compensating errors that cancel**: flash over-credits Q02/Q08 and under-credits Q19/Q21; grok over-credits Q21/Q25 and zeroes Q02/Q24. gpt-5.4 (71) is closest to truth **and** reaches it with individually correct/defensible per-question scores. **Always check per-question agreement, never just the total** — a judge can be right on the bottom line for entirely wrong reasons.

### Per-judge failure modes (the durable takeaways)

- **gpt-5.4 (medium)** — most accurate; 0 clear errors. The *only* judge to resolve Q21 (the >90°-vs-90° trap that fooled every other judge in one direction or the other). Its one borderline call (Q08, docks to the strict-correct 3) means it runs **slightly strict on genuinely ambiguous points** — the mirror image of flash. Read its absolute % as a soft **floor**.
- **flash** — **lenient at the top** (over-credits placeholder reasoning, awards full marks despite minor slips), yet **high-variance**: it can swing harsh on the wrong cue (Q21 → 0 *because the student described instead of drew*; Q19 → 1). Reliable for *ranking*, not for absolute level. Soft **ceiling**.
- **gemma (self-judge)** — solid; only failure here was over-crediting its own Q21. Mildly lenient on figure-*description* answers (accepts prose where a drawing was asked).
- **grok-4.3** — **avoid as a sole judge.** Despite being a strong general model it is the *least* accurate on disputes because it rigidly demands the CV's *exact* method and *exact* source and **penalises valid equivalent methods** — the precise thing rule 3.3 forbids. It zeroed a textbook-correct Beer–Lambert derivation (Q24) and a correct scale-uncertainty estimate (Q02). Its "harshness" is not rigour; it is a rule-3.3 blind spot.

## Adjudication method (how ground truth was established)

Ground truth was **not** taken from any single judge or from a prior summary (an earlier hand-tally was found internally inconsistent — e.g. it credited grok 3/5 where a recount gave 2/5). Instead, for each disputed question we ran **independent blind adjudicators** (subagents that read the question + CV images directly and fetch the student answer from the DB, never told what any judge scored), plus, for the two hardest, an **adversarial confront** step that laid out the strict-vs-lenient readings explicitly and asked which the CV wording supports.

- **Q08** — 3 blind lenses split (strict→3, generous→4, neutral→4, all flagging genuine ambiguity), but **both** confront arbiters ruled `gpt54_correct_dock`: the first scorepunt says *"onnauwkeurigheid in de **opgegeven waarde**"* and the CV's worked example derives ±0.5 Ω purely from "60 Ω" being 2 sig-figs. The student substituted resistor color-band tolerance — a *different physical quantity*, not an equivalent *method*, so rule 3.3 does not rescue it. gpt-5.4 right; award (4) defensible under geest-van-het-model leniency.
- **Q21** — both blind adjudicators independently returned **2/3** (left-figure path wrong: "rechte lijn naar beneden" = 90°, CV requires >90° exiting left of Q; right-figure and outside-field points earned). Matches gpt-5.4 exactly.

## Self-judging bias — judge-specific, and not a name-recognition effect

- The judge prompt contains **no model names** — neither the judge's own nor the answer model's. So self-judging cannot be a name-recognition effect; the residual risk is **correlated blind spots** (a model failing to see its own conceptual errors).
- gemini-3.5-flash grading **its own** answers: 98.7% (inflated); opus 100%.
- gemma self-judging run 33 scored **73/76 (96.1%)** — about **+3–4 above the true ≈69–70**, via lenient/wrong calls on Q08 and Q21, *not* via self-recognition. So gemma isn't "inflating because it knows it's grading itself"; it is simply a **mildly lenient judge in general**. Don't assume self-judging always inflates — but never use a self-judge for an **absolute** score; for relative ranking on identical answers it tracked neutral judges closely.

## Missing-image judge flag (feature, `0e54f92`)

- The judge emits `[MISSING_IMAGE=ja/nee]` when an answer reports a missing/unseen figure. The **numeric score stays faithful to the answer key** (an orthogonal flag, not a sentinel — preserves aggregates). At session end the runner prints `IMPORTANT Qx,..Qz are reported to have missing images`. The marker persists inside `motivation` (queryable, no schema change).
- **Validated**: gpt-4o judging a corrupted gemma run flagged exactly **Q07 & Q25** (the real missing-image answers), **0 false positives**, scores stayed 0/3.
- **Limitation**: catches **loud** complaints only; a silent hallucination (model invents an answer, no complaint) is undetectable from text → re-run is the only remedy. See `LEARNINGS_OPENROUTER_IMAGE_INTEGRITY`.

## Mediation — combining multiple judges without an extra LLM call or human review

- **Per-question median, then sum** — not the average, not the median-of-totals.
  - *Not the average*: averaging gives fractional scores, but scorepunten are **integers** (v2 rule 2) — a 1.5 is an illegal score the exam can't produce.
  - *Not the median-of-totals*: that gives no per-question outlier correction — a judge can be wildly wrong on Q21 yet have a defensible total (the compensating-errors trap above). Median **per question** cancels each judge's idiosyncratic miss independently.
  - Use an **odd** panel so the median is unambiguous; with 3 judges the median equals the majority whenever any two agree.
- **But a panel is not free, and not always better.** A median panel only helps when judges are of **similar quality with uncorrelated errors**. When one judge is **decisively better**, mixing it with weaker, more-lenient judges **drags its correct strict calls back toward the lenient consensus**. On run 33 a 3-judge median (e.g. gemma+flash+grok = 73, or gpt-5.4+two others = 72) is **less accurate** than gpt-5.4 alone (71, ≈ the true 69–70): the panel would restore Q08 to 4 and risk restoring Q21 to 3 by outvoting the one judge that got them right.

## Net recommendation

1. **Primary judge: gpt-5.4, reasoning medium, v2 prompt.** Only judge with zero clear errors on the disputed set; uniquely correct on the hardest question (Q21); closest-to-true total without compensating errors. Pricier than flash/gemma but negligible per 25-question run.
2. **Treat its absolute % as a soft floor** (slightly strict on genuinely-ambiguous points like Q08). To match *human* CvTE grading, which applies geest-van-het-model leniency, a borderline point may go the other way.
3. **Keep flash and gemma as cheap cross-checks** for ranking and for per-question disagreement detection — but flash is a soft *ceiling* (lenient) and gemma must not grade itself for absolute numbers.
4. **Do not use grok-4.3 as a sole judge** — it violates the equivalent-method rule and over-penalises valid alternative derivations.
5. **Fall back to a per-question median panel only** when grading a *new* run where you don't yet know where the disputes are, or when you specifically want to soften gpt-5.4's strictness toward human leniency. On a run whose disputes are already adjudicated, the best single judge beats the panel.

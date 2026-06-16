# LEARNINGS — Judges & judge reliability

**Date:** 2026-06-16 · **Related commit:** `0e54f92` (missing-image flag)

## Missing-image judge flag (feature, `0e54f92`)
- The judge emits `[MISSING_IMAGE=ja/nee]` in its verdict block when the answer reports a missing/unseen figure. The **numeric score stays faithful to the answer key** (an orthogonal flag, not a sentinel — preserves aggregates). At session end the runner prints `IMPORTANT Qx,..Qz are reported to have missing images`. The marker persists inside `motivation` (queryable, no schema change).
- **Validated**: gpt-4o judging a corrupted gemma run flagged exactly **Q07 & Q25** (the real missing-image answers), **0 false positives**, scores stayed 0/3.
- **Limitation**: catches **loud** complaints only; a silent hallucination (model invents an answer, no complaint) is undetectable from text → re-run is the only remedy.

## Self-judging bias is judge-specific, not universal
- gemini-3.5-flash grading **its own** answers: 98.7% (inflated); opus 100%.
- BUT **gemma's self-judge is NOT inflated vs a neutral judge on the same answers**: run 33 gemma-self **96.1%** vs flash **97.4%** — agreed on **24/25**, flash even slightly more lenient. ⇒ don't assume self-judging always inflates; measure it.

## "Judge the judge" findings (flash on the gemma batch)
- The scary-looking **"flash judges gemma 89.5% vs gemma-self 96.1%" gap was a RUN-vs-RUN confound**, not judge harshness: run 33 was simply a strong run (both judges ~96–97% on it); runs 4–9 were average. On *identical* answers, flash ≈ gemma.
- Adversarial audit (8 questions vs the official answer key): **7/8 flash scores accurate**, and the cross-run score variance was **justified by genuinely different answers** (temp=1.0). **1 real inconsistency** — Q15: flash penalized a *calculated* intensity in one run but rewarded the same approach in another.
- **Hand-adjudicated Q21 against the key**: flash **WRONG** (3/3 — over-credited; it misread the student's "exits right of Q, straight down" as ">90°"), gemma **RIGHT** (2/3). So on the one disagreement flash erred **lenient**, not harsh.
- **Flash leniency at the top**: 76–80% full-marks rates on a hard exam; awards full marks despite minor slips (e.g. "centrifugal" vs "centripetal" still scored 3/3).

## Net verdict on flash as a judge
- **Reliable for relative ranking and partial-credit**, but tilts **slightly lenient** on absolute level (read absolute % as a soft ceiling). It is **not harsh** — the initial hunch was wrong.
- **Caveats / recommendations**: `judge_count=1` is a single sample (~1 pt noise); a single judge model carries its own bias; self-judging inflates for some models. For trustworthy rankings use a **multi-count grid + a neutral third judge**, and never let a model grade itself for absolute scores.

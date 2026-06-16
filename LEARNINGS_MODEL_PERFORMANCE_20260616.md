# LEARNINGS — Model performance & provider/stack comparison

**Date:** 2026-06-16 · **Exam:** VWO physics, 25 questions, 76 points · **Judge:** gemini-3.5-flash (reasoning=low, judge_count=1) unless noted

## Leaderboard (flash-judged)
| Model | config | score |
|---|---|---|
| claude-opus-4.8 | reasoning medium | **100.0%** |
| gemini-3.5-flash | reasoning medium | 98.7% ⚠️ self-judge |
| gemma-4-31b-it (genai) | medium | 90.6% (n=7) |
| gemma-4-31b-it (wandb, bf16) | medium | 89.5% (n=7) |
| gemma-4-31b-it (siliconflow, fp8) | medium | 87.2% (n=7) |
| claude-opus-4.8 | reasoning **off** | 88.2% |
| gpt-4o | no reasoning mode | 67.1% |

## Reasoning on vs off — the big lever
- **opus-4.8**: medium 100% vs off 88.2% → **+12 pts** (9/76).
- **gemma-4-31b-it (genai, gemma-judged)**: on (high≡medium) 96.1% vs off 88.2% → **+8 pts** (6/76).
- **Cost**: thinking on ≈ **4× the wall-clock** (genai gemma ~35 min/run on vs ~9 min off). Decode rate is the same (~25 tok/s) — the extra time is purely reasoning tokens.

## Provider/stack comparison — gemma-4-31b-it, medium, flash-judged, n=7 each
| stack | quant | mean | sd | 95% CI |
|---|---|---|---|---|
| genai (direct) | native | 90.6% | 3.84 | [87.7, 93.5] |
| wandb (OpenRouter) | bf16 | 89.5% | 2.14 | [87.9, 91.1] |
| siliconflow (OpenRouter) | fp8 | 87.2% | 2.61 | [85.2, 89.2] |

- **No significant difference** (one-way ANOVA p=0.118). Pairwise Welch: genai–wandb p=0.51, genai–siliconflow p=0.08, wandb–siliconflow p=0.10.
- **genai ≈ wandb-bf16** — identical means; on the *same* answers (run 33) they tracked within ~1 pt. Routing through OpenRouter (bf16) vs hitting Google directly makes no measurable difference.
- **Only hint of a real effect: fp8 (siliconflow) trails bf16/native by ~2–3 pts** — consistent with quantization, but not significant.
- **Reasoning confirmed ON for both OR providers** (100% of answers had traces; siliconflow ~6172 vs wandb ~5622 chars — ~10% longer thinking yet scored slightly lower → not a quantity effect). Clean apples-to-apples.

## Speed (answer time, end-to-end incl. accumulating images)
| run | mean/q | total/run |
|---|---|---|
| gpt-4o (off) | 8 s | ~3.5 min |
| opus-4.8 (off) | 13 s | ~5 min |
| gemini-flash (medium) | 16 s | ~7 min |
| opus-4.8 (medium) | 23 s | ~10 min |
| gemma wandb (medium) | 34 s | ~14 min |
| qwen3.6-27b wandb (medium) | 78 s | ~33 min (very long reasoning) |
| gemma genai (medium) | ~85 s | ~35 min |

Throughput ~20–72 tok/s. Slow wall-clock is usually *more reasoning tokens*, not slow decode.

## Statistical methodology (hard-won)
- **n=2 lies.** siliconflow vs wandb looked like ~6 pts at n=2 (siliconflow's two early runs were unluckily low). At **n=7** the gap shrank to ~2.3 pts and was **not significant** (siliconflow mean rose 84→87% with more samples).
- To resolve a ~2-pt difference at 95% confidence you need roughly **~15–20 runs/group**.
- Report mean ± 95% CI; use Welch t-test / one-way ANOVA. Overlapping CIs + p>0.05 = not distinguishable, even with a large Cohen's d (low power at small n).
- temp=1.0 makes every run's answers genuinely different → run-to-run variance is real sampling spread, not measurement error.

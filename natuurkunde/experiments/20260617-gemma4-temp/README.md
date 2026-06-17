# 20260617 — gemma-4-31b temperature sweep (genai)

**Goal:** Does sampling temperature (0.0 / 0.3 / 0.5 / 0.7 / 1.0) change `gemma-4-31b-it`
accuracy on the VWO physics exam, run on Google's genai stack with thinking on?

## Configuration

| Dimension | Value |
|-----------|-------|
| model | `gemma-4-31b-it` |
| inference_stack | `genai` (`https://generativelanguage.googleapis.com/v1`) |
| temperature | **0.0, 0.3, 0.5, 0.7, 1.0** (swept axis) |
| top_p / top_k | 0.95 / 20 |
| max_tokens | 32768 |
| reasoning_effort | `medium` (on genai, Gemma = thinking-on default) |
| presence_penalty | none (not applied on the genai path) |
| replications | 3 complete runs per temperature (15 runs, 25 questions each) |
| judge | `openai/gpt-5.4` via openrouter, reasoning `medium`, 1×/answer |

## Results (scored by openai/gpt-5.4, reasoning=medium)

| temperature | n | mean% | sd | 95% CI |
|-------------|---|-------|------|---------------|
| 0.0 | 3 | 88.2 | 3.95 | [78.4, 98.0] |
| 0.3 | 3 | 91.2 | 0.76 | [89.3, 93.1] |
| 0.5 | 3 | 89.0 | 0.76 | [87.1, 90.9] |
| 0.7 | 3 | 90.8 | 1.32 | [87.5, 94.1] |
| 1.0 | 3 | 89.9 | 1.52 | [86.1, 93.7] |

Per-run raw scores (points out of 76):

| temperature | run scores | run ids |
|-------------|------------|---------|
| 0.0 | 67, 64, 70 | 69, 73, 74 |
| 0.3 | 69, 70, 69 | 70, 72, 71 |
| 0.5 | 68, 67, 68 | 62, 63, 67 |
| 0.7 | 70, 68, 69 | 60, 64, 66 |
| 1.0 | 69, 69, 67 | 61, 65, 68 |

## Conclusion

**No distinguishable effect of temperature on accuracy at n=3.** Cell means sit between
88.2% and 91.2% (~3-pt spread) with no monotonic trend, and all five 95% CIs overlap —
the differences are within run-to-run noise.

Two secondary observations (both n=3-fragile, treat as hints not findings):
- **temp=0.0 was the *least* stable, not the most** (sd 3.95 vs ≤1.5 elsewhere; runs
  scored 84/88/92%). Greedy decoding did not give deterministic results here — with
  thinking on, backend nondeterminism still produces divergent reasoning chains, and at
  n=3 one weak run swings the cell.
- temp=0.3 looked marginally best and tightest (91.2%, sd 0.76), but not separably so.

The earlier worry that sub-1.0 temperatures would make reasoning ramble to the token cap
did **not** materialise — no truncated/degraded answers. The three solve failures across
the whole sweep were transient genai blips (`503` / server-disconnect on Q16@0.7,
Q20@1.0, Q14@0.0), all fixed by re-solving.

To resolve the ~3-pt spread you'd need ~15–20 runs/cell; raise `target_n` in `spec.json`
and re-run `sweep next | … | judge` to fill the deficit.

## Reproduce

```bash
cd natuurkunde
../venv/bin/python eval.py sweep status 20260617-gemma4-temp   # coverage
../venv/bin/python eval.py sweep report 20260617-gemma4-temp   # this table
```

## Provenance

- Spec: [`spec.json`](spec.json) — registered in `eval.db` (`sweeps` table).
- Exact solve commands: [`logs/solve_cmds.txt`](logs/solve_cmds.txt) (0.5/0.7/1.0),
  [`logs/solve_cmds_extend.txt`](logs/solve_cmds_extend.txt) (0.0/0.3).
- Solve/judge logs: [`logs/`](logs/).
- DB backups: `eval.db.bak-pre-20260617-gemma4-temp` (initial),
  `eval.db.bak-pre-20260617-gemma4-temp-extend` (before adding 0.0/0.3).
- Runs in `eval.db`: ids 60–74. Judge: `openai/gpt-5.4` (reasoning medium), run_number 1.

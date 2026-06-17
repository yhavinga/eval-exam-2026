---
name: Sweep Runner
description: >-
  Design, run, monitor, and analyze LLM benchmark parameter sweeps (grids over
  temperature, model, provider, quantization, reasoning effort) with the
  project's `eval.py sweep` runner. Use when the user wants to define a sweep,
  check coverage / which configs are under-sampled, fill missing runs (solve +
  judge), or view per-cell score reports. Trigger phrases: "sweep", "parameter
  sweep", "grid", "define/run/status/report a sweep", "how many runs for ...",
  "compare temperatures/providers/models".
argument-hint: "[define|status|next|run|report] [sweep-name or what you want]"
---

# Sweep Runner

Orchestrate parameter sweeps for the VWO physics-exam benchmark: a sweep is a
declarative grid of solve configs; this skill drives its whole lifecycle —
**define → status → next → run → report** — through `eval.py sweep`.

## Mental model

A run is uniquely identified by its full config tuple, so that tuple *is* a grid
cell and the `runs` table *is* the observation store. A sweep just declares which
cells it wants (`axes` to vary × every other dimension `fixed`) and a per-cell
replication target. "Which configs need more runs" is then a deficit query, and
existing runs count toward any cell they match — no re-running what you already
have.

## Environment — always run commands this way

`eval.py` and `eval.db` live in `natuurkunde/`; all paths inside are relative, so
the working directory must be that folder. The Python venv is at the repo root.

```bash
cd /Users/yeb/Developer/yhavinga/eval-exam-2026/natuurkunde
../venv/bin/python eval.py sweep <subcommand> ...
```

`../venv/bin/python` needs no activation. `genai`/`openrouter` runs need internet
and the API keys in `natuurkunde/.env`.

## The spec file (JSON)

A sweep is authored as a JSON spec. Copy [spec-template.json](spec-template.json),
edit it, and save it (e.g. `/tmp/<name>.json`). Fields:

- `name` — unique slug for the sweep.
- `goal` — the hypothesis, one line (e.g. "Does temperature change gemma accuracy?").
- `target_n` — complete runs wanted per cell (≈15–20 to resolve a ~2-pt gap).
- `axes` — dimensions to vary; each maps to a list. The cross-product makes the cells.
- `fixed` — every dimension NOT in `axes`, pinned to one value. Pinning all of
  them is mandatory: `define` refuses a spec that leaves a required dimension
  unset, because an unpinned dimension is a silent confound.
- `exclude` *(optional)* — list of partial-match objects to drop invalid combos,
  e.g. `[{"inference_stack": "genai", "presence_penalty": 1.5}]`.
- `judge` — `{judge_model, judge_stack, reasoning_effort, judge_count}` used to
  score every cell (one judge, so judge variance never confounds the comparison).

**Required solve dimensions** (each must appear in `axes` or `fixed`): `model`,
`inference_stack`, `base_url`, `temperature`, `top_p`, `top_k`, `max_tokens`,
`reasoning_effort`. **Optional / nullable**: `presence_penalty`, `provider`,
`quantization` (the last two are OpenRouter routing).

Reference values:
- `inference_stack` → `base_url`: `genai` → `https://generativelanguage.googleapis.com/v1`;
  `openrouter` → `https://openrouter.ai/api/v1`; `lmstudio` → `http://192.168.2.97:1234/v1`.
- `reasoning_effort`: `off` | `low` | `medium` | `high` | `xhigh`. Reasoning ON is
  roughly 4× the wall-clock of OFF.
- Recommended judge: `openai/gpt-5.4`, reasoning `medium` — the most accurate judge
  measured (zero clear errors on the disputed set). `google/gemini-3.5-flash`
  (reasoning `low`) is cheaper but grades slightly lenient — read its absolute %
  as a soft ceiling.

## Lifecycle — do these in order

1. **Author the spec.** Write a JSON file from the template; pin every non-swept
   dimension.
2. **Check the grid (no writes):**
   `../venv/bin/python eval.py sweep define --spec-file <f> --dry-run`
   Shows the cells, total runs, and coverage against existing runs. Always do
   this before registering.
3. **Register:** `../venv/bin/python eval.py sweep define --spec-file <f>`
4. **Coverage:** `../venv/bin/python eval.py sweep status <name>` — reps / target /
   deficit per cell; under-sampled cells are flagged.
5. **Preview the runs (no API, no writes):**
   `../venv/bin/python eval.py sweep next <name> --dry-run`
   Emits the solve/judge commands with `--dry-run` appended, so piping to `sh`
   previews create-vs-resume for the whole grid without spending anything.
6. **Run it** — see "Running the grid" below.
7. **Watch:** rerun `sweep status <name>` until deficits reach 0.
8. **Report:** `../venv/bin/python eval.py sweep report <name>` — per-cell n,
   mean%, sd, 95% CI (scored by the spec's judge). Overlapping CIs mean the cells
   are not distinguishable at this n; widen `target_n` and run more.

## Running the grid (this spends money — gate it)

`sweep next <name>` prints the `solve` + `judge` commands with the next free run
numbers. To execute:

- Sequential: `../venv/bin/python eval.py sweep next <name> | sh`
- Parallel (faster): split the `solve` lines across several background shells.
  SQLite's busy-timeout makes concurrent writes safe, and `run_number` + the
  dedup key prevent duplicate runs. Run each cell's `judge` line after that
  cell's solves finish.

**Safety — every time, without exception:**

- Before launching, show the user the plan: the cells, the per-cell deficit, the
  total number of runs, the judge, and a rough cost/time estimate (remember
  reasoning ON ≈ 4× wall-clock). Get an explicit go-ahead before running anything
  that calls a paid API.
- Dry-run first: `sweep next --dry-run`, and/or a sample `solve --dry-run`, to
  confirm each command is CREATE vs RESUME as intended.
- Only run what `sweep next` emits — never hand-craft or alter configs.
- If a run is interrupted (lost wifi, killed), just re-run the same `solve`
  command: it resumes from where it stopped with full image context.
- After judging, scan the output for `IMPORTANT Qx,.. are reported to have
  missing images`. Those answers never received an image; re-solve them rather
  than trusting the low score.

## Per-command dry runs (credential-free, no DB writes)

- `eval.py solve ... --dry-run` → reports CREATE vs RESUME vs already-complete.
- `eval.py judge ... --dry-run` → reports how many answer×run pairs would be graded.

## Inspecting results directly

- `../venv/bin/python eval.py runs` — every run with answer/judge counts and score.
- Cross matrix of any answer model × judge model:
  ```sql
  SELECT a.model, j.judge_model,
         ROUND(100.0 * SUM(j.score) / SUM(j.max_score), 1) AS pct
  FROM answers a JOIN judgements j ON j.answer_id = a.id
  WHERE j.score IS NOT NULL
  GROUP BY a.model, j.judge_model;
  ```
  Run with `sqlite3 eval.db "<query>"` from `natuurkunde/`.

## Worked example (temperature sweep)

```bash
cd /Users/yeb/Developer/yhavinga/eval-exam-2026/natuurkunde
# 1-2. author /tmp/gemma-temp.json from the template, then check the grid
../venv/bin/python eval.py sweep define --spec-file /tmp/gemma-temp.json --dry-run
# 3-4. register and inspect coverage
../venv/bin/python eval.py sweep define --spec-file /tmp/gemma-temp.json
../venv/bin/python eval.py sweep status gemma-temp
# 5. preview every run with no API calls
../venv/bin/python eval.py sweep next gemma-temp --dry-run | sh
# 6. (after showing the plan and getting the go-ahead) run it
../venv/bin/python eval.py sweep next gemma-temp | sh
# 7-8. watch, then report
../venv/bin/python eval.py sweep status gemma-temp
../venv/bin/python eval.py sweep report gemma-temp
```

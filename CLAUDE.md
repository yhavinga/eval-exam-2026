# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VWO (Dutch pre-university) physics exam evaluation system using local LLMs via LMStudio. The system scans exam images, generates answers using vision-capable LLMs, and evaluates them against official correctievoorschriften (answer keys).

## Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Scan exam images and generate metadata
python eval.py scan [exam_path]

# Sync metadata to SQLite database
python eval.py sync [exam_path]

# Generate answers (requires model loaded in LMStudio)
python eval.py solve --model "qwen/qwen3.6-35b-a3b" --temperature 1.0

# Judge answers against correctievoorschrift
python eval.py judge --judge-model "qwen/qwen3.6-35b-a3b" --temperature 1.0
```

## LMStudio API

The system connects to LMStudio at `http://192.168.2.97:1234/v1` (OpenAI-compatible API).

```bash
# List available models (OpenAI-compatible)
curl http://192.168.2.97:1234/v1/models

# Check model details and state (shows loaded/not-loaded)
curl http://192.168.2.97:1234/api/v0/models

# Load a model
curl -X POST http://192.168.2.97:1234/api/v1/models/load \
  -H "Content-Type: application/json" \
  -d '{"model": "google/gemma-4-31b"}'
# Returns: {"instance_id": "google/gemma-4-31b", "status": "loaded", ...}

# Unload a model (use instance_id from load response, usually same as model id)
curl -X POST http://192.168.2.97:1234/api/v1/models/unload \
  -H "Content-Type: application/json" \
  -d '{"instance_id": "google/gemma-4-31b"}'
```

See [LMStudio REST API docs](https://lmstudio.ai/docs/developer/rest/load) for more options.

## Architecture

### Data Flow
1. **scan** → Reads `images/{year}/{exam_code}/` for PNGs, creates `metadata.jsonl`
2. **sync** → Loads `metadata.jsonl` into SQLite `questions` table
3. **solve** → Sends images to LLM, stores responses in `answers` table
4. **judge** → Compares answers against CV images, stores scores in `judgements` table

### Database Schema (schema.sql)
- `questions`: exam metadata, image paths, CV paths
- `answers`: model responses with generation parameters
- `judgements`: scores with judge model and motivation

### Image Naming Convention
```
{nr}_{topic}[_suffix].png         # Question images
{nr}_{topic}_cv.png               # Correctievoorschrift
{nr}_{topic}_cv_aanvullend.png    # Supplementary CV
```

Example: `01_botsproef_opgave.png`, `01_botsproef_cv.png`

### Directory Structure
```
images/{year}/{exam_code}/        # Question images
images/{year}/{exam_code}/cv/     # Correctievoorschrift images
images/{year}/{exam_code}/metadata.jsonl
analyse/                          # Analysis reports
```

## Model Configuration

**Reasoning models** (Qwen, Gemma-4) require `temperature=1.0` to avoid infinite loops. They return `reasoning_content` separately from `content`.

**Non-reasoning models** (Gemma-3) use standard `content` field only.

Key parameters for solve:
- `--temperature 1.0` (required for reasoning models)
- `--max-tokens 32768` or higher
- `--top-k 64` (for Gemma)
- `--presence-penalty` not needed for Gemma

## Cross-Validation Matrix

The system supports cross-validation: multiple answer models judged by multiple judge models. Query results with:

```sql
SELECT a.model, j.judge_model, ROUND(100.0 * SUM(j.score) / SUM(j.max_score), 1) as pct
FROM answers a JOIN judgements j ON j.answer_id = a.id
WHERE j.score IS NOT NULL
GROUP BY a.model, j.judge_model;
```

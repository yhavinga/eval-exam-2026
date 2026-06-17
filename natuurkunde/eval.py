#!/usr/bin/env python3
"""VWO Exam Evaluation Runner.

Usage:
    python eval.py scan [exam_path]   - Scan filesystem, generate metadata.jsonl
    python eval.py sync [exam_path]   - Sync metadata.jsonl to SQLite
    python eval.py solve              - Generate answers for all questions
    python eval.py judge              - Judge all answers
    python eval.py runs               - List runs with scores
    python eval.py sweep              - Define/track parameter sweeps
"""

import argparse
import asyncio
import base64
import itertools
import json
import os
import re
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from openai import OpenAI

load_dotenv()

DB_PATH = Path("eval.db")
SCHEMA_PATH = Path("schema.sql")
IMAGES_BASE = Path("images")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LMSTUDIO_BASE_URL = "http://192.168.2.97:1234/v1"
GENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1"


def get_api_key(base_url: str) -> str:
    """Get API key based on provider."""
    if base_url == "genai":
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY not set in .env")
        return key
    if "openrouter" in base_url:
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("OPENROUTER_API_KEY not set in .env")
        return key
    return "not-needed"


# Naming convention: {nr}_{name}[_suffix].png
# Examples: 01_botsproef.png, 02_botsproef_opgave.png, 03_botsproef_figuur_3.png
# CV examples: 01_botsproef_cv.png, 01_botsproef_cv_aanvullend.png
QUESTION_PATTERN = re.compile(r"^(\d+)_([a-z0-9_-]+?)(?:_(opgave|uitwerkbijlage|figuur_\d+|cv|cv_aanvullend|\d+))?\.png$", re.IGNORECASE)


def init_db() -> sqlite3.Connection:
    """Initialize database with schema."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()
    return conn


def load_image_as_base64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def parse_filename(filename: str) -> dict | None:
    """Parse question filename into components."""
    match = QUESTION_PATTERN.match(filename)
    if not match:
        return None
    return {
        "number": match.group(1),
        "name": match.group(2),
        "suffix": match.group(3),  # None, "opgave", "uitwerkbijlage", or a number
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def scan_exam_folder(exam_path: Path) -> list[dict]:
    """Scan exam folder and group files into questions."""
    questions = defaultdict(lambda: {"images": [], "cv": []})

    # Scan main folder for question images
    for f in sorted(exam_path.glob("*.png")):
        parsed = parse_filename(f.name)
        if parsed:
            key = f"{parsed['number']}_{parsed['name']}"
            questions[key]["images"].append(f.name)
            questions[key]["number"] = parsed["number"]
            questions[key]["name"] = parsed["name"]

    # Scan cv/ folder for correctievoorschriften
    cv_folder = exam_path / "cv"
    if cv_folder.exists():
        for f in sorted(cv_folder.glob("*.png")):
            parsed = parse_filename(f.name)
            if parsed:
                key = f"{parsed['number']}_{parsed['name']}"
                if key in questions:
                    questions[key]["cv"].append(f"cv/{f.name}")

    # Convert to list and sort by question number
    def sort_images(images: list[str]) -> list[str]:
        """Sort images: opgave first, then others alphabetically."""
        def key(name):
            if "_opgave" in name.lower():
                return (0, name)
            if "_uitwerkbijlage" in name.lower():
                return (2, name)
            return (1, name)
        return sorted(images, key=key)

    result = []
    for key, q in sorted(questions.items(), key=lambda x: x[1]["number"]):
        result.append({
            "question": q["number"],
            "name": q["name"],
            "images": sort_images(q["images"]),
            "cv": sorted(q["cv"]),
            "max_punten": None,
            "prompt": "Los dit op"
        })

    return result


def cmd_scan(args):
    """Scan filesystem and generate/update metadata.jsonl."""
    exam_paths = list(IMAGES_BASE.glob("*/*/")) if not args.exam_path else [Path(args.exam_path)]

    for exam_path in exam_paths:
        if not exam_path.is_dir():
            continue

        metadata_file = exam_path / "metadata.jsonl"
        existing = {}

        # Load existing metadata to preserve manual edits (max_punten, prompt)
        if metadata_file.exists():
            with open(metadata_file) as f:
                for line in f:
                    if line.strip():
                        q = json.loads(line)
                        existing[q["question"]] = q

        # Scan filesystem
        questions = scan_exam_folder(exam_path)

        # Merge: keep manual edits from existing
        for q in questions:
            if q["question"] in existing:
                old = existing[q["question"]]
                q["max_punten"] = old.get("max_punten")
                q["prompt"] = old.get("prompt", "Los dit op")

        # Write metadata.jsonl
        with open(metadata_file, "w") as f:
            for q in questions:
                f.write(json.dumps(q, ensure_ascii=False) + "\n")

        print(f"Scanned {exam_path}: {len(questions)} questions")
        for q in questions:
            cv_status = "✓ cv" if q["cv"] else "✗ no cv"
            pts = f"{q['max_punten']}pt" if q["max_punten"] else "?pt"
            print(f"  {q['question']} {q['name']}: {len(q['images'])} img, {cv_status}, {pts}")


def cmd_sync(args):
    """Sync metadata.jsonl to SQLite database."""
    conn = init_db()
    exam_paths = list(IMAGES_BASE.glob("*/*/")) if not args.exam_path else [Path(args.exam_path)]

    total = 0
    for exam_path in exam_paths:
        metadata_file = exam_path / "metadata.jsonl"
        if not metadata_file.exists():
            print(f"No metadata.jsonl in {exam_path}, run 'scan' first")
            continue

        # Extract exam_code from path: images/2026-05/vw-1023-a-26-1-o -> vw-1023-a-26-1-o
        exam_code = exam_path.name
        rel_path = exam_path.relative_to(IMAGES_BASE)

        with open(metadata_file) as f:
            for line in f:
                if not line.strip():
                    continue
                q = json.loads(line)

                # Build full paths relative to IMAGES_BASE
                image_paths = [str(rel_path / img) for img in q["images"]]
                cv_paths = [str(rel_path / cv) for cv in q["cv"]] if q["cv"] else None

                cur = conn.execute("""
                    INSERT INTO questions (exam_code, question_number, question_name, image_paths, correctievoorschrift_paths, max_punten, prompt)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(exam_code, question_number) DO UPDATE SET
                        question_name = excluded.question_name,
                        image_paths = excluded.image_paths,
                        correctievoorschrift_paths = excluded.correctievoorschrift_paths,
                        max_punten = excluded.max_punten,
                        prompt = excluded.prompt
                    RETURNING id
                """, (exam_code, q["question"], q["name"], json.dumps(image_paths),
                      json.dumps(cv_paths) if cv_paths else None,
                      q.get("max_punten"), q.get("prompt", "Los dit op")))
                cur.fetchone()
                conn.commit()
                total += 1

    print(f"Synced {total} questions to {DB_PATH}")
    conn.close()


def cmd_solve(args):
    """Generate answers for all questions, grouped by topic."""
    conn = init_db()

    # log_model: name for database, defaults to API model name if not specified
    log_model = args.log_model or args.model

    # Resolve stack/base_url first; defer client creation so --dry-run needs no
    # credentials (it inspects the DB and exits without ever calling the API).
    is_genai = args.stack == "genai"
    if is_genai:
        stack = "genai"
        base_url = GENAI_BASE_URL
    else:
        stack = "openrouter" if "openrouter" in args.base_url else args.stack
        base_url = args.base_url

    genai_client = client = None
    if not args.dry_run:
        if is_genai:
            genai_client = genai.Client(api_key=get_api_key("genai"))
        else:
            client = OpenAI(base_url=args.base_url, api_key=get_api_key(args.base_url), timeout=3600.0)

    reasoning_effort = args.reasoning_effort
    run_number = args.solve_run_number

    # Check for existing run with same config
    question_count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    existing_run = conn.execute("""
        SELECT r.id, r.run_name,
               COUNT(a.id) as total,
               COUNT(CASE WHEN a.response IS NOT NULL AND a.error IS NULL THEN 1 END) as ok
        FROM runs r
        LEFT JOIN answers a ON a.run_id = r.id
        WHERE r.model = ? AND r.inference_stack = ? AND r.base_url = ?
          AND r.temperature = ? AND r.top_p = ? AND r.top_k = ?
          AND r.presence_penalty IS ? AND r.max_tokens = ? AND r.reasoning_effort = ?
          AND r.provider IS ? AND r.quantization IS ?
          AND r.run_number = ?
        GROUP BY r.id
    """, (log_model, stack, base_url, args.temperature, args.top_p,
          args.top_k, args.presence_penalty, args.max_tokens, reasoning_effort,
          args.provider, args.quantization, run_number)).fetchone()

    if args.dry_run:
        route = f"{(args.provider or '-')}-{(args.quantization or '-')}"
        if existing_run and existing_run["ok"] >= question_count:
            print(f"[dry-run] run {existing_run['id']} already complete "
                  f"({existing_run['ok']}/{question_count}); --force would re-run it.")
        elif existing_run and not args.force:
            print(f"[dry-run] RESUME run {existing_run['id']}: {existing_run['run_name']} "
                  f"({existing_run['ok']}/{question_count} done) — would solve the remaining "
                  f"{question_count - existing_run['ok']} question(s).")
        else:
            print(f"[dry-run] CREATE new run: {log_model} / {stack} / {route} / "
                  f"t={args.temperature} / reasoning={reasoning_effort} / #{run_number} — "
                  f"would solve {question_count} question(s).")
        print("[dry-run] no API calls, no database writes.")
        conn.close()
        return

    if existing_run and not args.force:
        if existing_run["ok"] >= question_count:
            print(f"Run {existing_run['id']} already complete ({existing_run['ok']}/{question_count} ok). Use --force to re-run.")
            conn.close()
            return
        # Resume incomplete run
        run_id = existing_run["id"]
        run_name = existing_run["run_name"]
        print(f"Resuming run {run_id}: {run_name} ({existing_run['ok']}/{question_count} ok)")
    else:
        created_at = now_iso()
        cur = conn.execute("""
            INSERT INTO runs (created_at, model, inference_stack, base_url, temperature, top_p, top_k,
                              presence_penalty, max_tokens, reasoning_effort, run_number, notes,
                              provider, quantization)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id, run_name
        """, (created_at, log_model, stack, base_url, args.temperature, args.top_p,
              args.top_k, args.presence_penalty, args.max_tokens, reasoning_effort, run_number, args.notes,
              args.provider, args.quantization))
        row = cur.fetchone()
        run_id = row["id"]
        run_name = row["run_name"]
        conn.commit()
        print(f"Created run {run_id}: {run_name}")

    # Group questions by (exam_code, question_name) = topic
    questions = conn.execute("""
        SELECT * FROM questions ORDER BY exam_code, question_name, question_number
    """).fetchall()

    topics = defaultdict(list)
    for q in questions:
        topic_key = (q["exam_code"], q["question_name"])
        topics[topic_key].append(q)

    # Sort topics by minimum question number (numeric order)
    sorted_topics = sorted(
        topics.items(),
        key=lambda x: min(int(q["question_number"]) for q in x[1])
    )

    print(f"Solving {len(questions)} questions in {len(topics)} topics...")

    for (exam_code, topic_name), topic_questions in sorted_topics:
        print(f"\n=== Topic: {exam_code} / {topic_name} ({len(topic_questions)} questions) ===")

        # Fresh conversation for each topic
        if is_genai:
            contents = []
        else:
            messages = []

        for q in topic_questions:
            # Check if already successfully answered in this run
            existing = conn.execute(
                "SELECT id, response FROM answers WHERE run_id = ? AND question_id = ?",
                (run_id, q["id"])
            ).fetchone()

            if existing and existing["response"] is not None:
                print(f"  Q{q['question_number']}: already answered, adding to context")
                # Reconstruct the full user turn (images + prompt) identical to a fresh
                # solve, so resumed runs carry the same visual context forward to later
                # questions as an uninterrupted run would.
                image_paths = json.loads(q["image_paths"])
                prompt = q["prompt"]
                if is_genai:
                    parts = []
                    for img_path in image_paths:
                        parts.append(types.Part.from_bytes(
                            data=(IMAGES_BASE / img_path).read_bytes(), mime_type="image/png"
                        ))
                    parts.append(types.Part.from_text(text=f"Vraag {q['question_number']}: {prompt}"))
                    contents.append(types.Content(role="user", parts=parts))
                    contents.append(types.Content(role="model", parts=[
                        types.Part.from_text(text=existing["response"])
                    ]))
                else:
                    content = []
                    for img_path in image_paths:
                        img_data = load_image_as_base64(IMAGES_BASE / img_path)
                        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}})
                    content.append({"type": "text", "text": f"Vraag {q['question_number']}: {prompt}"})
                    messages.append({"role": "user", "content": content})
                    messages.append({"role": "assistant", "content": existing["response"]})
                continue

            if existing:
                conn.execute("DELETE FROM answers WHERE id = ?", (existing["id"],))
                conn.commit()

            print(f"  Q{q['question_number']}: solving...", end=" ", flush=True)

            image_paths = json.loads(q["image_paths"])
            prompt = q["prompt"]
            start = time.perf_counter()
            response = None
            reasoning = None
            error = None

            if is_genai:
                parts = []
                for img_path in image_paths:
                    parts.append(types.Part.from_bytes(
                        data=(IMAGES_BASE / img_path).read_bytes(), mime_type="image/png"
                    ))
                parts.append(types.Part.from_text(text=f"Vraag {q['question_number']}: {prompt}"))
                contents.append(types.Content(role="user", parts=parts))

                genai_levels = {"off": "minimal", "low": "low", "medium": "medium",
                                "high": "high", "on": "high", "xhigh": "high"}
                level = genai_levels.get(reasoning_effort, "high")
                if "gemma" in args.model.lower():
                    # Gemma only supports minimal (off) vs default (on)
                    thinking_cfg = types.ThinkingConfig(
                        thinking_level="minimal" if reasoning_effort == "off" else None,
                        include_thoughts=reasoning_effort != "off",
                    )
                else:
                    thinking_cfg = types.ThinkingConfig(
                        thinking_level=level, include_thoughts=True,
                    )
                config = types.GenerateContentConfig(
                    thinking_config=thinking_cfg,
                    max_output_tokens=args.max_tokens,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    top_k=args.top_k,
                )

                for attempt in range(5):
                    try:
                        resp = genai_client.models.generate_content(
                            model=args.model, contents=contents, config=config
                        )
                        response = resp.text
                        thinking_parts = []
                        if resp.candidates and resp.candidates[0].content:
                            for part in resp.candidates[0].content.parts:
                                if getattr(part, 'thought', False) and part.text:
                                    thinking_parts.append(part.text)
                        reasoning = "\n".join(thinking_parts) if thinking_parts else None
                        error = None
                        break
                    except Exception as e:
                        error = str(e)
                        if "429" in error or "RESOURCE_EXHAUSTED" in error:
                            wait = 5 * (attempt + 1)
                            print(f"RATE LIMITED, waiting {wait}s...", end=" ", flush=True)
                            time.sleep(wait)
                            continue
                        break

                duration_ms = int((time.perf_counter() - start) * 1000)
                contents.append(types.Content(role="model", parts=[
                    types.Part.from_text(text=response or "[error]")
                ]))
            else:
                content = []
                for img_path in image_paths:
                    img_data = load_image_as_base64(IMAGES_BASE / img_path)
                    content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}})
                content.append({"type": "text", "text": f"Vraag {q['question_number']}: {prompt}"})
                messages.append({"role": "user", "content": content})

                extra_body = {"top_k": args.top_k}
                if args.presence_penalty is not None:
                    extra_body["presence_penalty"] = args.presence_penalty
                if "openrouter" in base_url:
                    or_effort = {"off": "none", "low": "low", "medium": "medium", "high": "high", "xhigh": "xhigh"}.get(reasoning_effort, "high")
                    extra_body["reasoning"] = {"effort": or_effort}
                    if args.provider:
                        extra_body["provider"] = {"order": [args.provider], "allow_fallbacks": False}
                    if args.quantization:
                        extra_body.setdefault("provider", {})["quantizations"] = [args.quantization]
                        extra_body["provider"]["allow_fallbacks"] = False
                elif "8030" in base_url or "vllm" in base_url.lower():
                    extra_body["chat_template_kwargs"] = {"enable_thinking": reasoning_effort != "off"}
                    extra_body["skip_special_tokens"] = False

                for attempt in range(2):
                    try:
                        resp = client.chat.completions.create(
                            model=args.model,
                            messages=messages,
                            max_tokens=args.max_tokens,
                            temperature=args.temperature,
                            top_p=args.top_p,
                            extra_body=extra_body
                        )
                        msg = resp.choices[0].message
                        response = msg.content
                        reasoning = getattr(msg, 'reasoning', None) or getattr(msg, 'reasoning_content', None)
                        error = None
                        break
                    except Exception as e:
                        error = str(e)
                        if attempt == 0 and "parse" in error.lower():
                            print("RETRY...", end=" ", flush=True)
                            continue
                        response = None
                        reasoning = None

                duration_ms = int((time.perf_counter() - start) * 1000)
                messages.append({"role": "assistant", "content": response or "[error]"})

            # Save to DB
            cur = conn.execute("""
                INSERT INTO answers (run_id, question_id, created_at, response, reasoning, duration_ms, error)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            """, (run_id, q["id"], now_iso(), response, reasoning, duration_ms, error))
            cur.fetchone()
            conn.commit()

            if error:
                print(f"ERROR: {error}")
            else:
                ctx_len = len(contents) if is_genai else len(messages)
                print(f"done ({duration_ms}ms, ctx={ctx_len} msgs)")

    conn.close()


def parse_run_numbers(s: str) -> list[int]:
    """Parse '1,2,3' or '1..7' or '1..3,5,7' into sorted list of ints."""
    result = set()
    for part in s.split(","):
        part = part.strip()
        if ".." in part:
            start, end = part.split("..", 1)
            result.update(range(int(start), int(end) + 1))
        else:
            result.add(int(part))
    return sorted(result)


def cmd_judge(args):
    """Judge answers asynchronously across a grid of solve runs × judge counts."""
    import judge_async

    judge_stack = "openrouter" if "openrouter" in args.judge_base_url else args.judge_stack
    solve_run_numbers = parse_run_numbers(args.solve_runs)

    solve_reasoning = args.solve_reasoning or args.reasoning_effort

    asyncio.run(judge_async.run(
        judge_model=args.judge_model,
        judge_base_url=args.judge_base_url,
        judge_stack=judge_stack,
        temperature=args.temperature,
        reasoning_effort=args.reasoning_effort,
        answer_model=args.answer_model,
        solve_run_numbers=solve_run_numbers,
        solve_reasoning=solve_reasoning,
        judge_count=args.judge_count,
        concurrency=args.concurrency,
        force=args.force,
        provider=getattr(args, 'provider', None),
        quantization=getattr(args, 'quantization', None),
        dry_run=args.dry_run,
    ))


# --- Parameter sweeps --------------------------------------------------------
#
# A sweep is a declarative grid. Its `spec` names which dimensions to vary
# (`axes`, cross-producted) and pins every other solve dimension (`fixed`), so
# each resulting cell is a fully-specified config that can be matched exactly
# against the runs table. The runs table is the observation store; coverage is a
# deficit query, and existing runs count automatically toward any cell they fit.

# Every solve dimension. The required ones must be set by an axis or `fixed`;
# the optional ones (nullable in the schema) default to None when neither does.
SOLVE_DIMS = ["model", "inference_stack", "base_url", "temperature", "top_p",
              "top_k", "presence_penalty", "max_tokens", "reasoning_effort",
              "provider", "quantization"]
REQUIRED_DIMS = ["model", "inference_stack", "base_url", "temperature", "top_p",
                 "top_k", "max_tokens", "reasoning_effort"]

# A cell is matched against a run by its full config tuple. NULL-safe `IS` so the
# optional dims (presence_penalty/provider/quantization) match unset against unset.
CELL_MATCH_SQL = """
        r.model IS ? AND r.inference_stack IS ? AND r.base_url IS ?
          AND r.temperature IS ? AND r.top_p IS ? AND r.top_k IS ?
          AND r.presence_penalty IS ? AND r.max_tokens IS ? AND r.reasoning_effort IS ?
          AND r.provider IS ? AND r.quantization IS ?"""


def cell_params(cell: dict) -> tuple:
    return tuple(cell[d] for d in SOLVE_DIMS)


def expand_cells(spec: dict) -> list[dict]:
    """Cross-product the swept axes with the fixed values, dropping exclusions.

    Each cell pins all SOLVE_DIMS (optional ones default to None) so coverage can
    be matched exactly with no hidden confounds. An exclusion is a partial-match
    object: a cell is dropped if it equals the rule on every key the rule names.
    """
    axes = spec.get("axes", {})
    fixed = spec.get("fixed", {})
    exclude = spec.get("exclude", [])
    axis_names = list(axes.keys())

    cells = []
    for combo in itertools.product(*(axes[a] for a in axis_names)):
        cell = dict(fixed)
        cell.update(dict(zip(axis_names, combo)))
        if any(all(cell.get(k) == v for k, v in rule.items()) for rule in exclude):
            continue
        for dim in SOLVE_DIMS:
            cell.setdefault(dim, None)
        cells.append(cell)
    return cells


def cell_complete_runs(conn, cell: dict) -> int:
    """Count runs matching a cell's exact config tuple that answered every
    question without error (a 'complete' replication)."""
    row = conn.execute(f"""
        SELECT COUNT(DISTINCT r.id) AS complete
        FROM runs r
        CROSS JOIN (SELECT COUNT(*) AS qcount FROM questions) q
        JOIN (
            SELECT run_id, COUNT(*) AS ok_count
            FROM answers WHERE response IS NOT NULL AND error IS NULL
            GROUP BY run_id
        ) ok ON ok.run_id = r.id AND ok.ok_count >= q.qcount
        WHERE {CELL_MATCH_SQL}
    """, cell_params(cell)).fetchone()
    return row["complete"]


def cell_max_run_number(conn, cell: dict) -> int:
    """Highest run_number already used for this exact cell (0 if none), so new
    replications get the next free numbers."""
    row = conn.execute(f"""
        SELECT COALESCE(MAX(r.run_number), 0) AS m FROM runs r
        WHERE {CELL_MATCH_SQL}
    """, cell_params(cell)).fetchone()
    return row["m"]


# t_{0.975} by degrees of freedom for small-sample 95% CIs; approaches 1.96 for large n.
_T95 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31,
        9: 2.26, 10: 2.23, 12: 2.18, 15: 2.13, 20: 2.09, 30: 2.04, 60: 2.00}


def mean_sd_ci(values: list[float]):
    """Mean, sample sd, and 95% CI bounds. CI is None for n<2 (undefined)."""
    import statistics
    n = len(values)
    mean = statistics.fmean(values)
    if n < 2:
        return mean, None, None, None
    sd = statistics.stdev(values)
    df = n - 1
    t = _T95.get(df) or next((_T95[k] for k in sorted(_T95) if k >= df), 1.96)
    half = t * sd / (n ** 0.5)
    return mean, sd, mean - half, mean + half


def cell_run_scores(conn, cell: dict, judge_model: str, judge_reasoning: str) -> list[float]:
    """Per-run score% for complete runs in this cell, scored by the designated
    judge's first pass (run_number=1), counting only fully-judged runs."""
    qcount = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    rows = conn.execute(f"""
        SELECT r.id AS run_id,
               100.0 * SUM(j.score) / NULLIF(SUM(j.max_score), 0) AS pct,
               COUNT(j.id) AS judged
        FROM runs r
        JOIN answers a ON a.run_id = r.id AND a.response IS NOT NULL AND a.error IS NULL
        JOIN judgements j ON j.answer_id = a.id
             AND j.judge_model = ? AND j.reasoning_effort = ? AND j.run_number = 1
             AND j.score IS NOT NULL
        WHERE {CELL_MATCH_SQL}
        GROUP BY r.id
        HAVING judged >= ?
    """, (judge_model, judge_reasoning) + cell_params(cell) + (qcount,)).fetchall()
    return [row["pct"] for row in rows]


def cell_label(spec: dict, cell: dict) -> str:
    """Short label of just the swept axes — what actually varies between cells."""
    axes = spec.get("axes", {})
    if not axes:
        return "(single cell)"
    return " ".join(f"{a}={cell[a]}" for a in axes)


def solve_command(cell: dict, run_number: int, dry_run: bool = False) -> str:
    parts = ["python eval.py solve",
             f"--model {cell['model']}",
             f"--stack {cell['inference_stack']}",
             f"--base-url {cell['base_url']}",
             f"--temperature {cell['temperature']}",
             f"--top-p {cell['top_p']}",
             f"--top-k {cell['top_k']}",
             f"--max-tokens {cell['max_tokens']}",
             f"--reasoning-effort {cell['reasoning_effort']}"]
    if cell.get("presence_penalty") is not None:
        parts.append(f"--presence-penalty {cell['presence_penalty']}")
    if cell.get("provider") is not None:
        parts.append(f"--provider {cell['provider']}")
    if cell.get("quantization") is not None:
        parts.append(f"--quantization {cell['quantization']}")
    parts.append(f"--solve-run-number {run_number}")
    if dry_run:
        parts.append("--dry-run")
    return " ".join(parts)


def judge_command(cell: dict, judge: dict, run_numbers: list[int], dry_run: bool = False) -> str:
    # The judge filter keys on (answer-model, solve-runs, solve-reasoning) and is
    # provider-agnostic, so this grades every matching answer once regardless of
    # provider — which is what we want; duplicate invocations are idempotent.
    runs = ",".join(str(n) for n in run_numbers)
    parts = ["python eval.py judge",
             f"--judge-model {judge['judge_model']}",
             f"--judge-stack {judge.get('judge_stack', 'openrouter')}",
             f"--judge-base-url {judge.get('judge_base_url', OPENROUTER_BASE_URL)}",
             f"--reasoning-effort {judge.get('reasoning_effort', 'medium')}",
             f"--answer-model {cell['model']}",
             f"--solve-runs {runs}",
             f"--solve-reasoning {cell['reasoning_effort']}",
             f"--judge-count {judge.get('judge_count', 1)}"]
    if dry_run:
        parts.append("--dry-run")
    return " ".join(parts)


def load_spec(path: str) -> dict:
    """Read and validate a sweep spec, failing loudly on an unpinned dimension so
    no confound slips in unspecified."""
    with open(path) as f:
        spec = json.load(f)
    for key in ("name", "goal", "target_n"):
        if key not in spec:
            raise SystemExit(f"Spec is missing required field: {key}")
    axes, fixed = spec.get("axes", {}), spec.get("fixed", {})
    missing = [d for d in REQUIRED_DIMS if d not in axes and d not in fixed]
    if missing:
        raise SystemExit(
            f"Spec does not pin required dimension(s): {', '.join(missing)}. "
            f"Every non-swept dimension must appear in `fixed`.")
    return spec


def get_sweep(conn, name: str):
    row = conn.execute("SELECT * FROM sweeps WHERE name = ?", (name,)).fetchone()
    if not row:
        raise SystemExit(f"No sweep named '{name}'. Define it with `sweep define` first.")
    return row, json.loads(row["spec"])


def print_coverage(conn, spec: dict, cells: list[dict]) -> int:
    """Print the per-cell reps/target/deficit table; return total runs still needed."""
    target = spec["target_n"]
    print(f"{'cell':<44} {'reps':>5} {'target':>6} {'deficit':>7}")
    print("-" * 66)
    total_deficit = 0
    for cell in cells:
        complete = cell_complete_runs(conn, cell)
        deficit = max(0, target - complete)
        total_deficit += deficit
        flag = "  <-- under-sampled" if deficit else ""
        print(f"{cell_label(spec, cell):<44} {complete:>5} {target:>6} {deficit:>7}{flag}")
    print("-" * 66)
    print(f"Total complete runs still needed: {total_deficit}")
    return total_deficit


def cmd_sweep(args):
    """Define and track parameter sweeps (define / status / next)."""
    conn = init_db()
    if args.sweep_command == "define":
        spec = load_spec(args.spec_file)
        cells = expand_cells(spec)
        total = len(cells) * spec["target_n"]
        if args.dry_run:
            print(f"[dry-run] sweep '{spec['name']}': {len(cells)} cells x target "
                  f"{spec['target_n']} = {total} complete runs.\nCoverage against existing runs:\n")
            print_coverage(conn, spec, cells)
            print("\n[dry-run] nothing written — run without --dry-run to register.")
            conn.close()
            return
        if conn.execute("SELECT 1 FROM sweeps WHERE name = ?", (spec["name"],)).fetchone():
            raise SystemExit(f"Sweep '{spec['name']}' already exists. Pick a new name first.")
        conn.execute("""
            INSERT INTO sweeps (created_at, name, goal, spec, status)
            VALUES (?, ?, ?, ?, 'open')
        """, (now_iso(), spec["name"], spec["goal"], json.dumps(spec)))
        conn.commit()
        print(f"Defined sweep '{spec['name']}': {len(cells)} cells x "
              f"target {spec['target_n']} = {total} complete runs.")

    elif args.sweep_command == "status":
        row, spec = get_sweep(conn, args.name)
        cells = expand_cells(spec)
        print(f"Sweep '{spec['name']}' [{row['status']}] — {spec['goal']}")
        print(f"{len(cells)} cells, target {spec['target_n']} complete runs each\n")
        print_coverage(conn, spec, cells)

    elif args.sweep_command == "next":
        row, spec = get_sweep(conn, args.name)
        cells = expand_cells(spec)
        target = spec["target_n"]
        judge = spec.get("judge")
        any_needed = False
        for cell in cells:
            deficit = max(0, target - cell_complete_runs(conn, cell))
            if not deficit:
                continue
            any_needed = True
            start = cell_max_run_number(conn, cell) + 1
            new_numbers = list(range(start, start + deficit))
            print(f"# {cell_label(spec, cell)}  (need {deficit})")
            for rn in new_numbers:
                print("  " + solve_command(cell, rn, dry_run=args.dry_run))
            if judge:
                print("  " + judge_command(cell, judge, new_numbers, dry_run=args.dry_run))
            print()
        if not any_needed:
            print("All cells meet target. Nothing to run.")

    elif args.sweep_command == "report":
        row, spec = get_sweep(conn, args.name)
        cells = expand_cells(spec)
        judge = spec.get("judge") or {}
        jm = judge.get("judge_model")
        jr = judge.get("reasoning_effort", "medium")
        if not jm:
            raise SystemExit("Sweep spec has no `judge`; cannot report scores.")
        print(f"Sweep '{spec['name']}' — scored by {jm} (reasoning={jr})")
        print(f"{'cell':<40} {'n':>3} {'mean%':>7} {'sd':>6} {'95% CI':>16}")
        print("-" * 76)
        for cell in cells:
            scores = cell_run_scores(conn, cell, jm, jr)
            if not scores:
                print(f"{cell_label(spec, cell):<40} {0:>3} {'-':>7} {'-':>6} {'-':>16}")
                continue
            mean, sd, lo, hi = mean_sd_ci(scores)
            ci = f"[{lo:.1f}, {hi:.1f}]" if lo is not None else "(n<2)"
            sd_s = f"{sd:.2f}" if sd is not None else "-"
            print(f"{cell_label(spec, cell):<40} {len(scores):>3} {mean:>7.1f} {sd_s:>6} {ci:>16}")
        print("-" * 76)
        print("Cells with overlapping CIs are not distinguishable at this n; widen "
              "target_n to resolve small gaps (~15-20 runs for a ~2-pt difference).")

    conn.close()


def cmd_runs(args):
    """List all runs with answer counts and scores."""
    conn = init_db()

    runs = conn.execute("""
        SELECT r.id, r.run_name, r.model, r.inference_stack, r.reasoning_effort,
               r.temperature, r.run_number, r.created_at, r.notes,
               COUNT(DISTINCT a.id) as answer_count,
               COUNT(DISTINCT CASE WHEN a.response IS NOT NULL AND a.error IS NULL THEN a.id END) as success_count,
               ROUND(100.0 * SUM(CASE WHEN j.score IS NOT NULL THEN j.score ELSE 0 END) /
                     NULLIF(SUM(CASE WHEN j.max_score IS NOT NULL THEN j.max_score ELSE 0 END), 0), 1) as score_pct,
               COUNT(DISTINCT j.id) as judgement_count
        FROM runs r
        LEFT JOIN answers a ON a.run_id = r.id
        LEFT JOIN judgements j ON j.answer_id = a.id
        GROUP BY r.id
        ORDER BY r.created_at
    """).fetchall()

    if not runs:
        print("No runs found.")
        conn.close()
        return

    print(f"{'ID':>3}  {'Run Name':<55} {'Answers':>7} {'Judged':>7} {'Score':>6}  Notes")
    print("-" * 100)
    for r in runs:
        score_str = f"{r['score_pct']}%" if r['score_pct'] is not None else "-"
        notes_str = r['notes'] or ""
        print(f"{r['id']:>3}  {r['run_name']:<55} {r['answer_count']:>3}/{r['success_count']:>3} "
              f"{r['judgement_count']:>5}  {score_str:>6}  {notes_str}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="VWO Exam Evaluation Runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan command
    p_scan = subparsers.add_parser("scan", help="Scan filesystem, generate metadata.jsonl")
    p_scan.add_argument("exam_path", nargs="?", help="Specific exam folder to scan")
    p_scan.set_defaults(func=cmd_scan)

    # sync command
    p_sync = subparsers.add_parser("sync", help="Sync metadata.jsonl to SQLite")
    p_sync.add_argument("exam_path", nargs="?", help="Specific exam folder to sync")
    p_sync.set_defaults(func=cmd_sync)

    # solve command
    p_solve = subparsers.add_parser("solve", help="Generate answers for questions")
    p_solve.add_argument("--model", default="qwen3.5-27b", help="Model name (sent to API)")
    p_solve.add_argument("--log-model", help="Model name in database (if different from --model)")
    p_solve.add_argument("--base-url", default="http://192.168.2.97:1234/v1", help="API base URL")
    p_solve.add_argument("--stack", default="lmstudio", help="Inference stack name")
    p_solve.add_argument("--temperature", type=float, default=1.0, help="Temperature (1.0 for Qwen thinking)")
    p_solve.add_argument("--top-p", type=float, default=0.95, help="Top-p sampling")
    p_solve.add_argument("--top-k", type=int, default=20, help="Top-k sampling")
    p_solve.add_argument("--presence-penalty", type=float, default=None, help="Presence penalty (only sent to the API when passed)")
    p_solve.add_argument("--max-tokens", type=int, default=65536, help="Max tokens for response")
    p_solve.add_argument("--reasoning-effort", default="on", help='Reasoning effort: "off", "low", "medium", "high", "xhigh"')
    p_solve.add_argument("--solve-run-number", type=int, required=True, help="Solve run number (explicit, for parallel runs)")
    p_solve.add_argument("--provider", help="OpenRouter provider slug (e.g. novita)")
    p_solve.add_argument("--quantization", help="OpenRouter quantization filter (e.g. bf16, fp8, int8)")
    p_solve.add_argument("--notes", help="Optional notes for this run")
    p_solve.add_argument("--force", action="store_true", help="Create a new run even if one exists")
    p_solve.add_argument("--dry-run", action="store_true", help="Report create-vs-resume and exit; no API calls or DB writes")
    p_solve.set_defaults(func=cmd_solve)

    # judge command
    p_judge = subparsers.add_parser("judge", help="Judge answers")
    p_judge.add_argument("--judge-model", default="qwen3.5-27b", help="Judge model to use")
    p_judge.add_argument("--judge-base-url", default="http://192.168.2.97:1234/v1", help="Judge API base URL")
    p_judge.add_argument("--judge-stack", default="lmstudio", help="Judge inference stack")
    p_judge.add_argument("--temperature", type=float, default=1.0, help="Temperature for judge")
    p_judge.add_argument("--reasoning-effort", default="on", help='Reasoning effort: "off", "low", "medium", "high", "xhigh"')
    p_judge.add_argument("--answer-model", required=True, help="Answer model to judge (e.g. google/gemma-4-31b-it)")
    p_judge.add_argument("--solve-runs", required=True, help="Solve run numbers to judge (e.g. 1,2,3 or 1..7)")
    p_judge.add_argument("--solve-reasoning", help="Reasoning effort of solve runs to filter on (defaults to --reasoning-effort)")
    p_judge.add_argument("--judge-count", type=int, required=True, help="Number of times to judge each answer (creates judge run_numbers 1..N)")
    p_judge.add_argument("--concurrency", type=int, default=20, help="Max concurrent API calls")
    p_judge.add_argument("--provider", help="OpenRouter provider slug (e.g. novita)")
    p_judge.add_argument("--quantization", help="OpenRouter quantization filter (e.g. bf16, fp8, int8)")
    p_judge.add_argument("--force", action="store_true", help="Re-judge already judged answers")
    p_judge.add_argument("--dry-run", action="store_true", help="Report how many answers would be judged and exit; no API calls or DB writes")
    p_judge.set_defaults(func=cmd_judge)

    # sweep command (parameter sweeps)
    p_sweep = subparsers.add_parser("sweep", help="Define and track parameter sweeps")
    sweep_sub = p_sweep.add_subparsers(dest="sweep_command", required=True)
    p_sweep_define = sweep_sub.add_parser("define", help="Define a sweep from a JSON spec file")
    p_sweep_define.add_argument("--spec-file", required=True, help="Path to the sweep spec JSON")
    p_sweep_define.add_argument("--dry-run", action="store_true", help="Preview cells and coverage without registering the sweep")
    p_sweep_define.set_defaults(func=cmd_sweep)
    p_sweep_status = sweep_sub.add_parser("status", help="Show per-cell run coverage and deficits")
    p_sweep_status.add_argument("name", help="Sweep name")
    p_sweep_status.set_defaults(func=cmd_sweep)
    p_sweep_next = sweep_sub.add_parser("next", help="Emit solve/judge commands to fill under-sampled cells")
    p_sweep_next.add_argument("name", help="Sweep name")
    p_sweep_next.add_argument("--dry-run", action="store_true", help="Append --dry-run to every emitted command (preview the whole grid)")
    p_sweep_next.set_defaults(func=cmd_sweep)
    p_sweep_report = sweep_sub.add_parser("report", help="Per-cell score: n, mean%, sd, 95% CI (scored by the spec's judge)")
    p_sweep_report.add_argument("name", help="Sweep name")
    p_sweep_report.set_defaults(func=cmd_sweep)

    # runs command
    p_runs = subparsers.add_parser("runs", help="List runs with scores")
    p_runs.set_defaults(func=cmd_runs)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

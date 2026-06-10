#!/usr/bin/env python3
"""VWO Exam Evaluation Runner.

Usage:
    python eval.py scan [exam_path]   - Scan filesystem, generate metadata.jsonl
    python eval.py sync [exam_path]   - Sync metadata.jsonl to SQLite
    python eval.py solve              - Generate answers for all questions
    python eval.py judge              - Judge all answers
    python eval.py runs               - List runs with scores
"""

import argparse
import asyncio
import base64
import json
import os
import re
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DB_PATH = Path("eval.db")
SCHEMA_PATH = Path("schema.sql")
IMAGES_BASE = Path("images")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LMSTUDIO_BASE_URL = "http://192.168.2.97:1234/v1"


def get_api_key(base_url: str) -> str:
    """Get API key based on provider."""
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
    client = OpenAI(base_url=args.base_url, api_key=get_api_key(args.base_url), timeout=3600.0)

    # log_model: name for database, defaults to API model name if not specified
    log_model = args.log_model or args.model

    # Auto-detect inference stack from base_url
    stack = "openrouter" if "openrouter" in args.base_url else args.stack

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
          AND r.presence_penalty = ? AND r.max_tokens = ? AND r.reasoning_effort = ?
          AND r.run_number = ?
        GROUP BY r.id
    """, (log_model, stack, args.base_url, args.temperature, args.top_p,
          args.top_k, args.presence_penalty, args.max_tokens, reasoning_effort, run_number)).fetchone()

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
                              presence_penalty, max_tokens, reasoning_effort, run_number, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id, run_name
        """, (created_at, log_model, stack, args.base_url, args.temperature, args.top_p,
              args.top_k, args.presence_penalty, args.max_tokens, reasoning_effort, run_number, args.notes))
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
        messages = []

        for q in topic_questions:
            # Check if already successfully answered in this run
            existing = conn.execute(
                "SELECT id, response FROM answers WHERE run_id = ? AND question_id = ?",
                (run_id, q["id"])
            ).fetchone()

            if existing and existing["response"] is not None:
                print(f"  Q{q['question_number']}: already answered, adding to context")
                messages.append({"role": "user", "content": [
                    {"type": "text", "text": f"[Vraag {q['question_number']} was al beantwoord]"}
                ]})
                messages.append({"role": "assistant", "content": existing["response"]})
                continue

            if existing:
                conn.execute("DELETE FROM answers WHERE id = ?", (existing["id"],))
                conn.commit()

            print(f"  Q{q['question_number']}: solving...", end=" ", flush=True)

            # Build user message with images for this question
            image_paths = json.loads(q["image_paths"])
            prompt = q["prompt"]

            content = []
            for img_path in image_paths:
                img_data = load_image_as_base64(IMAGES_BASE / img_path)
                content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}})
            content.append({"type": "text", "text": f"Vraag {q['question_number']}: {prompt}"})

            messages.append({"role": "user", "content": content})

            # Call API with full conversation context (retry once on parse errors)
            start = time.perf_counter()
            response = None
            reasoning = None
            error = None

            # Build extra_body
            extra_body = {
                "top_k": args.top_k,
                "presence_penalty": args.presence_penalty
            }
            if "openrouter" in args.base_url:
                or_effort = {"off": "none", "low": "low", "medium": "medium", "high": "high", "xhigh": "xhigh"}.get(reasoning_effort, "high")
                extra_body["reasoning"] = {"effort": or_effort}
                if args.provider:
                    extra_body["provider"] = {"order": [args.provider], "allow_fallbacks": False}
                if args.quantization:
                    extra_body.setdefault("provider", {})["quantizations"] = [args.quantization]
                    extra_body["provider"]["allow_fallbacks"] = False
            elif "8030" in args.base_url or "vllm" in args.base_url.lower():
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
                    # Extract reasoning if present (vLLM: 'reasoning', LMStudio: 'reasoning_content')
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

            # Add assistant response to conversation for context
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
                print(f"done ({duration_ms}ms, ctx={len(messages)} msgs)")

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
    ))


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
    p_solve.add_argument("--presence-penalty", type=float, default=1.5, help="Presence penalty (shortens thinking)")
    p_solve.add_argument("--max-tokens", type=int, default=65536, help="Max tokens for response")
    p_solve.add_argument("--reasoning-effort", default="on", help='Reasoning effort: "off", "low", "medium", "high", "xhigh"')
    p_solve.add_argument("--solve-run-number", type=int, required=True, help="Solve run number (explicit, for parallel runs)")
    p_solve.add_argument("--provider", help="OpenRouter provider slug (e.g. novita)")
    p_solve.add_argument("--quantization", help="OpenRouter quantization filter (e.g. bf16, fp8, int8)")
    p_solve.add_argument("--notes", help="Optional notes for this run")
    p_solve.add_argument("--force", action="store_true", help="Create a new run even if one exists")
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
    p_judge.set_defaults(func=cmd_judge)

    # runs command
    p_runs = subparsers.add_parser("runs", help="List runs with scores")
    p_runs.set_defaults(func=cmd_runs)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""VWO Exam Evaluation Runner.

Usage:
    python eval.py scan [exam_path]   - Scan filesystem, generate metadata.jsonl
    python eval.py sync [exam_path]   - Sync metadata.jsonl to SQLite
    python eval.py solve              - Generate answers for all questions
    python eval.py judge              - Judge all answers
"""

import argparse
import base64
import json
import re
import sqlite3
import time
from collections import defaultdict
from pathlib import Path
from openai import OpenAI

DB_PATH = Path("eval.db")
SCHEMA_PATH = Path("schema.sql")
IMAGES_BASE = Path("images")

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
    client = OpenAI(base_url=args.base_url, api_key="not-needed", timeout=3600.0)

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

    print(f"Solving {len(questions)} questions in {len(topics)} topics with {args.model}...")

    for (exam_code, topic_name), topic_questions in sorted_topics:
        print(f"\n=== Topic: {exam_code} / {topic_name} ({len(topic_questions)} questions) ===")

        # Fresh conversation for each topic
        messages = []

        for q in topic_questions:
            # Check if already answered with this model
            existing = conn.execute(
                "SELECT id, response FROM answers WHERE question_id = ? AND model = ?",
                (q["id"], args.model)
            ).fetchone()

            if existing and not args.force:
                print(f"  Q{q['question_number']}: already answered, adding to context")
                # Add to context for subsequent questions
                messages.append({"role": "user", "content": [
                    {"type": "text", "text": f"[Vraag {q['question_number']} was al beantwoord]"}
                ]})
                messages.append({"role": "assistant", "content": existing["response"] or "[geen antwoord]"})
                continue

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
            for attempt in range(2):
                try:
                    resp = client.chat.completions.create(
                        model=args.model,
                        messages=messages,
                        max_tokens=args.max_tokens,
                        temperature=args.temperature,
                        top_p=args.top_p,
                        extra_body={
                            "top_k": args.top_k,
                            "presence_penalty": args.presence_penalty
                        }
                    )
                    msg = resp.choices[0].message
                    response = msg.content
                    # Extract reasoning_content if present (Qwen/Gemma thinking mode)
                    reasoning = getattr(msg, 'reasoning_content', None)
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

            # Add assistant response to conversation for context (only content, not reasoning for KV cache efficiency)
            messages.append({"role": "assistant", "content": response or "[error]"})

            # Save to DB (both response and reasoning)
            cur = conn.execute("""
                INSERT INTO answers (question_id, model, inference_stack, base_url, temperature, top_p, top_k, presence_penalty, max_tokens, response, reasoning, duration_ms, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            """, (q["id"], args.model, args.stack, args.base_url, args.temperature, args.top_p, args.top_k, args.presence_penalty, args.max_tokens, response, reasoning, duration_ms, error))
            cur.fetchone()
            conn.commit()

            if error:
                print(f"ERROR: {error}")
            else:
                print(f"done ({duration_ms}ms, ctx={len(messages)} msgs)")

    conn.close()


def cmd_judge(args):
    """Judge all answers."""
    conn = init_db()

    # Get answers that haven't been judged yet (or all if --force)
    if args.force:
        answers = conn.execute("""
            SELECT a.*, q.exam_code, q.question_number
            FROM answers a JOIN questions q ON a.question_id = q.id
        """).fetchall()
    else:
        answers = conn.execute("""
            SELECT a.*, q.exam_code, q.question_number
            FROM answers a
            JOIN questions q ON a.question_id = q.id
            WHERE a.id NOT IN (SELECT answer_id FROM judgements WHERE judge_model = ?)
        """, (args.judge_model,)).fetchall()

    print(f"Judging {len(answers)} answers with {args.judge_model}...")

    for a in answers:
        print(f"  {a['exam_code']} Q{a['question_number']} (answer {a['id']}): judging...", end=" ", flush=True)
        try:
            judgement_id = judge_answer(conn, a["id"], args.judge_model, args.judge_base_url, args.judge_stack, args.temperature)
            j = conn.execute("SELECT score, max_score, duration_ms FROM judgements WHERE id = ?", (judgement_id,)).fetchone()
            print(f"{j['score']}/{j['max_score']} ({j['duration_ms']}ms)")
        except ValueError as e:
            print(f"SKIP: {e}")

    conn.close()


def solve_question(
    conn: sqlite3.Connection,
    question_id: int,
    model: str,
    base_url: str,
    inference_stack: str = "lmstudio",
    temperature: float = 0.0,
    max_tokens: int = 65536
) -> int:
    """Generate answer for a question, returns answer id."""
    client = OpenAI(base_url=base_url, api_key="not-needed", timeout=3600.0)

    q = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
    image_paths = json.loads(q["image_paths"])
    prompt = q["prompt"]

    # Build messages - multi-turn for multiple images
    if len(image_paths) == 1:
        img_data = load_image_as_base64(IMAGES_BASE / image_paths[0])
        messages = [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}},
            {"type": "text", "text": prompt}
        ]}]
    else:
        messages = []
        for i, img_path in enumerate(image_paths):
            img_data = load_image_as_base64(IMAGES_BASE / img_path)
            if i == 0:
                messages.append({"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}},
                    {"type": "text", "text": "Dit is de opgave."}
                ]})
                messages.append({"role": "assistant", "content": "Begrepen, ik zie de opgave."})
            elif i == len(image_paths) - 1:
                messages.append({"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}},
                    {"type": "text", "text": f"Hier is aanvullende informatie. {prompt}"}
                ]})
            else:
                messages.append({"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}},
                    {"type": "text", "text": "Hier is aanvullende informatie."}
                ]})
                messages.append({"role": "assistant", "content": "Begrepen."})

    start = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        response = resp.choices[0].message.content
        error = None
    except Exception as e:
        response = None
        error = str(e)
    duration_ms = int((time.perf_counter() - start) * 1000)

    cur = conn.execute("""
        INSERT INTO answers (question_id, model, inference_stack, base_url, temperature, max_tokens, response, duration_ms, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        RETURNING id
    """, (question_id, model, inference_stack, base_url, temperature, max_tokens, response, duration_ms, error))
    result = cur.fetchone()[0]
    conn.commit()
    return result


def judge_answer(
    conn: sqlite3.Connection,
    answer_id: int,
    judge_model: str,
    judge_base_url: str,
    judge_stack: str = "openai",
    temperature: float = 1.0
) -> int:
    """Judge an answer using correctievoorschrift, returns judgement id."""
    answer = conn.execute("SELECT * FROM answers WHERE id = ?", (answer_id,)).fetchone()
    question = conn.execute("SELECT * FROM questions WHERE id = ?", (answer["question_id"],)).fetchone()

    cv_paths = json.loads(question["correctievoorschrift_paths"]) if question["correctievoorschrift_paths"] else []
    if not cv_paths:
        raise ValueError(f"No correctievoorschrift for question {question['id']}")

    question_images = json.loads(question["image_paths"])
    max_punten = question["max_punten"] or 0

    client = OpenAI(base_url=judge_base_url, api_key="not-needed", timeout=3600.0)

    content = []
    for img_path in question_images:
        img_data = load_image_as_base64(IMAGES_BASE / img_path)
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}})

    for cv_path in cv_paths:
        img_data = load_image_as_base64(IMAGES_BASE / cv_path)
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}})

    content.append({"type": "text", "text": f"""Je bent een examinator voor VWO natuurkunde.

OPGAVE: Zie de eerste afbeelding(en).

CORRECTIEVOORSCHRIFT: Zie de laatste afbeelding(en). Het maximum aantal punten staat in het correctievoorschrift.

ANTWOORD VAN LEERLING:
{answer["response"]}

OPDRACHT:
Beoordeel het antwoord volgens het correctievoorschrift.

Geef je beoordeling in dit formaat (motivatie EERST, dan scores):
MOTIVATIE: [uitleg waarom deze score]
[SCORE=getal]
[MAX=getal]"""})

    start = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=judge_model,
            messages=[{"role": "user", "content": content}],
            max_tokens=65536,
            temperature=temperature
        )
        motivation = resp.choices[0].message.content
        score = None
        max_score = None
        if motivation:
            # Parse SCORE and MAX in various formats: [SCORE=3], SCORE=3, SCORE: 3
            score_match = re.search(r'\[?SCORE[=:]\s*(\d+(?:\.\d+)?)\]?', motivation)
            max_match = re.search(r'\[?MAX[=:]\s*(\d+(?:\.\d+)?)\]?', motivation)
            if score_match:
                score = float(score_match.group(1))
            if max_match:
                max_score = float(max_match.group(1))
        error = None
    except Exception as e:
        motivation = None
        score = None
        max_score = None
        error = str(e)
    duration_ms = int((time.perf_counter() - start) * 1000)

    cur = conn.execute("""
        INSERT INTO judgements (answer_id, judge_model, judge_stack, score, max_score, motivation, duration_ms, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        RETURNING id
    """, (answer_id, judge_model, judge_stack, score, max_score, motivation, duration_ms, error))
    result = cur.fetchone()[0]
    conn.commit()
    return result


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
    p_solve.add_argument("--model", default="qwen3.5-27b", help="Model to use")
    p_solve.add_argument("--base-url", default="http://192.168.2.97:1234/v1", help="API base URL")
    p_solve.add_argument("--stack", default="lmstudio", help="Inference stack name")
    p_solve.add_argument("--temperature", type=float, default=1.0, help="Temperature (1.0 for Qwen thinking)")
    p_solve.add_argument("--top-p", type=float, default=0.95, help="Top-p sampling")
    p_solve.add_argument("--top-k", type=int, default=20, help="Top-k sampling")
    p_solve.add_argument("--presence-penalty", type=float, default=1.5, help="Presence penalty (shortens thinking)")
    p_solve.add_argument("--max-tokens", type=int, default=65536, help="Max tokens for response")
    p_solve.add_argument("--force", action="store_true", help="Re-solve already answered questions")
    p_solve.set_defaults(func=cmd_solve)

    # judge command
    p_judge = subparsers.add_parser("judge", help="Judge answers")
    p_judge.add_argument("--judge-model", default="qwen3.5-27b", help="Judge model to use")
    p_judge.add_argument("--judge-base-url", default="http://192.168.2.97:1234/v1", help="Judge API base URL")
    p_judge.add_argument("--judge-stack", default="lmstudio", help="Judge inference stack")
    p_judge.add_argument("--temperature", type=float, default=1.0, help="Temperature for judge (1.0 for Qwen reasoning)")
    p_judge.add_argument("--force", action="store_true", help="Re-judge already judged answers")
    p_judge.set_defaults(func=cmd_judge)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

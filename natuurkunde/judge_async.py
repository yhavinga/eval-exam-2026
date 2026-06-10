"""Async grid judging engine for VWO exam evaluation."""

import asyncio
import json
import re
import time

from openai import AsyncOpenAI

from eval import IMAGES_BASE, get_api_key, init_db, load_image_as_base64, now_iso

JUDGE_PROMPT_TEMPLATE = """Je bent een examinator voor VWO natuurkunde.

OPGAVE: Zie de eerste afbeelding(en).

CORRECTIEVOORSCHRIFT: Zie de laatste afbeelding(en). Het maximum aantal punten staat in het correctievoorschrift.

ANTWOORD VAN LEERLING:
{response}

OPDRACHT:
Beoordeel het antwoord volgens het correctievoorschrift.

Geef je beoordeling in dit formaat (motivatie EERST, dan scores):
MOTIVATIE: [uitleg waarom deze score]
[SCORE=getal]
[MAX=getal]"""


def _build_extra_body(base_url: str, reasoning_effort: str,
                      provider: str | None = None, quantization: str | None = None) -> dict:
    extra_body = {}
    if "openrouter" in base_url:
        or_effort = {"off": "none", "low": "low", "medium": "medium", "high": "high", "xhigh": "xhigh"}.get(reasoning_effort, "high")
        extra_body["reasoning"] = {"effort": or_effort}
        if provider:
            extra_body["provider"] = {"order": [provider], "allow_fallbacks": False}
        if quantization:
            extra_body.setdefault("provider", {})["quantizations"] = [quantization]
            extra_body["provider"]["allow_fallbacks"] = False
    elif "8030" in base_url or "vllm" in base_url.lower():
        extra_body["chat_template_kwargs"] = {"enable_thinking": reasoning_effort != "off"}
        extra_body["skip_special_tokens"] = False
    return extra_body


def _parse_score(motivation: str | None) -> tuple[float | None, float | None]:
    if not motivation:
        return None, None
    score_match = re.search(r'\[?SCORE[=:]\s*(\d+(?:\.\d+)?)\]?', motivation)
    max_match = re.search(r'\[?MAX[=:]\s*(\d+(?:\.\d+)?)\]?', motivation)
    score = float(score_match.group(1)) if score_match else None
    max_score = float(max_match.group(1)) if max_match else None
    return score, max_score


async def _judge_one(
    client: AsyncOpenAI,
    semaphore: asyncio.Semaphore,
    db_lock: asyncio.Lock,
    conn,
    answer_id: int,
    content: list,
    judge_model: str,
    judge_stack: str,
    temperature: float,
    reasoning_effort: str,
    run_number: int,
    extra_body: dict,
    progress: dict,
):
    async with semaphore:
        start = time.perf_counter()
        try:
            resp = await client.chat.completions.create(
                model=judge_model,
                messages=[{"role": "user", "content": content}],
                max_tokens=16384,
                temperature=temperature,
                extra_body=extra_body or None,
            )
            motivation = resp.choices[0].message.content
            score, max_score = _parse_score(motivation)
            error = None
        except Exception as e:
            motivation = None
            score = None
            max_score = None
            error = str(e)
        duration_ms = int((time.perf_counter() - start) * 1000)

    async with db_lock:
        conn.execute("""
            DELETE FROM judgements
            WHERE answer_id = ? AND judge_model = ? AND judge_stack = ? AND temperature = ?
              AND reasoning_effort = ? AND run_number = ?
        """, (answer_id, judge_model, judge_stack, temperature, reasoning_effort, run_number))

        conn.execute("""
            INSERT INTO judgements (answer_id, created_at, judge_model, judge_stack, temperature,
                                    reasoning_effort, run_number, score, max_score, motivation, duration_ms, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (answer_id, now_iso(), judge_model, judge_stack, temperature,
              reasoning_effort, run_number, score, max_score, motivation, duration_ms, error))
        conn.commit()

        progress["done"] += 1
        if error:
            progress["errors"] += 1
        elif score is None:
            progress["no_score"] += 1
        total = progress["total"]
        done = progress["done"]
        errors = progress["errors"]
        no_score = progress["no_score"]
        pct = int(100 * done / total) if total else 0
        parts = []
        if errors:
            parts.append(f"{errors} errors")
        if no_score:
            parts.append(f"{no_score} unparsed")
        extra = f", {', '.join(parts)}" if parts else ""
        print(f"\r  {done}/{total} scored ({pct}%){extra}    ", end="", flush=True)


async def run(
    judge_model: str,
    judge_base_url: str,
    judge_stack: str,
    temperature: float,
    reasoning_effort: str,
    answer_model: str,
    solve_run_numbers: list[int],
    solve_reasoning: str,
    judge_count: int,
    concurrency: int,
    force: bool,
    provider: str | None = None,
    quantization: str | None = None,
):
    conn = init_db()
    client = AsyncOpenAI(
        base_url=judge_base_url,
        api_key=get_api_key(judge_base_url),
        timeout=3600.0,
    )
    extra_body = _build_extra_body(judge_base_url, reasoning_effort, provider, quantization)

    # Validate solve runs exist for this model + reasoning effort
    placeholders = ",".join("?" * len(solve_run_numbers))
    existing_runs = conn.execute(
        f"SELECT run_number FROM runs WHERE model = ? AND reasoning_effort = ? AND run_number IN ({placeholders})",
        [answer_model, solve_reasoning] + solve_run_numbers
    ).fetchall()
    existing_nums = {r["run_number"] for r in existing_runs}
    missing = set(solve_run_numbers) - existing_nums
    if missing:
        print(f"Error: no runs found for model '{answer_model}' (reasoning={solve_reasoning}) with run_numbers: {sorted(missing)}")
        conn.close()
        return

    # Get successful answers for specified model + reasoning + run_numbers
    answers = conn.execute(f"""
        SELECT a.id, a.response,
               q.image_paths, q.correctievoorschrift_paths, q.exam_code, q.question_number
        FROM answers a
        JOIN questions q ON a.question_id = q.id
        JOIN runs r ON a.run_id = r.id
        WHERE r.model = ? AND r.reasoning_effort = ? AND r.run_number IN ({placeholders})
          AND a.response IS NOT NULL AND a.error IS NULL
    """, [answer_model, solve_reasoning] + solve_run_numbers).fetchall()

    if not answers:
        print("No successful answers found for the specified solve runs.")
        conn.close()
        return

    # Pre-cache images as data URLs (deduplicated by path)
    image_cache = {}
    for a in answers:
        for path in json.loads(a["image_paths"]):
            if path not in image_cache:
                image_cache[path] = f"data:image/png;base64,{load_image_as_base64(IMAGES_BASE / path)}"
        cv_raw = a["correctievoorschrift_paths"]
        if cv_raw:
            for path in json.loads(cv_raw):
                if path not in image_cache:
                    image_cache[path] = f"data:image/png;base64,{load_image_as_base64(IMAGES_BASE / path)}"

    # Pre-build message content per answer (shared across judge_numbers)
    answer_content = {}
    skipped_no_cv = 0
    for a in answers:
        cv_raw = a["correctievoorschrift_paths"]
        cv_paths = json.loads(cv_raw) if cv_raw else []
        if not cv_paths:
            skipped_no_cv += 1
            continue

        content = []
        for path in json.loads(a["image_paths"]):
            content.append({"type": "image_url", "image_url": {"url": image_cache[path]}})
        for path in cv_paths:
            content.append({"type": "image_url", "image_url": {"url": image_cache[path]}})
        content.append({"type": "text", "text": JUDGE_PROMPT_TEMPLATE.format(response=a["response"])})
        answer_content[a["id"]] = content

    if skipped_no_cv:
        print(f"Skipped {skipped_no_cv} answers without correctievoorschrift.")

    # Build task list: (answer_id, judge_number) pairs
    tasks = []
    for a in answers:
        if a["id"] not in answer_content:
            continue
        for judge_num in range(1, judge_count + 1):
            if not force:
                existing = conn.execute("""
                    SELECT id FROM judgements
                    WHERE answer_id = ? AND judge_model = ? AND judge_stack = ? AND temperature = ?
                      AND reasoning_effort = ? AND run_number = ? AND score IS NOT NULL
                """, (a["id"], judge_model, judge_stack, temperature, reasoning_effort, judge_num)).fetchone()
                if existing:
                    continue
            tasks.append((a["id"], judge_num))

    if not tasks:
        print("All answers already judged. Use --force to re-judge.")
        conn.close()
        return

    print(f"Judging {len(tasks)} answer×run pairs with {judge_model} (concurrency={concurrency})...")

    progress = {"done": 0, "errors": 0, "no_score": 0, "total": len(tasks)}
    semaphore = asyncio.Semaphore(concurrency)
    db_lock = asyncio.Lock()

    async_tasks = [
        _judge_one(
            client, semaphore, db_lock, conn,
            answer_id, answer_content[answer_id],
            judge_model, judge_stack, temperature, reasoning_effort, judge_num,
            extra_body, progress,
        )
        for answer_id, judge_num in tasks
    ]

    await asyncio.gather(*async_tasks)
    print()

    errors = progress["errors"]
    no_score = progress["no_score"]
    ok = progress["done"] - errors - no_score
    parts = [f"{ok} scored"]
    if no_score:
        parts.append(f"{no_score} unparsed")
    if errors:
        parts.append(f"{errors} errors")
    print(f"Done: {', '.join(parts)}.")

    conn.close()

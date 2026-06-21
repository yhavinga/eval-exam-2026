"""Async grid judging engine for VWO exam evaluation."""

import asyncio
import json
import re
import time

from google import genai
from google.genai import types
from openai import AsyncOpenAI

from eval import IMAGES_BASE, get_api_key, init_db, load_image_as_base64, now_iso

JUDGE_PROMPT_TEMPLATE = """Je bent een examinator voor VWO natuurkunde.

OPGAVE: Zie de eerste afbeelding(en).

CORRECTIEVOORSCHRIFT: Zie de laatste afbeelding(en). Het maximum aantal punten staat in het correctievoorschrift.

ANTWOORD VAN LEERLING:
{response}

OPDRACHT:
Beoordeel het antwoord volgens het correctievoorschrift.

BEOORDELINGSREGELS (pas toe bovenop het beoordelingsmodel):
- Scorepunten zijn gehele getallen van 0 t/m het maximum; geen halve of negatieve punten.
- Volledig juist -> maximum; gedeeltelijk juist -> deelscore volgens het beoordelingsmodel.
- Een vakinhoudelijk aantoonbaar juist antwoord dat niet letterlijk in het model staat (bv. een wiskundig GELIJKWAARDIGE methode) krijgt punten naar analogie / in de geest van het model -- reken een gelijkwaardige correcte methode dus NIET fout.
- Mogelijkheden gescheiden door "/" zijn gelijkwaardige formuleringen; tekst tussen haakjes hoeft de leerling niet te noemen.
- Een ontbrekende of foutieve gevraagde uitleg/afleiding/berekening -> 0 punten voor dat onderdeel, tenzij het model anders aangeeft.
- Eenzelfde fout wordt binnen een vraag maar een keer aangerekend (consequent doorrekenen met een al afgestrafte fout geeft geen extra aftrek), tenzij de vraag daardoor sterk vereenvoudigt.
- 'Gebruik van een formule'-scorepunt: toekennen als de juiste formule is gebruikt met minstens een juist ingevulde grootheid (bij afleiding/redenering: formule genoteerd EN een relevante bewerking/redeneerstap).
- 'Completeren van de berekening/bepaling'-scorepunt: NIET toekennen bij een rekenfout, verkeerd gecombineerde elementen, ontbrekende/onpassende eenheid, of een uitkomst alleen als orde van grootte -- dus ook niet als de einduitkomst hierdoor afwijkt van de vereiste uitkomst.
- Significantie alleen beoordelen als er expliciet naar significante cijfers wordt gevraagd of de juistheid van een gegeven waarde moet worden aangetoond.

Let op: soms kon de leerling de vraag niet maken doordat een benodigde afbeelding of
figuur niet is meegestuurd. Signalen hiervoor zijn: het antwoord zegt expliciet dat er
geen afbeelding/figuur is ontvangen of zichtbaar was (bijvoorbeeld "ik heb geen
afbeelding ontvangen" of "ik heb de figuur bij vraag X nodig"), OF het antwoord is
opvallend kort/leeg en mist juist de gegevens die alleen uit de figuur te halen zijn.
Een kort maar inhoudelijk correct antwoord is GEEN ontbrekende afbeelding. Beoordeel de
score bij een ontbrekende afbeelding nog steeds volgens het correctievoorschrift
(meestal 0) en zet [MISSING_IMAGE=ja]. In alle andere gevallen [MISSING_IMAGE=nee].

Geef je beoordeling in dit formaat (motivatie EERST, dan scores):
MOTIVATIE: [uitleg waarom deze score]
[SCORE=getal]
[MAX=getal]
[MISSING_IMAGE=ja of nee]"""


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
    elif "z.ai" in base_url:
        # z.ai (GLM) takes OpenAI-style reasoning_effort as a top-level field; the
        # vision GLM (glm-4.5v) needs a reasoning control present or it returns an
        # empty completion. Passed through verbatim so an unsupported value fails loud.
        extra_body["reasoning_effort"] = reasoning_effort
    return extra_body


def _parse_score(motivation: str | None) -> tuple[float | None, float | None]:
    if not motivation:
        return None, None
    score_match = re.search(r'\[?SCORE[=:]\s*(\d+(?:\.\d+)?)\]?', motivation)
    max_match = re.search(r'\[?MAX[=:]\s*(\d+(?:\.\d+)?)\]?', motivation)
    score = float(score_match.group(1)) if score_match else None
    max_score = float(max_match.group(1)) if max_match else None
    return score, max_score


def _parse_missing_image(motivation: str | None) -> bool:
    """True if the judge flagged the answer as too short / wrong because a required
    image was not delivered to the solving model (transport failure, not a real miss).
    Requires the bracketed single-token form so a model that echoes the template's
    "[MISSING_IMAGE=ja of nee]" placeholder is not misread as a positive."""
    if not motivation:
        return False
    m = re.search(r'\[MISSING_IMAGE[=:]\s*(ja|nee|true|false|yes|no)\]', motivation, re.IGNORECASE)
    return bool(m) and m.group(1).lower() in ("ja", "true", "yes")


async def _judge_one(
    client: AsyncOpenAI | None,
    semaphore: asyncio.Semaphore,
    db_lock: asyncio.Lock,
    conn,
    answer_id: int,
    content,
    judge_model: str,
    judge_stack: str,
    temperature: float,
    reasoning_effort: str,
    run_number: int,
    extra_body: dict | None,
    progress: dict,
    genai_client=None,
    genai_config=None,
):
    async with semaphore:
        start = time.perf_counter()
        motivation = None
        score = None
        max_score = None
        error = None
        for attempt in range(5):
            try:
                if genai_client:
                    resp = await genai_client.aio.models.generate_content(
                        model=judge_model, contents=content, config=genai_config
                    )
                    motivation = resp.text
                else:
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
                break
            except Exception as e:
                error = str(e)
                if "429" in error or "RESOURCE_EXHAUSTED" in error:
                    wait = 5 * (attempt + 1)
                    await asyncio.sleep(wait)
                    continue
                motivation = None
                break
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
        if _parse_missing_image(motivation):
            progress["missing_image"].add(answer_id)
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
    dry_run: bool = False,
):
    conn = init_db()
    is_genai = judge_stack == "genai"
    # Defer client creation past the dry-run early-return so --dry-run (which only
    # counts answers from the DB) needs no credentials.
    client = genai_client = genai_config = extra_body = None
    if not dry_run:
        if is_genai:
            genai_client = genai.Client(api_key=get_api_key("genai"))
            genai_levels = {"off": "minimal", "low": "low", "medium": "medium",
                            "high": "high", "on": "high", "xhigh": "high"}
            level = genai_levels.get(reasoning_effort, "high")
            if "gemma" in judge_model.lower():
                thinking_cfg = types.ThinkingConfig(
                    thinking_level="minimal" if reasoning_effort == "off" else None,
                    include_thoughts=reasoning_effort != "off",
                )
            else:
                thinking_cfg = types.ThinkingConfig(
                    thinking_level=level, include_thoughts=True,
                )
            genai_config = types.GenerateContentConfig(
                thinking_config=thinking_cfg,
                max_output_tokens=16384,
                temperature=temperature,
            )
        else:
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

    # Pre-cache images (raw bytes for genai, data URIs for OpenAI)
    image_cache = {}
    for a in answers:
        for path in json.loads(a["image_paths"]):
            if path not in image_cache:
                if is_genai:
                    image_cache[path] = (IMAGES_BASE / path).read_bytes()
                else:
                    image_cache[path] = f"data:image/png;base64,{load_image_as_base64(IMAGES_BASE / path)}"
        cv_raw = a["correctievoorschrift_paths"]
        if cv_raw:
            for path in json.loads(cv_raw):
                if path not in image_cache:
                    if is_genai:
                        image_cache[path] = (IMAGES_BASE / path).read_bytes()
                    else:
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

        if is_genai:
            parts = []
            for path in json.loads(a["image_paths"]):
                parts.append(types.Part.from_bytes(data=image_cache[path], mime_type="image/png"))
            for path in cv_paths:
                parts.append(types.Part.from_bytes(data=image_cache[path], mime_type="image/png"))
            parts.append(types.Part.from_text(text=JUDGE_PROMPT_TEMPLATE.format(response=a["response"])))
            answer_content[a["id"]] = [types.Content(role="user", parts=parts)]
        else:
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

    if dry_run:
        print(f"[dry-run] would judge {len(tasks)} answer×run pair(s) with {judge_model} "
              f"(answer-model={answer_model}, solve-runs={solve_run_numbers}, "
              f"reasoning={solve_reasoning}, judge-count={judge_count}) — no API calls, no DB writes.")
        conn.close()
        return

    print(f"Judging {len(tasks)} answer×run pairs with {judge_model} (concurrency={concurrency})...")

    progress = {"done": 0, "errors": 0, "no_score": 0, "total": len(tasks), "missing_image": set()}
    semaphore = asyncio.Semaphore(concurrency)
    db_lock = asyncio.Lock()

    async_tasks = [
        _judge_one(
            client, semaphore, db_lock, conn,
            answer_id, answer_content[answer_id],
            judge_model, judge_stack, temperature, reasoning_effort, judge_num,
            extra_body, progress,
            genai_client=genai_client, genai_config=genai_config,
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

    # Surface answers the judge flagged as missing their image: these low scores reflect a
    # transport failure (the figure never reached the solver), not the model's ability, and
    # are the questions to re-solve rather than trust.
    missing_ids = progress["missing_image"]
    if missing_ids:
        qnum_by_id = {a["id"]: a["question_number"] for a in answers}
        qnums = sorted({qnum_by_id[i] for i in missing_ids}, key=int)
        qlist = ", ".join(f"Q{n}" for n in qnums)
        print(f"IMPORTANT {qlist} are reported to have missing images")

    conn.close()

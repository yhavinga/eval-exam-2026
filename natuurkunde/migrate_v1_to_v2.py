#!/usr/bin/env python3
"""One-time migration: v1 schema (params per answer) -> v2 schema (runs table).

Usage: cd natuurkunde && python migrate_v1_to_v2.py
"""

import json
import sqlite3
from pathlib import Path

OLD_DB = Path("eval.db.v1")
NEW_DB = Path("eval.db")
SCHEMA = Path("schema.sql")


def migrate():
    if not OLD_DB.exists():
        print(f"Old database {OLD_DB} not found. Already migrated?")
        return

    old = sqlite3.connect(str(OLD_DB))
    old.row_factory = sqlite3.Row

    # Create new DB with v2 schema
    if NEW_DB.exists():
        NEW_DB.unlink()
    new = sqlite3.connect(str(NEW_DB))
    new.row_factory = sqlite3.Row
    new.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA) as f:
        new.executescript(f.read())
    new.commit()

    # 1. Copy questions as-is
    questions = old.execute("SELECT * FROM questions").fetchall()
    for q in questions:
        new.execute("""
            INSERT INTO questions (id, exam_code, question_number, question_name, image_paths,
                                   correctievoorschrift_paths, max_punten, prompt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (q["id"], q["exam_code"], q["question_number"], q["question_name"],
              q["image_paths"], q["correctievoorschrift_paths"], q["max_punten"], q["prompt"]))
    new.commit()
    print(f"Copied {len(questions)} questions")

    # 2. Group answers by config -> create runs
    configs = old.execute("""
        SELECT model, inference_stack, base_url, temperature, top_p, top_k,
               presence_penalty, max_tokens, reasoning_enabled, COUNT(*) as cnt,
               MIN(created_at) as first_created
        FROM answers
        GROUP BY model, inference_stack, base_url, temperature, top_p, top_k,
                 presence_penalty, max_tokens, reasoning_enabled
        ORDER BY first_created
    """).fetchall()

    # Track run_number per config key
    run_number_tracker = {}
    run_id_map = {}  # old (model, stack, ... , reasoning) -> new run_id

    for cfg in configs:
        config_key = (cfg["model"], cfg["inference_stack"], cfg["base_url"],
                      cfg["temperature"], cfg["top_p"], cfg["top_k"],
                      cfg["presence_penalty"], cfg["max_tokens"])

        run_number = run_number_tracker.get(config_key, 0) + 1
        run_number_tracker[config_key] = run_number

        reasoning_effort = "on" if cfg["reasoning_enabled"] else "off"

        cur = new.execute("""
            INSERT INTO runs (created_at, model, inference_stack, base_url, temperature, top_p,
                              top_k, presence_penalty, max_tokens, reasoning_effort, run_number, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
        """, (cfg["first_created"], cfg["model"], cfg["inference_stack"], cfg["base_url"],
              cfg["temperature"], cfg["top_p"], cfg["top_k"], cfg["presence_penalty"],
              cfg["max_tokens"], reasoning_effort, run_number, None))
        run_id = cur.fetchone()[0]

        lookup_key = config_key + (cfg["reasoning_enabled"],)
        run_id_map[lookup_key] = run_id

    new.commit()
    print(f"Created {len(configs)} runs")

    # 3. Migrate answers
    answers = old.execute("SELECT * FROM answers ORDER BY id").fetchall()
    migrated = 0
    for a in answers:
        config_key = (a["model"], a["inference_stack"], a["base_url"],
                      a["temperature"], a["top_p"], a["top_k"],
                      a["presence_penalty"], a["max_tokens"], a["reasoning_enabled"])
        run_id = run_id_map[config_key]

        new.execute("""
            INSERT INTO answers (id, run_id, question_id, created_at, response, reasoning,
                                 duration_ms, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (a["id"], run_id, a["question_id"], a["created_at"],
              a["response"], a["reasoning"], a["duration_ms"], a["error"]))
        migrated += 1

    new.commit()
    print(f"Migrated {migrated} answers")

    # 4. Migrate judgements (add temperature=1.0, reasoning_effort inferred from answer's run)
    judgements = old.execute("SELECT * FROM judgements ORDER BY id").fetchall()
    migrated_j = 0
    for j in judgements:
        # Get the answer's run to determine reasoning_effort
        answer = new.execute("SELECT run_id FROM answers WHERE id = ?", (j["answer_id"],)).fetchone()
        if answer:
            run = new.execute("SELECT reasoning_effort FROM runs WHERE id = ?", (answer["run_id"],)).fetchone()
            reasoning_effort = run["reasoning_effort"] if run else "on"
        else:
            reasoning_effort = "on"

        new.execute("""
            INSERT INTO judgements (id, answer_id, created_at, judge_model, judge_stack,
                                    temperature, reasoning_effort, score, max_score,
                                    motivation, duration_ms, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (j["id"], j["answer_id"], j["created_at"], j["judge_model"], j["judge_stack"],
              1.0, reasoning_effort, j["score"], j["max_score"],
              j["motivation"], j["duration_ms"], j["error"]))
        migrated_j += 1

    new.commit()
    print(f"Migrated {migrated_j} judgements")

    # 5. Sanity checks
    for table in ["questions", "answers", "judgements"]:
        old_count = old.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        new_count = new.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        status = "OK" if old_count == new_count else "MISMATCH"
        print(f"  {table}: {old_count} -> {new_count} [{status}]")

    run_count = new.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    print(f"  runs: {run_count} (expected {len(configs)})")

    old.close()
    new.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    migrate()

-- VWO Exam Evaluation Schema v2

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_code TEXT NOT NULL,
    question_number TEXT NOT NULL,
    question_name TEXT,
    image_paths TEXT NOT NULL,
    correctievoorschrift_paths TEXT,
    max_punten INTEGER,
    prompt TEXT DEFAULT 'Los dit op',
    UNIQUE(exam_code, question_number)
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    model TEXT NOT NULL,
    inference_stack TEXT NOT NULL,
    base_url TEXT NOT NULL,
    temperature REAL NOT NULL,
    top_p REAL NOT NULL,
    top_k INTEGER NOT NULL,
    presence_penalty REAL,
    max_tokens INTEGER NOT NULL,
    reasoning_effort TEXT NOT NULL,
    run_number INTEGER NOT NULL,
    notes TEXT,
    -- OpenRouter routing, first-class so a provider/quant can be a clean sweep
    -- axis. Nullable: lmstudio/genai and pre-convention runs leave them unset.
    provider TEXT,
    quantization TEXT,
    run_name TEXT GENERATED ALWAYS AS (
        model || '/' || inference_stack || '/t' || temperature || '/reasoning-' || reasoning_effort || '/' || run_number
    ) STORED
);

CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    question_id INTEGER NOT NULL REFERENCES questions(id),
    created_at TEXT NOT NULL,
    response TEXT,
    reasoning TEXT,
    duration_ms INTEGER,
    error TEXT,
    UNIQUE(run_id, question_id)
);

CREATE TABLE IF NOT EXISTS judgements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    answer_id INTEGER NOT NULL REFERENCES answers(id),
    created_at TEXT NOT NULL,
    judge_model TEXT NOT NULL,
    judge_stack TEXT NOT NULL,
    temperature REAL NOT NULL,
    reasoning_effort TEXT NOT NULL,
    run_number INTEGER NOT NULL,
    score REAL,
    max_score REAL,
    motivation TEXT,
    duration_ms INTEGER,
    error TEXT
);

-- A parameter sweep. `spec` is the declarative grid (axes x fixed - exclude +
-- target_n + judge); cells are derived from it on demand rather than stored, so
-- editing the spec can never leave stale cells behind. `goal` is the hypothesis;
-- `learnings` is filled in as results land.
CREATE TABLE IF NOT EXISTS sweeps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    name TEXT NOT NULL UNIQUE,
    goal TEXT NOT NULL,
    spec TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    learnings TEXT
);

CREATE INDEX IF NOT EXISTS idx_answers_run ON answers(run_id);
CREATE INDEX IF NOT EXISTS idx_answers_question ON answers(question_id);
CREATE INDEX IF NOT EXISTS idx_judgements_answer ON judgements(answer_id);

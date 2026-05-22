-- VWO Exam Evaluation Schema

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_code TEXT NOT NULL,                -- e.g. "vw-1023-a-26-1-o"
    question_number TEXT NOT NULL,          -- e.g. "01", "02"
    question_name TEXT,                     -- e.g. "botsproef"
    image_paths TEXT NOT NULL,              -- JSON array of image paths
    correctievoorschrift_paths TEXT,        -- JSON array of CV image paths
    max_punten INTEGER,
    prompt TEXT DEFAULT 'Los dit op',
    UNIQUE(exam_code, question_number)
);

CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL REFERENCES questions(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    -- run metadata
    model TEXT NOT NULL,                    -- e.g. "qwen3.5-27b"
    inference_stack TEXT,                   -- e.g. "lmstudio", "ollama"
    base_url TEXT,
    temperature REAL DEFAULT 0.0,
    max_tokens INTEGER,
    -- response
    response TEXT,
    duration_ms INTEGER,
    error TEXT
);

CREATE TABLE IF NOT EXISTS judgements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    answer_id INTEGER NOT NULL REFERENCES answers(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    judge_model TEXT NOT NULL,
    judge_stack TEXT,
    score REAL,
    max_score REAL,
    motivation TEXT,
    duration_ms INTEGER,
    error TEXT
);

CREATE INDEX IF NOT EXISTS idx_answers_question ON answers(question_id);
CREATE INDEX IF NOT EXISTS idx_answers_model ON answers(model);
CREATE INDEX IF NOT EXISTS idx_judgements_answer ON judgements(answer_id);

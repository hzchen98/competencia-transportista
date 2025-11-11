CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20),
    category VARCHAR(20) DEFAULT 'teorico',
    question TEXT,
    options JSONB,
    correct_option TEXT,
    norma TEXT
);

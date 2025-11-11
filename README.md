# Transportista Quiz — README

A small Python + Postgres quiz system with a Streamlit UI. Questions are loaded from text files / zip archives into a Postgres `questions` table on startup.

## Contents
- `docker-compose.yml` — starts Postgres, a one\-off `loader` service and the Streamlit app.
- `db/create_table.sql` — DB schema run by Postgres on first initialization.
- `db/load_questions.py` — parser + inserter used by the `loader` service.
- `preguntas.zip` / `casos.zip` — expected archives with `.txt` files (theoretical / practical).
- `web/quiz_app.py` — Streamlit front\-end.

## Requirements
- For local runs: Python 3.11 and `psycopg2-binary`

## Quick start (Docker)
1. Put `preguntas.zip` and `casos.zip` in the project root.
2. Start services:
   - PowerShell / CMD:
     - `docker compose up --build`
   - This will:
     - initialize Postgres (runs `db/create_table.sql` on first run),
     - wait for DB healthcheck, then run the `loader` service which executes `db/load_questions.py`,
     - start the Streamlit app on `http://localhost:8501`.

To re-run the loader without recreating the DB data, run:
- `docker compose run --rm loader`

To re-run initialization scripts (SQL) remove the DB volume and restart:
- `docker volume rm <project>_db_data`
- `docker compose up --build`

## Local run (without Docker)
1. Create venv and install:
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
   - `pip install psycopg2-binary`
2. Set environment variables (example PowerShell):
   - `$env:POSTGRES_HOST="localhost"`
   - `$env:POSTGRES_NAME="quizdb"`
   - `$env:POSTGRES_USER="postgres"`
   - `$env:POSTGRES_PASSWORD="your_password"`
   - `$env:POSTGRES_PORT="5432"`
3. Run:
   - `python db/load_questions.py`

## Input formats
- Practical (\`practico\`): blocks with `COD:`, `PREGUNTA:`, `RESPUESTA A:` … `RESPUESTA H:`, `SOLUCION: RESPUESTA X`, `NORMA:`.
- Theoretical (\`teorico\`): blocks with `COD:`, `PREGUNTA:`, `A:`, `B:`, `C:`, `D:`, `SOLUCION: X`, `NORMA:`.
- Zips should contain `.txt` files in UTF\-8.

## Behavior notes
- `db/create_table.sql` only runs on first container initialization.
- `loader` waits for DB health and runs `db/load_questions.py` once (service configured with `restart: "no"`).
- The loader inserts parsed questions into `questions`. Duplicate `code` handling is not enforced by the loader by default; consider adding checks if needed.

## Troubleshooting
- If loader fails due to DB connection, check `POSTGRES_*` env vars and DB health.
- If parsing misses questions, confirm TXT format matches the expected patterns and files are UTF\-8 encoded.
- To inspect DB: connect to `localhost:5439` (host port) with the configured credentials.

## Useful file locations
- Schema: `db/create_table.sql`
- Loader script: `db/load_questions.py`
- Streamlit app: `web/quiz_app.py`
- Compose file: `docker-compose.yml`
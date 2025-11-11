import os

import psycopg2
import re
import zipfile
import json

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "dbname": os.getenv("POSTGRES_NAME", "quizdb"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "your_password"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}


def parse_teorico(text):
    pattern = re.compile(
        r"COD:\s*(?P<code>\S+)\s*"
        r"PREGUNTA:\s*(?P<question>.*?)\s*"
        r"A:\s*(?P<a>.*?)\s*"
        r"B:\s*(?P<b>.*?)\s*"
        r"C:\s*(?P<c>.*?)\s*"
        r"D:\s*(?P<d>.*?)\s*"
        r"SOLUCION:\s*(?P<correct>[A-D])\s*"
        r"NORMA:\s*(?P<norma>.*?)\s*(?=COD:|$)",
        re.DOTALL
    )
    questions = []
    for m in pattern.finditer(text):
        gd = m.groupdict()
        questions.append({
            "code": gd["code"],
            "category": "teorico",
            "question": gd["question"].strip(),
            "options": {
                "A": gd["a"].strip(),
                "B": gd["b"].strip(),
                "C": gd["c"].strip(),
                "D": gd["d"].strip(),
            },
            "correct_option": gd["correct"].strip(),
            "norma": gd["norma"].strip()
        })
    return questions


def parse_practico(text):
    pattern = re.compile(
        r"COD:\s*(?P<code>\S+)\s*"
        r"PREGUNTA:\s*(?P<question>.*?)\s*"
        r"(?P<responses>(?:RESPUESTA\s+[A-H]:.*?)+)"
        r"SOLUCION:\s*(?P<correct>RESPUESTA\s+[A-H])\s*"
        r"NORMA:\s*(?P<norma>.*?)(?=COD:|$)",
        re.DOTALL | re.IGNORECASE,
    )

    resp_item = re.compile(
        r"RESPUESTA\s*(?P<label>[A-H]):\s*(?P<body>.*?)(?=(RESPUESTA\s+[A-H]:|SOLUCION:|$))",
        re.DOTALL | re.IGNORECASE,
    )

    results = []
    for m in pattern.finditer(text):
        code = m.group("code").strip()
        question = m.group("question").strip()
        responses_block = m.group("responses")
        norma = m.group("norma").strip()
        correct = m.group("correct").strip().replace("RESPUESTA", "").strip()
        options = {}
        for r in resp_item.finditer(responses_block):
            lbl = r.group("label").strip()
            body = r.group("body").strip().replace("\n", " ").strip()
            options[lbl] = body
        results.append(
            {
                "code": code,
                "category": "practico",
                "question": question,
                "options": options,
                "correct_option": correct,
                "norma": norma,
            }
        )
    return results

def load_from_zip(zip_path, category="teorico"):
    with zipfile.ZipFile(zip_path, "r") as z:
        all_questions = []
        for name in z.namelist():
            if not name.endswith(".txt"):
                continue
            text = z.read(name).decode("utf-8")
            if category == "teorico":
                all_questions += parse_teorico(text)
            else:
                all_questions += parse_practico(text)
        return all_questions


def insert_questions(questions):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    for q in questions:
        cur.execute("""
                    INSERT INTO questions (code, category, question, options, correct_option, norma)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """, (q["code"], q["category"], q["question"], json.dumps(q["options"]), q["correct_option"],
                          q["norma"]))
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    teorico_zip = "preguntas.zip"
    practico_zip = "casos.zip"

    teorico = load_from_zip(teorico_zip, "teorico")
    practico = load_from_zip(practico_zip, "practico")

    insert_questions(teorico + practico)
    print(f"✅ Loaded {len(teorico)} theoretical and {len(practico)} practical questions.")

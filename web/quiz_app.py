import os

import streamlit as st
import psycopg2
import time
import json

# --- DATABASE CONNECTION ---
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "dbname": os.getenv("POSTGRES_NAME", "quizdb"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "your_password"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}

def get_random_questions(category, limit=None):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    query = f"""
        SELECT id, question, options, correct_option, category 
        FROM questions 
        WHERE category = %s 
        ORDER BY RANDOM()
    """
    if limit:
        query += f" LIMIT {limit}"
    cur.execute(query, (category,))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


# --- STREAMLIT CONFIG ---
st.set_page_config(page_title="Quiz App", page_icon="🧠", layout="wide")
st.title("🧠 Transportista Quiz System")

# --- SIDEBAR ---
category = st.sidebar.selectbox("📚 Choose Category:", ["teorico", "practico"])
mode = st.sidebar.selectbox(
    "🎯 Select Exam Mode",
    ["Free Quiz", "Exam Test", "Exam Mode"]
)

# --- STATE ---
if "index" not in st.session_state:
    st.session_state.index = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "questions" not in st.session_state:
    st.session_state.questions = []
if "start_time" not in st.session_state:
    st.session_state.start_time = None


# --- RENDER QUESTION ---
def render_question(q):
    st.markdown(f"### {q[1]}")
    options = q[2]
    choice = st.radio("Choose an answer:", list(options.keys()), format_func=lambda x: options[x])
    return choice


# =======================
#  FREE QUIZ MODE
# =======================
if mode == "Free Quiz":
    if not st.session_state.questions:
        st.session_state.questions = get_random_questions(category, 1)

    q = st.session_state.questions[0]
    choice = render_question(q)

    if st.button("Submit"):
        if choice == q[3]:
            st.success("✅ Correct!")
        else:
            st.error(f"❌ Incorrect. Correct answer: {q[3]}")
        st.session_state.questions = get_random_questions(category, 1)


# =======================
#  EXAM TEST MODE
# =======================
elif mode == "Exam Test":
    if category == "practico":
        question_options = [4, 6, 8, 10]
    else:
        question_options = [10, 20, 30, 40, 50, 100]

    num = st.sidebar.selectbox("📄 Number of questions:", question_options, index=0)

    if st.button("Start Test"):
        st.session_state.questions = get_random_questions(category, num)
        st.session_state.index = 0
        st.session_state.score = 0
        st.session_state.start_time = time.time()

    if st.session_state.questions:
        total = len(st.session_state.questions)
        q = st.session_state.questions[st.session_state.index]
        st.subheader(f"Question {st.session_state.index + 1}/{total}")
        choice = render_question(q)

        if st.button("Next"):
            if choice == q[3]:
                st.session_state.score += 1
            st.session_state.index += 1
            if st.session_state.index == total:
                elapsed = int(time.time() - st.session_state.start_time)
                st.success(f"✅ Completed! Score: {st.session_state.score}/{total}")
                st.info(f"🕒 Time: {elapsed//60} min {elapsed%60} sec")
                st.session_state.questions = []


# =======================
#  EXAM MODE
# =======================
elif mode == "Exam Mode":
    # RULE: Supuestos prácticos only 4 questions, teorico = 200
    total_q = 4 if category == "practico" else 200
    time_limit = 7200 if category == "teorico" else 1800  # 2h vs 30min (optional tweak)

    if st.button("Start Exam"):
        st.session_state.questions = get_random_questions(category, total_q)
        st.session_state.index = 0
        st.session_state.score = 0
        st.session_state.start_time = time.time()

    if st.session_state.questions:
        q = st.session_state.questions[st.session_state.index]
        elapsed = int(time.time() - st.session_state.start_time)
        remaining = time_limit - elapsed
        if remaining <= 0:
            st.error("⏰ Time’s up!")
            st.stop()

        st.sidebar.write(f"⏱ Remaining: {remaining//60}m {remaining%60}s")
        st.subheader(f"Question {st.session_state.index + 1}/{total_q}")
        choice = render_question(q)

        if st.button("Next"):
            if choice == q[3]:
                st.session_state.score += 1
            st.session_state.index += 1
            if st.session_state.index == total_q:
                st.success(f"✅ Exam Finished! Score: {st.session_state.score}/{total_q}")
                st.session_state.questions = []

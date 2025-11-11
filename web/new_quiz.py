import os

import streamlit as st
import psycopg2
import random
import time
from datetime import datetime

# =============================
# DATABASE CONFIG
# =============================
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "dbname": os.getenv("POSTGRES_NAME", "quizdb"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "your_password"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}


# =============================
# DATABASE UTILITIES
# =============================
def get_questions(category):
    """Fetch all questions for the given category."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
                SELECT id, question, options, correct_option
                FROM questions
                WHERE category = %s
                """, (category,))
    questions = cur.fetchall()
    cur.close()
    conn.close()
    return questions


# =============================
# QUIZ UTILITIES
# =============================
def initialize_session():
    """Initialize Streamlit session state."""
    defaults = {
        "mode": None,
        "category": None,
        "questions": [],
        "index": 0,
        "responses": [],
        "start_time": None,
        "finished": False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_exam():
    """Reset exam session state."""
    for key in ["questions", "index", "responses", "start_time", "finished"]:
        st.session_state[key] = None if key == "start_time" else []
    st.session_state.index = 0
    st.session_state.finished = False


def calculate_score(responses):
    """Compute final score with penalties."""
    correct = sum(1 for r in responses if r["user_answer"] == r["correct"])
    wrong = sum(1 for r in responses if r["user_answer"] and r["user_answer"] != r["correct"])
    total = len(responses)
    score = correct - (wrong * (1 / 3))
    percentage = (score / total) * 100 if total > 0 else 0
    passed = percentage >= 60
    return correct, wrong, score, percentage, passed


def _reset_for_ui_change():
    """Callback when mode or category changes: clear any active quiz state so UI updates."""
    reset_exam()

# =============================
# MAIN APP
# =============================
def main():
    st.text("🚚 Transportista Quiz System")

    initialize_session()

    # --- Choose category ---
    category = st.selectbox("Choose Category:", ["Teórico", "Supuestos Prácticos"], on_change=_reset_for_ui_change)
    st.session_state.category = "teorico" if category == "Teórico" else "practico"

    # --- Choose mode ---
    mode = st.selectbox("Choose Mode:", ["Free Quiz", "Exam Test", "Exam Mode"], on_change=_reset_for_ui_change)
    st.session_state.mode = mode

    if mode == "Exam Test":
        if st.session_state.category == "practico":
            num = st.selectbox("Number of questions:", [2, 4, 6, 8, 10])
        else:
            num = st.selectbox("Number of questions:", [2, 10, 20, 30, 40, 50, 70, 100, 150, 200])

    # --- Start button ---
    if st.button("Start Quiz"):
        reset_exam()
        questions = get_questions(st.session_state.category)

        if not questions:
            st.error("No questions found for this category.")
            return

        random.shuffle(questions)

        # mode configurations
        if mode == "Free Quiz":
            st.session_state.questions = questions
        elif mode == "Exam Test":
            st.session_state.questions = random.sample(questions, min(num, len(questions)))
        elif mode == "Exam Mode":
            if st.session_state.category == "practico":
                st.session_state.questions = random.sample(questions, min(4, len(questions)))
            else:
                st.session_state.questions = random.sample(questions, min(200, len(questions)))
            st.session_state.start_time = time.time()

    # --- Exam display logic ---
    if st.session_state.questions and not st.session_state.finished:
        total_q = len(st.session_state.questions)
        current_q = st.session_state.questions[st.session_state.index]
        q_id, question, options, correct = current_q

        st.markdown(f"**Question {st.session_state.index + 1}/{total_q}**")
        st.write(question)

        user_choice = st.radio("Choose an answer:", list(options.keys()), format_func=lambda x: f'{x} {options[x]}', key=f"q{q_id}")

        if st.button("Submit Answer"):
            st.session_state.responses.append({
                "question_id": q_id,
                "question": question,
                "options": options,
                "correct": correct,
                "user_answer": user_choice
            })

            # For Free Quiz show immediate feedback
            if mode == "Free Quiz":
                if user_choice == correct:
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Incorrect. Correct answer: {correct}")

            # Move to next
            st.session_state.index += 1
            if st.session_state.index >= total_q:
                st.session_state.finished = True

        # Timer for Exam Mode
        if mode == "Exam Mode" and st.session_state.start_time:
            elapsed = time.time() - st.session_state.start_time
            remaining = 2 * 60 * 60 - elapsed
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            st.info(f"⏱ Time remaining: {mins:02d}:{secs:02d}")
            if remaining <= 0:
                st.warning("⏰ Time’s up! Submitting automatically...")
                st.session_state.finished = True

    # --- End of exam summary ---
    if st.session_state.finished and st.session_state.responses:
        correct, wrong, score, percentage, passed = calculate_score(st.session_state.responses)

        st.subheader("📊 Exam Summary")
        st.write(f"✅ Correct answers: {correct}")
        st.write(f"❌ Wrong answers: {wrong}")
        st.write(f"🧮 Final Score: {score:.2f} / {len(st.session_state.responses)}")
        st.write(f"📈 Percentage: {percentage:.1f}%")

        if st.session_state.mode == "Exam Mode" and st.session_state.start_time:
            elapsed = time.time() - st.session_state.start_time
            st.write(f"⏱ Time used: {elapsed / 60:.1f} minutes")

        if passed:
            st.success("🎉 Congratulations! You passed the exam.")
        else:
            st.error("❌ You did not reach the 60% required to pass.")

        # Review section
        st.subheader("📝 Review Answers")
        for i, r in enumerate(st.session_state.responses, 1):
            is_correct = r["user_answer"] == r["correct"]
            color = "green" if is_correct else "red"
            st.markdown(f"**{i}. {r['question']}**")
            for opt in r["options"]:
                if opt == r["correct"]:
                    st.markdown(f"- ✅ **{opt}** {r['options'][opt]} (correct)")
                elif opt == r["user_answer"]:
                    st.markdown(f"- ❌ **{opt}** {r['options'][opt]} (your answer)")
                else:
                    st.markdown(f"- {opt} {r['options'][opt]}")
            st.markdown("---")

        if st.button("Restart"):
            reset_exam()


if __name__ == "__main__":
    main()

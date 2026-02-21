from flask import Flask, render_template, request, redirect, session
import sqlite3
import random
import os

app = Flask(__name__)
app.secret_key = "secret123"

DB_PATH = "quiz_app.db"


# ---------- DATABASE INIT (VERY IMPORTANT FOR RENDER) ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # users
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # questions
    c.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        opt_a TEXT,
        opt_b TEXT,
        opt_c TEXT,
        opt_d TEXT,
        correct_opt TEXT,
        test_id INTEGER DEFAULT 1
    )
    """)

    # results
    c.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        test_id INTEGER,
        score INTEGER,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # answers
    c.execute("""
    CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        result_id INTEGER,
        question_id INTEGER,
        selected TEXT,
        is_correct INTEGER
    )
    """)

    # ✅ create admin if not exists
    c.execute("SELECT * FROM users WHERE role='admin'")
    if not c.fetchone():
        c.execute(
            "INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)",
            ("Admin", "admin@gmail.com", "1234", "admin"),
        )

    conn.commit()
    conn.close()


# ---------- DATABASE HELPER ----------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# 🔥 RUN INIT ON STARTUP (CRITICAL FOR RENDER)
init_db()


# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password),
        )
        user = cursor.fetchone()
        db.close()

        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect("/admin")
            else:
                return redirect("/student")
        else:
            return "Invalid credentials"

    return render_template("login.html")


# ---------- ADMIN ----------
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/")
    return render_template("admin_dashboard.html")


# ---------- STUDENT TEST ----------
@app.route("/student")
def student():
    if session.get("role") != "student":
        return redirect("/")

    student_id = session["user_id"]

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT question_id FROM answers
        JOIN results ON answers.result_id = results.id
        WHERE results.student_id = ? AND is_correct = 0
    """, (student_id,))
    wrong_ids = [row["question_id"] for row in cursor.fetchall()]

    if wrong_ids:
        placeholders = ",".join(["?"] * len(wrong_ids))
        cursor.execute(
            f"SELECT * FROM questions WHERE id IN ({placeholders})",
            wrong_ids
        )
    else:
        cursor.execute("SELECT * FROM questions WHERE test_id = 1")

    rows = cursor.fetchall()
    db.close()

    questions = [dict(row) for row in rows]
    random.shuffle(questions)

    for q in questions:
        opts = [
            ('A', q['opt_a']),
            ('B', q['opt_b']),
            ('C', q['opt_c']),
            ('D', q['opt_d'])
        ]
        random.shuffle(opts)
        q['shuffled_options'] = opts

    return render_template("student_test.html", questions=questions)


# ---------- ADD STUDENT ----------
@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if session.get("role") != "admin":
        return redirect("/")

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?,?,?,'student')",
            (name, email, password),
        )

        db.commit()
        db.close()

        return "Student added successfully!"

    return render_template("add_student.html")


# ---------- ADD QUESTION ----------
@app.route("/add_question", methods=["GET", "POST"])
def add_question():
    if session.get("role") != "admin":
        return redirect("/")

    if request.method == "POST":
        question = request.form["question"]
        a = request.form["a"]
        b = request.form["b"]
        c = request.form["c"]
        d = request.form["d"]
        correct = request.form["correct"]

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            """INSERT INTO questions
            (question, opt_a, opt_b, opt_c, opt_d, correct_opt)
            VALUES (?,?,?,?,?,?)""",
            (question, a, b, c, d, correct),
        )

        db.commit()
        db.close()

        return "Question added!"

    return render_template("add_question.html")


# ---------- SUBMIT TEST ----------
@app.route("/submit_test", methods=["POST"])
def submit_test():
    if session.get("role") != "student":
        return redirect("/")

    student_id = session["user_id"]

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM questions WHERE test_id = 1")
    questions = cursor.fetchall()

    score = 0
    for q in questions:
        selected = request.form.get(f"q{q['id']}")
        if selected == q["correct_opt"]:
            score += 1

    cursor.execute(
        "INSERT INTO results (student_id, test_id, score) VALUES (?,?,?)",
        (student_id, 1, score),
    )

    db.commit()
    db.close()

    return f"Your Score: {score} / {len(questions)}"


# ---------- HISTORY ----------
@app.route("/history")
def history():
    if session.get("role") != "student":
        return redirect("/")

    student_id = session["user_id"]

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM results WHERE student_id=? ORDER BY date DESC",
        (student_id,),
    )

    results = cursor.fetchall()
    db.close()

    return render_template("history.html", results=results)


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
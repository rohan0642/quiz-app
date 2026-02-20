from flask import Flask, render_template, request, redirect, session
import mysql.connector
import random

app = Flask(__name__)
app.secret_key = "secret123"

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root0000",
    database="quiz_app"
)

cursor = db.cursor(dictionary=True)


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password),
        )
        user = cursor.fetchone()

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


@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/")
    return render_template("admin_dashboard.html")


import random

@app.route("/student")
def student():
    if session.get("role") != "student":
        return redirect("/")

    student_id = session["user_id"]

    # wrong question logic (keep yours)
    cursor.execute("""
        SELECT question_id FROM answers
        JOIN results ON answers.result_id = results.id
        WHERE results.student_id = %s AND is_correct = 0
    """, (student_id,))
    wrong_ids = [row["question_id"] for row in cursor.fetchall()]

    if wrong_ids:
        format_strings = ','.join(['%s'] * len(wrong_ids))
        cursor.execute(
            f"SELECT * FROM questions WHERE id IN ({format_strings})",
            tuple(wrong_ids)
        )
    else:
        cursor.execute("SELECT * FROM questions WHERE test_id = 1")


    questions = cursor.fetchall()

    # ✅ SHUFFLE QUESTIONS
    random.shuffle(questions)

    # ✅ SHUFFLE OPTIONS FOR EACH QUESTION
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





@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if session.get("role") != "admin":
        return redirect("/")

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,'student')",
            (name, email, password),
        )
        db.commit()

        return "Student added successfully!"

    return render_template("add_student.html")


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

        cursor.execute(
            """INSERT INTO questions
            (question, opt_a, opt_b, opt_c, opt_d, correct_opt)
            VALUES (%s,%s,%s,%s,%s,%s)""",
            (question, a, b, c, d, correct),
        )
        db.commit()

        return "Question added!"

    return render_template("add_question.html")


@app.route("/submit_test", methods=["POST"])
def submit_test():
    if session.get("role") != "student":
        return redirect("/")

    student_id = session["user_id"]

    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    random.shuffle(questions)

    score = 0

    for q in questions:
        selected = request.form.get(f"q{q['id']}")

        if selected == q["correct_opt"]:
            score += 1

    # store result
    cursor.execute(
        "INSERT INTO results (student_id, test_id, score) VALUES (%s, %s, %s)",
        (student_id, 1, score),
    )
    db.commit()

    return f"Your Score: {score} / {len(questions)}"


@app.route("/history")
def history():
    if session.get("role") != "student":
        return redirect("/")

    student_id = session["user_id"]

    cursor.execute(
        "SELECT * FROM results WHERE student_id=%s ORDER BY date DESC",
        (student_id,)
    )

    results = cursor.fetchall()

    return render_template("history.html", results=results)



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)

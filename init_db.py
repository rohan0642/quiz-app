import sqlite3

conn = sqlite3.connect("quiz_app.db")
c = conn.cursor()

# USERS
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT,
    role TEXT
)
""")

# QUESTIONS
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

# RESULTS
c.execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    test_id INTEGER,
    score INTEGER,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ANSWERS
c.execute("""
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER,
    question_id INTEGER,
    selected TEXT,
    is_correct INTEGER
)
""")

conn.commit()
conn.close()

print("✅ SQLite DB ready")
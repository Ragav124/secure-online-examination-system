
import os
import sqlite3
from flask import current_app, g

QUESTIONS = [
    (
        "Which protocol encrypts web traffic?",
        ["HTTP", "HTTPS", "FTP", "Telnet"],
        1,
    ),
    (
        "Which technique protects stored passwords?",
        ["Plain text", "Base64", "Password hashing", "URL encoding"],
        2,
    ),
    (
        "What does SQL injection target?",
        ["Database queries", "Screen resolution", "Image quality", "Keyboard input"],
        0,
    ),
    (
        "Which principle gives users only necessary permissions?",
        ["Open access", "Least privilege", "Shared passwords", "Anonymous access"],
        1,
    ),
    (
        "Which attack attempts to trick users into revealing credentials?",
        ["Phishing", "Compression", "Caching", "Encryption"],
        0,
    ),
]


def get_db():
    if "db" not in g:
        os.makedirs(current_app.instance_path, exist_ok=True)
        db_path = os.path.join(current_app.instance_path, "exam.db")
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()

    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student'
                CHECK(role IN ('student')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option INTEGER NOT NULL
                CHECK(correct_option BETWEEN 0 AND 3)
        );

        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            event TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)

    count = db.execute(
        "SELECT COUNT(*) FROM questions"
    ).fetchone()[0]

    if count == 0:
        for question, options, correct in QUESTIONS:
            db.execute(
                """
                INSERT INTO questions (
                    question_text, option_a, option_b,
                    option_c, option_d, correct_option
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (question, *options, correct),
            )

    db.commit()

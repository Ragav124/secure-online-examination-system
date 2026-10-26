
import os
import time
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db, close_db, init_db
from security import configure_security_logging, log_security_event

load_dotenv()

app = Flask(__name__, instance_relative_config=True)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1",
    PERMANENT_SESSION_LIFETIME=1800,
    MAX_CONTENT_LENGTH=32 * 1024,
)

if not app.config["SECRET_KEY"]:
    raise RuntimeError(
        "Set SECRET_KEY in your private .env file before starting the app."
    )

csrf = CSRFProtect(app)
app.teardown_appcontext(close_db)
configure_security_logging(app)

EXAM_DURATION = 10 * 60


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self'; "
        "script-src 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'"
    )
    return response


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not 3 <= len(username) <= 30:
            flash("Username must be 3–30 characters.", "error")
            return render_template("register.html")

        if not all(c.isalnum() or c in "_-" for c in username):
            flash("Use only letters, numbers, _ or - in usernames.", "error")
            return render_template("register.html")

        if len(password) < 12 or len(password) > 128:
            flash("Password must be 12–128 characters.", "error")
            return render_template("register.html")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            db.commit()
        except Exception as exc:
            if "UNIQUE constraint failed" in str(exc):
                flash("That username is already registered.", "error")
                return render_template("register.html")
            raise

        log_security_event("registration_success", username)
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = get_db().execute(
            "SELECT id, username, password_hash, role FROM users "
            "WHERE username = ?",
            (username,),
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session.permanent = True
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            log_security_event("login_success", username)
            return redirect(url_for("dashboard"))

        log_security_event("login_failure", username or None)
        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    log_security_event("logout", session.get("username"))
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    result = get_db().execute(
        "SELECT score, total, submitted_at FROM results WHERE user_id = ?",
        (session["user_id"],),
    ).fetchone()

    return render_template("dashboard.html", result=result)


@app.route("/exam", methods=["GET", "POST"])
@login_required
def exam():
    db = get_db()
    user_id = session["user_id"]

    existing_result = db.execute(
        "SELECT id FROM results WHERE user_id = ?", (user_id,)
    ).fetchone()

    if existing_result:
        flash("You have already submitted this examination.", "warning")
        return redirect(url_for("result"))

    if request.method == "GET":
        session["exam_started_at"] = time.time()
        questions = db.execute(
            "SELECT id, question_text, option_a, option_b, option_c, option_d "
            "FROM questions ORDER BY id"
        ).fetchall()
        return render_template(
            "exam.html",
            questions=questions,
            duration=EXAM_DURATION,
        )

    started_at = session.get("exam_started_at")

    if started_at is None:
        abort(400, description="Exam session expired. Please start again.")

    elapsed = time.time() - started_at

    if elapsed < 0 or elapsed > EXAM_DURATION + 30:
        session.pop("exam_started_at", None)
        abort(400, description="Exam time expired. Submission was not accepted.")

    questions = db.execute(
        "SELECT id, correct_option FROM questions ORDER BY id"
    ).fetchall()

    score = 0
    for question in questions:
        submitted = request.form.get(str(question["id"]), "")
        if submitted in {"0", "1", "2", "3"}:
            if int(submitted) == question["correct_option"]:
                score += 1

    try:
        db.execute(
            "INSERT INTO results (user_id, score, total) VALUES (?, ?, ?)",
            (user_id, score, len(questions)),
        )
        db.commit()
    except Exception:
        db.rollback()
        log_security_event("duplicate_submission_blocked",
                           session.get("username"))
        flash("Your result was already recorded.", "warning")
        return redirect(url_for("result"))

    session.pop("exam_started_at", None)
    log_security_event("exam_submitted", session.get("username"))
    return redirect(url_for("result"))


@app.route("/result")
@login_required
def result():
    result_data = get_db().execute(
        "SELECT score, total, submitted_at FROM results WHERE user_id = ?",
        (session["user_id"],),
    ).fetchone()

    if result_data is None:
        return redirect(url_for("dashboard"))

    return render_template("result.html", result=result_data)


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")


import logging
from flask import current_app
from database import get_db


def configure_security_logging(app):
    handler = logging.FileHandler("security.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s"
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def log_security_event(event, username=None):
    db = get_db()
    db.execute(
        "INSERT INTO security_events (username, event) VALUES (?, ?)",
        (username, event),
    )
    db.commit()

    # Keep log messages free of passwords and submitted answers.
    safe_username = username or "anonymous"
    current_app.logger.info(
        "Security event=%s username=%s",
        event,
        safe_username,
    )

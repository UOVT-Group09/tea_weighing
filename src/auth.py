"""Operator authentication: login, logout and session handling.

Owner: H.G.P.C. Sagara (PM & Integration Dev)

The weighing centre is used by one or more *operators*. This module owns the
``operator`` credential table, the login/logout routes, and the
``login_required`` decorator that the rest of the app uses to protect routes.

Passwords are stored hashed (werkzeug, which ships with Flask) — never in
plain text.
"""

from functools import wraps

import logging

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from .config import Config
from .db import DatabaseError, execute, query

log = logging.getLogger(__name__)

bp = Blueprint("auth", __name__)


# --- table bootstrap -------------------------------------------------------

CREATE_OPERATOR_TABLE = """
CREATE TABLE IF NOT EXISTS operator (
    operator_id  INT AUTO_INCREMENT PRIMARY KEY,
    username     VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def ensure_operator_table():
    """Create the operator table and seed a default operator if empty.

    Called once at startup. Authentication is owned by integration, so the
    operator table lives here rather than in the shared schema (models.py).
    Safe to call repeatedly. Returns True on success, False if the database
    is unreachable (the app still boots so the rest can be demoed).
    """
    try:
        execute(CREATE_OPERATOR_TABLE)
        existing = query("SELECT COUNT(*) AS n FROM operator", one=True)
        if existing and existing["n"] == 0:
            execute(
                "INSERT INTO operator (username, password_hash) VALUES (%s, %s)",
                (
                    Config.DEFAULT_OPERATOR_USERNAME,
                    generate_password_hash(Config.DEFAULT_OPERATOR_PASSWORD),
                ),
            )
            log.info("Seeded default operator '%s'.", Config.DEFAULT_OPERATOR_USERNAME)
        return True
    except DatabaseError as exc:
        log.warning("Operator table not ready: %s", exc)
        return False


# --- session helpers -------------------------------------------------------


def login_required(view):
    """Decorator: redirect to the login page if no operator is in session."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("operator_id") is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@bp.before_app_request
def load_logged_in_operator():
    """Expose the current operator on ``g`` for templates and views."""
    operator_id = session.get("operator_id")
    g.operator = (
        {"id": operator_id, "username": session.get("operator_username")}
        if operator_id is not None
        else None
    )


# --- routes ----------------------------------------------------------------


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("auth/login.html")

        try:
            operator = query(
                "SELECT * FROM operator WHERE username = %s", (username,), one=True
            )
        except DatabaseError:
            flash("Login is temporarily unavailable. Please try again.", "danger")
            return render_template("auth/login.html")

        if operator and check_password_hash(operator["password_hash"], password):
            session.clear()
            session["operator_id"] = operator["operator_id"]
            session["operator_username"] = operator["username"]
            flash(f"Welcome, {operator['username']}.", "success")
            nxt = request.args.get("next")
            return redirect(nxt or url_for("dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

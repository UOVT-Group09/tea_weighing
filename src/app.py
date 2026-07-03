"""Flask application factory, routing and module integration.

Owner: H.G.P.C. Sagara (PM & Integration Dev)

This is the integration point for the whole system. Each teammate builds a
feature module that exposes a Flask ``bp`` blueprint; this factory wires them
all together, sets up authentication and configuration, and installs the
error handlers that keep stack traces away from the user (guideline §5.5).

Module → Blueprint → Owner
    auth.py        auth        H.G.P.C. Sagara        (this role)
    farmers.py     farmers     D.M.N.D. Dissanayaka / shared
    weights.py     weights     K.G.C. Ravishan
    payments.py    payments    D.M.N.D. Dissanayaka
    attendance.py  attendance  D.M.N.K. Disanayaka
    reports.py     reports     P.A.K.N. Dharmarathna

Run locally:
    cd tea_weighing
    python -m src.app
"""

import logging

from flask import Flask, render_template

from . import models
from .auth import bp as auth_bp
from .auth import ensure_operator_table, login_required
from .config import Config
from .db import db_available

# Feature blueprints contributed by the team. Registered with URL prefixes so
# each module owns a clean section of the URL space.
from .farmers import bp as farmers_bp
from .weights import bp as weights_bp
from .payments import bp as payments_bp
from .attendance import bp as attendance_bp
from .reports import bp as reports_bp

BLUEPRINTS = [
    (farmers_bp, "/farmers"),
    (weights_bp, "/weights"),
    (payments_bp, "/payments"),
    (attendance_bp, "/attendance"),
    (reports_bp, "/reports"),
]


def create_app(config_object=Config):
    """Build and return a configured Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.secret_key = config_object.SECRET_KEY

    logging.basicConfig(level=logging.INFO)

    # Authentication (login/logout/sessions) — always registered.
    app.register_blueprint(auth_bp)

    # Feature modules from the rest of the team.
    for blueprint, prefix in BLUEPRINTS:
        app.register_blueprint(blueprint, url_prefix=prefix)

    register_core_routes(app)
    register_error_handlers(app)

    # Create/seed the operator table and the shared schema on first boot
    # (no-op if the database is unavailable).
    ensure_operator_table()
    models.init_schema()

    return app


def register_core_routes(app):
    """Routes owned directly by integration: home, dashboard, health check."""

    @app.route("/")
    def index():
        from flask import redirect, url_for

        return redirect(url_for("dashboard"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        # The dashboard is the operator's landing page; it links out to every
        # feature module and shows whether the database is reachable.
        return render_template("dashboard.html", db_ok=db_available())

    @app.route("/healthz")
    def healthz():
        # Lightweight endpoint for the cloud host's uptime checks.
        return {"status": "ok", "database": "up" if db_available() else "down"}


def register_error_handlers(app):
    """Friendly error pages — never leak a stack trace to the user (§5.5)."""

    @app.errorhandler(404)
    def not_found(error):  # noqa: ARG001
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        app.logger.error("Unhandled server error: %s", error)
        return render_template("errors/500.html"), 500


# Module-level app for WSGI servers (gunicorn src.app:app) and `python -m src.app`.
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", False))

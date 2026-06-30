"""MySQL connection layer.

Owner: H.G.P.C. Sagara (PM & Integration Dev)

Every other module (farmers, weights, payments, attendance, reports) goes
through the helpers here instead of opening its own connection. This keeps
connection handling, error wrapping and parameterised queries consistent.

Design rules from the project guideline (Section 5.5):
  * All database calls are wrapped in try/except.
  * A stack trace is never shown to the user — failures raise ``DatabaseError``
    with a short message that the route layer turns into a friendly page.
  * Queries are always parameterised (``%s`` placeholders) to prevent injection.
"""

import mysql.connector
from flask import current_app, g

from .config import Config


class DatabaseError(Exception):
    """Raised for any database problem, carrying a user-safe message."""


def get_db():
    """Return a MySQL connection for the current request, opening one if needed.

    The connection is cached on Flask's ``g`` so a single request reuses one
    connection, and ``close_db`` (registered as a teardown handler) closes it.
    """
    if "db" not in g:
        try:
            g.db = mysql.connector.connect(**Config.db_config())
        except mysql.connector.Error as exc:
            # Log the real error for developers; surface a safe message only.
            current_app.logger.error("MySQL connection failed: %s", exc)
            raise DatabaseError(
                "Could not connect to the database. Please check the "
                "connection settings and that MySQL is running."
            ) from exc
    return g.db


def close_db(exception=None):  # noqa: ARG001 - signature required by Flask teardown
    """Close the request-scoped connection if one was opened."""
    db = g.pop("db", None)
    if db is not None and db.is_connected():
        db.close()


def query(sql, params=None, *, one=False):
    """Run a SELECT and return rows as dictionaries.

    Args:
        sql: parameterised SQL using ``%s`` placeholders.
        params: tuple/list of values bound to the placeholders.
        one: when True, return a single row (or None) instead of a list.
    """
    try:
        cursor = get_db().cursor(dictionary=True)
        cursor.execute(sql, params or ())
        rows = cursor.fetchall()
        cursor.close()
        return (rows[0] if rows else None) if one else rows
    except mysql.connector.Error as exc:
        current_app.logger.error("Query failed: %s | SQL=%s", exc, sql)
        raise DatabaseError("A database read error occurred.") from exc


def execute(sql, params=None):
    """Run an INSERT/UPDATE/DELETE, commit, and return the last row id."""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(sql, params or ())
        db.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id
    except mysql.connector.Error as exc:
        current_app.logger.error("Write failed: %s | SQL=%s", exc, sql)
        raise DatabaseError("A database write error occurred.") from exc


def db_available():
    """Return True if a connection can be opened — used by the dashboard banner."""
    try:
        get_db()
        return True
    except DatabaseError:
        return False


def init_app(app):
    """Register the teardown handler so connections are always closed."""
    app.teardown_appcontext(close_db)

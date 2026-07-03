"""MySQL helpers — the simple version.

Owner: H.G.P.C. Sagara (PM & Integration Dev)

How it works (nothing hidden):
    1. ``get_connection()`` opens a fresh connection using the settings in
       config.py.
    2. ``query()`` / ``execute()`` open a connection, run one SQL statement,
       close the connection, and return the result.

That's it. No connection caching, no Flask hooks — every call is
open → run → close, which is easy to follow and plenty fast for this app.

Rules from the project guideline (Section 5.5):
  * Every database call is wrapped in try/except.
  * The user never sees a stack trace — failures raise ``DatabaseError`` with
    a short message that routes turn into a friendly flash message.
  * Queries are always parameterised (``%s`` placeholders) — never build SQL
    with f-strings or ``+``.
"""

import logging

import mysql.connector

from .config import Config

log = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Raised for any database problem, carrying a user-safe message."""


def get_connection():
    """Open and return a new MySQL connection."""
    try:
        return mysql.connector.connect(**Config.DB_CONFIG)
    except mysql.connector.Error as exc:
        # Log the real error for developers; surface a safe message only.
        log.error("MySQL connection failed: %s", exc)
        raise DatabaseError(
            "Could not connect to the database. Please check the "
            "connection settings and that MySQL is running."
        ) from exc


def query(sql, params=None, *, one=False):
    """Run a SELECT and return rows as dictionaries.

    Args:
        sql: parameterised SQL using ``%s`` placeholders.
        params: tuple/list of values bound to the placeholders.
        one: when True, return a single row (or None) instead of a list.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        rows = cursor.fetchall()
        return (rows[0] if rows else None) if one else rows
    except mysql.connector.Error as exc:
        log.error("Query failed: %s | SQL=%s", exc, sql)
        raise DatabaseError("A database read error occurred.") from exc
    finally:
        conn.close()


def execute(sql, params=None):
    """Run an INSERT/UPDATE/DELETE, commit, and return the last row id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        conn.commit()
        return cursor.lastrowid
    except mysql.connector.Error as exc:
        log.error("Write failed: %s | SQL=%s", exc, sql)
        raise DatabaseError("A database write error occurred.") from exc
    finally:
        conn.close()


def db_available():
    """Return True if the database is reachable — used by the dashboard banner."""
    try:
        get_connection().close()
        return True
    except DatabaseError:
        return False

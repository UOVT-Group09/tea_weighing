"""Connection smoke test — run this BEFORE deploying to confirm the cloud
database is reachable and the schema applies.

Reads the same environment variables the app uses (from .env locally, or the
host's environment in the cloud), then:
    1. opens a connection and prints the server version,
    2. creates every table from models.SCHEMA_STATEMENTS,
    3. creates + seeds the operator table,
    4. lists the resulting tables.

Run from the tea_weighing/ directory:
    python -m data.check_db
"""

from src import models
from src.auth import ensure_operator_table
from src.config import Config
from src.db import DatabaseError, get_connection, query


def main():
    cfg = Config.DB_CONFIG
    tls = "on" if "ssl_ca" in cfg else "off"
    print(f"Connecting to {cfg['user']}@{cfg['host']}:{cfg['port']}/{cfg['database']} (TLS {tls})")

    try:
        conn = get_connection()
    except DatabaseError as exc:
        print(f"FAILED: {exc}")
        print("\nCheck: host/port (TiDB Cloud uses 4000), the password, and that")
        print("DB_SSL=1 is set for a managed provider.")
        raise SystemExit(1)

    version = query("SELECT VERSION() AS v", one=True)
    conn.close()
    print(f"Connected. Server reports: {version['v']}")

    print("Creating schema...")
    if not models.init_schema():
        print("FAILED: schema creation did not complete.")
        raise SystemExit(1)

    print("Creating/seeding operator table...")
    if not ensure_operator_table():
        print("FAILED: operator table not ready.")
        raise SystemExit(1)

    tables = query("SHOW TABLES")
    names = sorted(next(iter(row.values())) for row in tables)
    print(f"\nOK - {len(names)} tables present: {', '.join(names)}")
    print(f"Log in as '{Config.DEFAULT_OPERATOR_USERNAME}' with the password in DEFAULT_OPERATOR_PASSWORD.")


if __name__ == "__main__":
    main()

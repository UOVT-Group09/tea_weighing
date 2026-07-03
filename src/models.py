"""Database schema definition.

Owner: D.M.N.D. Dissanayaka (DB & Payments).

INTEGRATION NOTE from H.G.P.C. Sagara: the schema lives here as the single
source of truth. The data model from guideline §4.1 is captured below as
``SCHEMA_STATEMENTS`` so the integration layer and seed scripts can create the
database in one call. The operator/auth table is created separately in auth.py.

Tables implemented (guideline §4.1):
    farmer        (farmer_id PK, name, contact)
    weight_record (record_id PK, farmer_id FK -> farmer, date, weight_kg, flagged)
    payment       (payment_id PK, farmer_id FK -> farmer, period, total_kg, amount)
    plucker       (plucker_id PK, name, daily_rate)
    attendance    (attendance_id PK, plucker_id FK -> plucker, date, present)
    price_config  (price_id PK, price_per_kg, effective_date)
"""

from .db import DatabaseError, execute

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS farmer (
        farmer_id  INT AUTO_INCREMENT PRIMARY KEY,
        name       VARCHAR(100) NOT NULL,
        contact    VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS plucker (
        plucker_id INT AUTO_INCREMENT PRIMARY KEY,
        name       VARCHAR(100) NOT NULL,
        daily_rate DECIMAL(8,2) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS weight_record (
        record_id  INT AUTO_INCREMENT PRIMARY KEY,
        farmer_id  INT NOT NULL,
        date       DATE NOT NULL,
        weight_kg  DECIMAL(7,2) NOT NULL,
        flagged    TINYINT(1) NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_weight_record_farmer
            FOREIGN KEY (farmer_id) REFERENCES farmer(farmer_id) ON DELETE CASCADE,
        INDEX idx_weight_record_farmer_date (farmer_id, date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS price_config (
        price_id       INT AUTO_INCREMENT PRIMARY KEY,
        price_per_kg   DECIMAL(8,2) NOT NULL,
        effective_date DATE NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS payment (
        payment_id   INT AUTO_INCREMENT PRIMARY KEY,
        farmer_id    INT NOT NULL,
        period_start DATE NOT NULL,
        period_end   DATE NOT NULL,
        total_kg     DECIMAL(8,2) NOT NULL,
        amount       DECIMAL(10,2) NOT NULL,
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_payment_farmer
            FOREIGN KEY (farmer_id) REFERENCES farmer(farmer_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INT AUTO_INCREMENT PRIMARY KEY,
        plucker_id    INT NOT NULL,
        date          DATE NOT NULL,
        present       TINYINT(1) NOT NULL DEFAULT 0,
        CONSTRAINT fk_attendance_plucker
            FOREIGN KEY (plucker_id) REFERENCES plucker(plucker_id) ON DELETE CASCADE,
        UNIQUE KEY uq_attendance_plucker_date (plucker_id, date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
)

# Kept for anyone who wants to eyeball the full DDL in one string (docs, seed
# scripts) — ``init_schema`` executes ``SCHEMA_STATEMENTS`` individually since
# the MySQL connector runs one statement per ``execute`` call.
SCHEMA_SQL = "\n".join(statement.strip() for statement in SCHEMA_STATEMENTS)


def init_schema():
    """Create every table if it doesn't already exist.

    Safe to call repeatedly (each statement is ``CREATE TABLE IF NOT
    EXISTS``). Returns True on success, False if the database is unreachable
    so the app can still boot and show the "database offline" banner.
    """
    try:
        for statement in SCHEMA_STATEMENTS:
            execute(statement)
        return True
    except DatabaseError:
        return False

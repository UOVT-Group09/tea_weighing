"""Database schema definition for the Tea Leaves Weighing & Smart Records System."""

from src.db import get_db

# Fully normalised schema per system specification requirements
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS farmer (
    farmer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact VARCHAR(15) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS price_config (
    price_id INT AUTO_INCREMENT PRIMARY KEY,
    price_per_kg DECIMAL(10, 2) NOT NULL,
    effective_date DATE NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS weight_record (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT,
    date DATE NOT NULL,
    weight_kg DECIMAL(10, 2) NOT NULL,
    flagged BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (farmer_id) REFERENCES farmer(farmer_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS plucker (
    plucker_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    daily_rate DECIMAL(10, 2) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    plucker_id INT,
    date DATE NOT NULL,
    present BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (plucker_id) REFERENCES plucker(plucker_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT,
    period VARCHAR(50) NOT NULL,
    total_kg DECIMAL(10, 2) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (farmer_id) REFERENCES farmer(farmer_id) ON DELETE CASCADE
) ENGINE=InnoDB;
"""


def init_schema():
    """Initialise and create all structured database tables."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Executes all schema creation queries safely
        for result in cursor.execute(SCHEMA_SQL, multi=True):
            pass
            
        conn.commit()
        print("[Database] All tables initialised successfully!")
        
    except Exception as e:
        print(f"[Database Error] Failed to initialize schema: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    init_schema()
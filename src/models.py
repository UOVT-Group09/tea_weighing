"""Database schema definition.

Owner: D.M.N.D. Dissanayaka (DB & Payments).

INTEGRATION NOTE from H.G.P.C. Sagara: the schema lives here as the single
source of truth. The data model from guideline §4.1 is captured below as
``SCHEMA_SQL`` so the integration layer and seed scripts can create the
database in one call. The operator/auth table is created separately in auth.py.

Tables to implement (guideline §4.1):
    farmer        (farmer_id PK, name, contact)
    weight_record (record_id PK, farmer_id FK, date, weight_kg, flagged)
    payment       (payment_id PK, farmer_id FK, period, total_kg, amount)
    plucker       (plucker_id PK, name, daily_rate)
    attendance    (attendance_id PK, plucker_id FK, date, present)
    price_config  (price_id PK, price_per_kg, effective_date)
"""

# Owner D.M.N.D. Dissanayaka: fill in the CREATE TABLE statements here.
SCHEMA_SQL = """
-- TODO (Dissanayaka): full normalised schema per guideline §4.1.
"""


def init_schema():
    """Create all tables. Implemented by the database owner."""
    raise NotImplementedError("Owner: D.M.N.D. Dissanayaka — implement schema (§4.1)")

"""Payment & wage engine.

Owner: D.M.N.D. Dissanayaka (DB & Payments).
"""

from flask import Blueprint, render_template, flash, redirect, url_for
from .auth import login_required
from .db import execute

bp = Blueprint("payments", __name__)

@bp.route("/")
@login_required
def index():
    # 1. Fetch the latest active tea leaves price per kg from configuration
    # -------------------------------------------------------------------------
    price_query = "SELECT price_per_kg FROM price_config ORDER BY effective_date DESC, price_id DESC LIMIT 1"
    price_result = execute(price_query)
    
    # Fallback to a default price if no configuration is found in the database
    price_per_kg = float(price_result[0]['price_per_kg']) if price_result else 250.0

    # 2. Calculate Farmer Payments - Strictly excluding flagged anomaly/error records
    # -------------------------------------------------------------------------
    farmer_query = """
        SELECT 
            f.farmer_id,
            f.name,
            f.contact,
            COALESCE(SUM(w.weight_kg), 0) AS total_kg,
            COALESCE(SUM(w.weight_kg), 0) * %s AS total_amount
        FROM farmer f
        LEFT JOIN weight_record w ON f.farmer_id = w.farmer_id AND w.flagged = 0
        GROUP BY f.farmer_id, f.name, f.contact
    """
    farmer_payments = execute(farmer_query, (price_per_kg,))

    # 3. Calculate Plucker Wages - Based on attendance logs and individual daily rates
    # -------------------------------------------------------------------------
    plucker_query = """
        SELECT 
            p.plucker_id,
            p.name,
            p.daily_rate,
            COUNT(a.attendance_id) AS days_present,
            COUNT(a.attendance_id) * p.daily_rate AS total_wage
        FROM plucker p
        LEFT JOIN attendance a ON p.plucker_id = a.plucker_id AND a.present = 1
        GROUP BY p.plucker_id, p.name, p.daily_rate
    """
    plucker_wages = execute(plucker_query)

    # Render data to the frontend template view
    return render_template(
        "payments/index.html",
        price_per_kg=price_per_kg,
        farmer_payments=farmer_payments,
        plucker_wages=plucker_wages
    )
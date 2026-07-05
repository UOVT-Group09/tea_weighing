"""
Daily weight entry + smart error/anomaly check wiring.

Owner: K.G.C. Ravishan (Lead Dev — Weights & Smart Checks)

Records a weight against a farmer. Every submission is run through
checks.check() first. Positive-but-out-of-range weights trigger a warning
and require confirmation. Flagged rows are stored but excluded from payments.
"""

from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from . import checks
from .auth import login_required
from .db import DatabaseError, execute, query
from .validators import parse_weight, parse_past_or_today

bp = Blueprint("weights", __name__, url_prefix="/weights")

RECENT_LIMIT = 10


# =========================
# DATA HELPERS
# =========================
def _farmers():
    return query("SELECT farmer_id, name FROM farmer ORDER BY name")


def _recent_entries(farmer_id):
    return query(
        """
        SELECT record_id, date, weight_kg, flagged
        FROM weight_record
        WHERE farmer_id = %s
        ORDER BY date DESC, record_id DESC
        LIMIT %s
        """,
        (farmer_id, RECENT_LIMIT),
    )


def _recent_average(farmer_id):
    rows = _recent_entries(farmer_id)
    weights = [float(row["weight_kg"]) for row in rows]
    return round(sum(weights) / len(weights), 2) if weights else None


def _render_index(*, farmers, selected_farmer_id, form_values=None, pending=None):
    recent = _recent_entries(selected_farmer_id) if selected_farmer_id else []

    return render_template(
        "weights/index.html",
        farmers=farmers,
        selected_farmer_id=selected_farmer_id,
        recent=recent,
        today=date.today().isoformat(),
        form_values=form_values or {},
        pending=pending,
    )


# =========================
# MAIN PAGE
# =========================
@bp.route("/")
@login_required
def index():
    try:
        farmers = _farmers()

    except DatabaseError:
        flash("Database is unavailable — weight entry is disabled.", "danger")
        return render_template(
            "weights/index.html",
            farmers=[],
            selected_farmer_id=None,
            recent=[],
            today=date.today().isoformat(),
            form_values={},
            pending=None,
        )

    requested = request.args.get("farmer_id", type=int)

    selected_farmer_id = requested if any(
        f["farmer_id"] == requested for f in farmers
    ) else (farmers[0]["farmer_id"] if farmers else None)

    return _render_index(
        farmers=farmers,
        selected_farmer_id=selected_farmer_id
    )


# =========================
# PARSE + VALIDATE ENTRY
# =========================
def _parse_entry(form):
    """Validate form using shared validators."""

    farmer_id = form.get("farmer_id", type=int)
    date_str = (form.get("date") or "").strip()
    weight_raw = (form.get("weight_kg") or "").strip()

    if not farmer_id:
        return None, None, date_str, "Please choose a farmer."

    # ✅ shared validator (weight)
    weight, err = parse_weight(weight_raw)
    if err:
        return farmer_id, None, date_str, err

    # ✅ shared validator (date)
    entry_date, err = parse_past_or_today(date_str)
    if err:
        return farmer_id, weight, date_str, err

    return farmer_id, weight, date_str, None


# =========================
# SAVE ENTRY (SMART CHECK)
# =========================
@bp.route("/save", methods=["POST"])
@login_required
def save():
    farmer_id, weight, date_str, error = _parse_entry(request.form)

    form_values = {
        "farmer_id": farmer_id,
        "date": date_str,
        "weight_kg": request.form.get("weight_kg"),
    }

    try:
        farmers = _farmers()

        if error:
            flash(error, "danger")
            return _render_index(
                farmers=farmers,
                selected_farmer_id=farmer_id,
                form_values=form_values
            )

        result = checks.check(farmer_id, weight)

        # ❌ reject case
        if result == checks.REJECT_NOT_POSITIVE:
            flash("Weight must be a positive number.", "danger")
            return _render_index(
                farmers=farmers,
                selected_farmer_id=farmer_id,
                form_values=form_values
            )

        # ⚠️ warning case (needs confirmation)
        if result == checks.WARN_OUT_OF_RANGE:
            farmer = next(
                (f for f in farmers if f["farmer_id"] == farmer_id),
                None
            )

            pending = {
                "farmer_id": farmer_id,
                "farmer_name": farmer["name"] if farmer else "",
                "date": date_str,
                "weight_kg": weight,
                "avg": _recent_average(farmer_id),
            }

            return _render_index(
                farmers=farmers,
                selected_farmer_id=farmer_id,
                form_values=form_values,
                pending=pending
            )

        # ✅ normal save
        _insert_record(farmer_id, date_str, weight, flagged=False)

    except DatabaseError:
        flash("Database error — entry not saved.", "danger")
        return redirect(url_for("weights.index"))

    flash(f"Saved {weight:g} kg successfully.", "success")
    return redirect(url_for("weights.index", farmer_id=farmer_id))


# =========================
# CONFIRM FLAGGED ENTRY
# =========================
@bp.route("/confirm", methods=["POST"])
@login_required
def confirm():
    farmer_id, weight, date_str, error = _parse_entry(request.form)

    if error:
        flash(error, "danger")
        return redirect(url_for("weights.index", farmer_id=farmer_id))

    try:
        _insert_record(farmer_id, date_str, weight, flagged=True)

    except DatabaseError:
        flash("Database error — entry not saved.", "danger")
        return redirect(url_for("weights.index", farmer_id=farmer_id))

    flash(f"Saved {weight:g} kg (flagged for review).", "warning")
    return redirect(url_for("weights.index", farmer_id=farmer_id))


# =========================
# DB INSERT
# =========================
def _insert_record(farmer_id, date_str, weight, *, flagged):
    execute(
        """
        INSERT INTO weight_record (farmer_id, date, weight_kg, flagged)
        VALUES (%s, %s, %s, %s)
        """,
        (farmer_id, date_str, weight, flagged),
    )
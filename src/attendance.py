"""
Plucker attendance module

Owner: D.M.N.K. Disanayaka (Attendance, Validation & Tests)

Features:
- View today's attendance list
- Mark attendance (present / absent)
- Add new pluckers
"""

from datetime import date as date_cls
from flask import Blueprint, render_template, request, redirect, url_for, flash

from .db import query, execute, DatabaseError
from .auth import login_required

bp = Blueprint("attendance", __name__, url_prefix="/attendance")


# 🔹 Show today's attendance page
@bp.route("/", methods=["GET"])
@login_required
def index():
    try:
        today = date_cls.today()

        # Get all pluckers
        pluckers = query("SELECT * FROM plucker ORDER BY name")

        # Get today's attendance records
        attendance_rows = query(
            "SELECT plucker_id, present FROM attendance WHERE date = %s",
            (today,),
        )

        # Convert to dictionary for easy lookup
        attendance_map = {row["plucker_id"]: row["present"] for row in attendance_rows}

    except DatabaseError as exc:
        flash(str(exc), "danger")
        pluckers = []
        attendance_map = {}
        today = date_cls.today()

    return render_template(
        "attendance/index.html",
        pluckers=pluckers,
        attendance_map=attendance_map,
        today=today,
    )


# 🔹 Mark attendance (insert or update)
@bp.route("/mark", methods=["POST"])
@login_required
def mark():
    try:
        plucker_id = int(request.form.get("plucker_id"))
        present = request.form.get("present") == "true"
        day_raw = request.form.get("date")

        # Validate date
        try:
            day = date_cls.fromisoformat(day_raw)
        except Exception:
            flash("Invalid date.", "danger")
            return redirect(url_for("attendance.index"))

        if day > date_cls.today():
            flash("Future dates are not allowed.", "danger")
            return redirect(url_for("attendance.index"))

        # UPSERT (insert or update)
        execute(
            "INSERT INTO attendance (plucker_id, date, present) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE present = VALUES(present)",
            (plucker_id, day, present),
        )

        flash("Attendance updated.", "success")

    except (ValueError, TypeError):
        flash("Invalid input.", "danger")

    except DatabaseError as exc:
        flash(str(exc), "danger")

    return redirect(url_for("attendance.index"))


# 🔹 Add new plucker
@bp.route("/pluckers/add", methods=["GET", "POST"])
@login_required
def add_plucker():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        rate_raw = request.form.get("daily_rate")

        # Validation
        if not name:
            flash("Name is required.", "danger")
            return render_template("attendance/add_plucker.html")

        try:
            rate = float(rate_raw)
            if rate <= 0:
                raise ValueError
        except (TypeError, ValueError):
            flash("Daily rate must be a positive number.", "danger")
            return render_template("attendance/add_plucker.html")

        try:
            execute(
                "INSERT INTO plucker (name, daily_rate) VALUES (%s, %s)",
                (name, rate),
            )
            flash("Plucker added successfully.", "success")
            return redirect(url_for("attendance.index"))

        except DatabaseError as exc:
            flash(str(exc), "danger")

    return render_template("attendance/add_plucker.html")
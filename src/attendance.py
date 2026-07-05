from datetime import date as date_cls
from flask import Blueprint, render_template, request, redirect, url_for, flash

from .db import query, execute, DatabaseError
from .auth import login_required

bp = Blueprint("attendance", __name__, url_prefix="/attendance")


# =========================
# 📌 INDEX - SHOW ATTENDANCE
# =========================
@bp.route("/", methods=["GET"])
@login_required
def index():
    try:
        today = date_cls.today().isoformat()

        # all pluckers
        pluckers = query("SELECT plucker_id, name FROM plucker ORDER BY name")

        # today's attendance
        rows = query(
            "SELECT plucker_id, present FROM attendance WHERE date = %s",
            (today,),
        )

        attendance_map = {
            r["plucker_id"]: r["present"] for r in rows
        }

    except DatabaseError as exc:
        flash(str(exc), "danger")
        today = date_cls.today().isoformat()
        pluckers = []
        attendance_map = {}

    return render_template(
        "attendance/index.html",
        today=today,
        pluckers=pluckers,
        attendance_map=attendance_map,
    )


# =========================
# 📌 MARK ATTENDANCE (UPSERT)
# =========================
@bp.route("/mark", methods=["POST"])
@login_required
def mark():
    try:
        plucker_id = int(request.form.get("plucker_id"))
        present = request.form.get("present") == "true"
        day = request.form.get("date") or date_cls.today().isoformat()

        # validate date
        try:
            day = date_cls.fromisoformat(day).isoformat()
        except Exception:
            flash("Invalid date format.", "danger")
            return redirect(url_for("attendance.index"))

        # prevent future date
        if day > date_cls.today().isoformat():
            flash("Future dates are not allowed.", "danger")
            return redirect(url_for("attendance.index"))

        # UPSERT (MySQL safe)
        execute(
            """
            INSERT INTO attendance (plucker_id, date, present)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE present = VALUES(present)
            """,
            (plucker_id, day, present),
        )

        flash("Attendance updated successfully.", "success")

    except (ValueError, TypeError):
        flash("Invalid input.", "danger")

    except DatabaseError as exc:
        flash(str(exc), "danger")

    return redirect(url_for("attendance.index"))


# =========================
# 📌 ADD PLUCKER
# =========================
@bp.route("/pluckers/add", methods=["GET", "POST"])
@login_required
def add_plucker():
    try:
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            rate = request.form.get("daily_rate")

            # validation
            if not name:
                flash("Name is required.", "danger")
                return redirect(url_for("attendance.add_plucker"))

            try:
                rate = float(rate)
                if rate <= 0:
                    raise ValueError
            except:
                flash("Invalid daily rate.", "danger")
                return redirect(url_for("attendance.add_plucker"))

            execute(
                "INSERT INTO plucker (name, daily_rate) VALUES (%s, %s)",
                (name, rate),
            )

            flash("Plucker added successfully.", "success")
            return redirect(url_for("attendance.index"))

        # GET request
        pluckers = query("SELECT * FROM plucker ORDER BY plucker_id DESC")

        return render_template(
            "attendance/add_plucker.html",
            pluckers=pluckers
        )

    except DatabaseError as exc:
        flash(str(exc), "danger")
        return render_template("attendance/add_plucker.html", pluckers=[])
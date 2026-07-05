"""Farmer registry — CRUD.

Owner: D.M.N.D. Dissanayaka (DB & Payments).
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from .auth import login_required
from .db import execute, query

bp = Blueprint("farmers", __name__)

# 1. Read (List all farmers)
@bp.route("/")
@login_required
def index():
    farmers = query("SELECT farmer_id, name, contact FROM farmer ORDER BY farmer_id DESC")
    return render_template("farmers/index.html", farmers=farmers)

# 2. Create (Add new farmer)
@bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        name = request.form.get("name")
        contact = request.form.get("contact")

        if not name:
            flash("Name is required!", "danger")
            return redirect(url_for("farmers.add"))

        execute("INSERT INTO farmer (name, contact) VALUES (%s, %s)", (name, contact if contact else None))
        flash("Farmer added successfully!", "success")
        return redirect(url_for("farmers.index"))
    
    return render_template("farmers/add.html")

# 3. Update (Edit farmer)
@bp.route("/edit/<int:farmer_id>", methods=["GET", "POST"])
@login_required
def edit(farmer_id):
    if request.method == "POST":
        name = request.form.get("name")
        contact = request.form.get("contact")

        if not name:
            flash("Name is required!", "danger")
            return redirect(url_for("farmers.edit", farmer_id=farmer_id))

        execute("UPDATE farmer SET name = %s, contact = %s WHERE farmer_id = %s", (name, contact if contact else None, farmer_id))
        flash("Farmer updated successfully!", "success")
        return redirect(url_for("farmers.index"))
    
    result = query("SELECT farmer_id, name, contact FROM farmer WHERE farmer_id = %s", (farmer_id,))
    farmer = result[0] if result else None
    
    if not farmer:
        flash("Farmer not found!", "danger")
        return redirect(url_for("farmers.index"))

    return render_template("farmers/edit.html", farmer=farmer)

# 4. Delete (Remove farmer)
@bp.route("/delete/<int:farmer_id>", methods=["POST"])
@login_required
def delete(farmer_id):
    try:
        execute("DELETE FROM farmer WHERE farmer_id = %s", (farmer_id,))
        flash("Farmer deleted successfully!", "success")
    except Exception:
        flash("Could not delete farmer. They might have related weight records.", "danger")
    return redirect(url_for("farmers.index"))
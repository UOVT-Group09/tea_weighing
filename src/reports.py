"""Reports, trend display and optional charts dashboard.

Owner: P.A.K.N. Dharmarathna (Domain Researcher & Reports/Trend Dev).

Daily and farmer-wise reports with date-range/farmer filters, trend estimates
from checks.py (per farmer and combined), and Chart.js charts.
"""

from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, render_template, request

from . import checks
from .auth import login_required
from .db import DatabaseError, query

bp = Blueprint("reports", __name__)

DEFAULT_RANGE_DAYS = 7


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _default_range():
    """Default view: last 7 days including today."""
    today = date.today()
    return today - timedelta(days=DEFAULT_RANGE_DAYS - 1), today


def _parse_filters():
    today = date.today()
    default_start, default_end = _default_range()
    start = _parse_date(request.args.get("start")) or default_start
    end = _parse_date(request.args.get("end")) or default_end

    if end > today:
        end = today
    if start > today:
        start = today
    if start > end:
        start, end = end, start

    farmer_id = request.args.get("farmer_id", type=int)
    return start, end, farmer_id


def _filter_query(start, end, farmer_id=None):
    """Build query-string args for links and forms."""
    q = {"start": start.isoformat(), "end": end.isoformat()}
    if farmer_id:
        q["farmer_id"] = farmer_id
    return q


def _farmers():
    return query("SELECT farmer_id, name FROM farmer ORDER BY name")


def _daily_report(start, end, farmer_id=None):
    sql = (
        "SELECT date, SUM(weight_kg) AS total_kg, COUNT(*) AS entries "
        "FROM weight_record WHERE date BETWEEN %s AND %s "
    )
    params = [start, end]
    if farmer_id:
        sql += "AND farmer_id = %s "
        params.append(farmer_id)
    sql += "GROUP BY date ORDER BY date DESC"
    return query(sql, tuple(params))


def _farmer_records(farmer_id, start, end):
    return query(
        """
        SELECT record_id, date, weight_kg, flagged
        FROM weight_record
        WHERE farmer_id = %s AND date BETWEEN %s AND %s
        ORDER BY date DESC, record_id DESC
        """,
        (farmer_id, start, end),
    )


def _chart_series(rows):
    chart_rows = sorted(rows, key=lambda r: r["date"])
    labels = [r["date"].strftime("%d %b") for r in chart_rows]
    values = [float(r["total_kg"]) for r in chart_rows]
    return labels, values


def _build_farmer_trends(farmers):
    """Trend estimate for every registered farmer."""
    return [
        {
            "farmer_id": f["farmer_id"],
            "name": f["name"],
            "trend": checks.estimate(f["farmer_id"]),
        }
        for f in farmers
    ]


def _aggregate_trend(farmer_trends):
    """Combined next-day harvest hint when viewing all farmers."""
    with_trend = [t for t in farmer_trends if t["trend"]]
    if not with_trend:
        return None

    total_estimate = round(sum(t["trend"][0] for t in with_trend), 2)
    up_count = sum(1 for t in with_trend if t["trend"][1] == "up")
    direction = "up" if up_count >= len(with_trend) / 2 else "down"
    return (total_estimate, direction, len(with_trend))


def _report_context(start, end, farmer_id, farmers, rows):
    farmer_trends = _build_farmer_trends(farmers)
    selected_farmer = None
    trend = None

    if farmer_id:
        selected_farmer = next(
            (f for f in farmers if f["farmer_id"] == farmer_id), None
        )
        if selected_farmer:
            trend = checks.estimate(farmer_id)

    chart_labels, chart_values = _chart_series(rows)
    aggregate_trend = None if farmer_id else _aggregate_trend(farmer_trends)

    return {
        "farmers": farmers,
        "rows": rows,
        "start": start,
        "end": end,
        "farmer_id": farmer_id,
        "filter_q": _filter_query(start, end, farmer_id),
        "today": date.today().isoformat(),
        "selected_farmer": selected_farmer,
        "trend": trend,
        "farmer_trends": farmer_trends,
        "aggregate_trend": aggregate_trend,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
        "db_error": False,
    }


@bp.route("/")
@login_required
def index():
    start, end, farmer_id = _parse_filters()

    try:
        farmers = _farmers()
        rows = _daily_report(start, end, farmer_id)
        ctx = _report_context(start, end, farmer_id, farmers, rows)
    except DatabaseError:
        ds, de = _default_range()
        ctx = {
            "farmers": [],
            "rows": [],
            "start": start or ds,
            "end": end or de,
            "farmer_id": farmer_id,
            "filter_q": _filter_query(start or ds, end or de, farmer_id),
            "today": date.today().isoformat(),
            "selected_farmer": None,
            "trend": None,
            "farmer_trends": [],
            "aggregate_trend": None,
            "chart_labels": [],
            "chart_values": [],
            "db_error": True,
        }

    return render_template("reports/index.html", **ctx)


@bp.route("/farmer/<int:farmer_id>")
@login_required
def farmer(farmer_id):
    start, end, _ = _parse_filters()

    try:
        farmer_row = query(
            "SELECT farmer_id, name FROM farmer WHERE farmer_id = %s",
            (farmer_id,),
            one=True,
        )
        if not farmer_row:
            return render_template("errors/404.html"), 404

        records = _farmer_records(farmer_id, start, end)
        trend = checks.estimate(farmer_id)
        farmers = _farmers()
        chart_labels, chart_values = _chart_series(
            _daily_report(start, end, farmer_id)
        )
    except DatabaseError:
        ds, de = _default_range()
        return render_template(
            "reports/farmer.html",
            farmer=None,
            records=[],
            trend=None,
            start=start or ds,
            end=end or de,
            filter_q=_filter_query(start or ds, end or de, farmer_id),
            today=date.today().isoformat(),
            farmers=[],
            chart_labels=[],
            chart_values=[],
            db_error=True,
        )

    return render_template(
        "reports/farmer.html",
        farmer=farmer_row,
        records=records,
        trend=trend,
        start=start,
        end=end,
        filter_q=_filter_query(start, end, farmer_id),
        today=date.today().isoformat(),
        farmers=farmers,
        chart_labels=chart_labels,
        chart_values=chart_values,
        db_error=False,
    )


@bp.route("/charts")
@login_required
def charts():
    start, end, farmer_id = _parse_filters()

    try:
        farmers = _farmers()
        rows = _daily_report(start, end, farmer_id)
        ctx = _report_context(start, end, farmer_id, farmers, rows)
    except DatabaseError:
        ds, de = _default_range()
        ctx = {
            "farmers": [],
            "rows": [],
            "start": start or ds,
            "end": end or de,
            "farmer_id": farmer_id,
            "filter_q": _filter_query(start or ds, end or de, farmer_id),
            "today": date.today().isoformat(),
            "selected_farmer": None,
            "trend": None,
            "farmer_trends": [],
            "aggregate_trend": None,
            "chart_labels": [],
            "chart_values": [],
            "db_error": True,
        }

    return render_template("reports/charts.html", **ctx)


@bp.route("/api/daily")
@login_required
def api_daily():
    """JSON feed for Chart.js — daily totals for the selected date range."""
    start, end, farmer_id = _parse_filters()
    try:
        rows = _daily_report(start, end, farmer_id)
    except DatabaseError:
        return jsonify({"error": "Database unavailable"}), 503

    chart_rows = sorted(rows, key=lambda r: r["date"])
    return jsonify(
        {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "farmer_id": farmer_id,
            "labels": [r["date"].isoformat() for r in chart_rows],
            "values": [float(r["total_kg"]) for r in chart_rows],
            "rows": [
                {
                    "date": r["date"].isoformat(),
                    "total_kg": float(r["total_kg"]),
                    "entries": int(r["entries"]),
                }
                for r in rows
            ],
        }
    )

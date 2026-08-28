"""Read-only data tools shared by the chatbot and the MCP server.

Owner: H.G.P.C. Sagara (PM & Integration Dev)

Every tool here is a plain function that returns JSON-safe dictionaries.
Two consumers call them:

    * llm.py — the in-app chatbot lets the LLM pick a tool (function calling)
    * src/mcp_server.py — exposes the same tools to MCP clients

Safety rules (deliberate, worth stating in the viva):
    * Tools are READ-ONLY — only SELECT statements, so the assistant can
      never modify or delete data.
    * The LLM never writes SQL. It can only pick a tool name and arguments;
      the SQL lives here and is always parameterised.
    * Database failures are caught and returned as ``{"error": ...}`` so the
      chatbot degrades gracefully instead of crashing.
"""

import json
from datetime import date as date_type

from ..checks import estimate
from ..db import DatabaseError, query
from . import rag


def _to_jsonable(rows):
    """Convert Decimal/date values from mysql-connector into JSON-safe types."""
    def convert(value):
        if isinstance(value, date_type):
            return value.isoformat()
        if hasattr(value, "is_finite"):  # Decimal
            return float(value)
        return value

    return [{k: convert(v) for k, v in row.items()} for row in rows]


def _current_price():
    row = query(
        "SELECT price_per_kg FROM price_config "
        "ORDER BY effective_date DESC, price_id DESC LIMIT 1",
        one=True,
    )
    return float(row["price_per_kg"]) if row else 250.0


# --------------------------------------------------------------------------
# Tool implementations
# --------------------------------------------------------------------------

def list_farmers():
    """List every registered farmer with id, name and contact."""
    try:
        rows = query("SELECT farmer_id, name, contact FROM farmer ORDER BY name")
        return {"farmers": _to_jsonable(rows), "count": len(rows)}
    except DatabaseError as exc:
        return {"error": str(exc)}


def get_farmer_summary(farmer_name):
    """Totals, recent weights and trend for one farmer (matched by name)."""
    try:
        farmer = query(
            "SELECT farmer_id, name, contact FROM farmer WHERE name LIKE %s LIMIT 1",
            (f"%{farmer_name}%",),
            one=True,
        )
        if not farmer:
            return {"error": f"No farmer matching '{farmer_name}' was found."}

        totals = query(
            """
            SELECT COALESCE(SUM(weight_kg), 0) AS total_kg,
                   COUNT(*) AS entries,
                   SUM(flagged) AS flagged_entries
            FROM weight_record WHERE farmer_id = %s
            """,
            (farmer["farmer_id"],),
            one=True,
        )
        recent = query(
            """
            SELECT date, weight_kg, flagged FROM weight_record
            WHERE farmer_id = %s ORDER BY date DESC, record_id DESC LIMIT 7
            """,
            (farmer["farmer_id"],),
        )
        trend = estimate(farmer["farmer_id"])
        return {
            "farmer": _to_jsonable([farmer])[0],
            "total_kg": float(totals["total_kg"] or 0),
            "entries": int(totals["entries"] or 0),
            "flagged_entries": int(totals["flagged_entries"] or 0),
            "recent_weights": _to_jsonable(recent),
            "trend": {"moving_avg_kg": trend[0], "direction": trend[1]}
            if trend
            else "not enough history (needs 3+ records)",
        }
    except DatabaseError as exc:
        return {"error": str(exc)}


def get_daily_summary(date=None):
    """Collection summary for one date (YYYY-MM-DD); defaults to today."""
    try:
        target = date or date_type.today().isoformat()
        totals = query(
            """
            SELECT COALESCE(SUM(weight_kg), 0) AS total_kg,
                   COUNT(*) AS entries,
                   COALESCE(SUM(flagged), 0) AS flagged_entries,
                   COUNT(DISTINCT farmer_id) AS farmers
            FROM weight_record WHERE date = %s
            """,
            (target,),
            one=True,
        )
        return {
            "date": target,
            "total_kg": float(totals["total_kg"] or 0),
            "entries": int(totals["entries"] or 0),
            "flagged_entries": int(totals["flagged_entries"] or 0),
            "farmers_delivered": int(totals["farmers"] or 0),
        }
    except DatabaseError as exc:
        return {"error": str(exc)}


def get_flagged_records(limit=10):
    """Most recent weight entries flagged by the automatic error check."""
    try:
        limit = max(1, min(int(limit), 50))
        rows = query(
            """
            SELECT w.record_id, f.name AS farmer, w.date, w.weight_kg
            FROM weight_record w JOIN farmer f ON f.farmer_id = w.farmer_id
            WHERE w.flagged = 1
            ORDER BY w.date DESC, w.record_id DESC LIMIT %s
            """,
            (limit,),
        )
        return {"flagged_records": _to_jsonable(rows), "count": len(rows)}
    except DatabaseError as exc:
        return {"error": str(exc)}


def get_payment_summary():
    """Per-farmer payable amounts (unflagged kg x current price) and wages."""
    try:
        price = _current_price()
        farmers = query(
            """
            SELECT f.name,
                   COALESCE(SUM(w.weight_kg), 0) AS total_kg,
                   COALESCE(SUM(w.weight_kg), 0) * %s AS amount
            FROM farmer f
            LEFT JOIN weight_record w
                   ON f.farmer_id = w.farmer_id AND w.flagged = 0
            GROUP BY f.farmer_id, f.name ORDER BY amount DESC
            """,
            (price,),
        )
        pluckers = query(
            """
            SELECT p.name, p.daily_rate,
                   COUNT(a.attendance_id) AS days_present,
                   COUNT(a.attendance_id) * p.daily_rate AS total_wage
            FROM plucker p
            LEFT JOIN attendance a
                   ON p.plucker_id = a.plucker_id AND a.present = 1
            GROUP BY p.plucker_id, p.name, p.daily_rate
            """,
        )
        return {
            "price_per_kg": price,
            "currency": "LKR",
            "farmer_payments": _to_jsonable(farmers),
            "plucker_wages": _to_jsonable(pluckers),
            "note": "Flagged weight entries are excluded from payments.",
        }
    except DatabaseError as exc:
        return {"error": str(exc)}


def get_attendance_summary(date=None):
    """Plucker attendance for one date (YYYY-MM-DD); defaults to today."""
    try:
        target = date or date_type.today().isoformat()
        rows = query(
            """
            SELECT p.name, a.present FROM plucker p
            LEFT JOIN attendance a
                   ON a.plucker_id = p.plucker_id AND a.date = %s
            ORDER BY p.name
            """,
            (target,),
        )
        present = [r["name"] for r in rows if r["present"]]
        return {
            "date": target,
            "present": present,
            "absent_or_unmarked": [r["name"] for r in rows if not r["present"]],
            "present_count": len(present),
            "total_pluckers": len(rows),
        }
    except DatabaseError as exc:
        return {"error": str(exc)}


def get_tea_price():
    """The tea price per kg currently used for payments."""
    try:
        return {"price_per_kg": _current_price(), "currency": "LKR"}
    except DatabaseError as exc:
        return {"error": str(exc)}


def search_app_knowledge(question):
    """Search the built-in user manual (used mainly by MCP clients)."""
    results = rag.retrieve(question, k=3)
    if not results:
        return {"results": [], "note": "Nothing in the manual matched."}
    return {"results": [{k: r[k] for k in ("source", "heading", "text")} for r in results]}


# --------------------------------------------------------------------------
# Registry — one place that maps tool names to functions and OpenAI-style
# schemas, so llm.py and mcp_server.py stay in sync automatically.
# --------------------------------------------------------------------------

_DATE_PARAM = {
    "type": "string",
    "description": "Date in YYYY-MM-DD format. Omit for today.",
}

TOOL_REGISTRY = {
    "list_farmers": (list_farmers, {"type": "object", "properties": {}}),
    "get_farmer_summary": (
        get_farmer_summary,
        {
            "type": "object",
            "properties": {
                "farmer_name": {
                    "type": "string",
                    "description": "Full or partial farmer name to look up.",
                }
            },
            "required": ["farmer_name"],
        },
    ),
    "get_daily_summary": (
        get_daily_summary,
        {"type": "object", "properties": {"date": _DATE_PARAM}},
    ),
    "get_flagged_records": (
        get_flagged_records,
        {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max rows (1-50)."}
            },
        },
    ),
    "get_payment_summary": (get_payment_summary, {"type": "object", "properties": {}}),
    "get_attendance_summary": (
        get_attendance_summary,
        {"type": "object", "properties": {"date": _DATE_PARAM}},
    ),
    "get_tea_price": (get_tea_price, {"type": "object", "properties": {}}),
    "search_app_knowledge": (
        search_app_knowledge,
        {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "What to look up."}
            },
            "required": ["question"],
        },
    ),
}


def openai_tool_specs():
    """Tool list in the OpenAI/Groq ``tools`` format for function calling."""
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": (func.__doc__ or "").strip(),
                "parameters": schema,
            },
        }
        for name, (func, schema) in TOOL_REGISTRY.items()
    ]


def run_tool(name, arguments):
    """Execute a tool by name with a dict of arguments; always returns JSON."""
    entry = TOOL_REGISTRY.get(name)
    if entry is None:
        return json.dumps({"error": f"Unknown tool '{name}'."})
    func = entry[0]
    try:
        return json.dumps(func(**(arguments or {})), default=str)
    except TypeError as exc:
        return json.dumps({"error": f"Bad arguments for {name}: {exc}"})

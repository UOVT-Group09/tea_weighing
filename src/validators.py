"""
Shared validation helpers for Tea Weighing System
"""

from datetime import date, datetime


# =========================
# WEIGHT VALIDATION
# =========================
def parse_weight(raw):
    """
    Returns: (value, error)
    """
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None, "Weight must be a number."

    if value <= 0:
        return None, "Weight must be positive."

    return value, None


# =========================
# DATE VALIDATION
# =========================
def parse_past_or_today(raw):
    """
    Returns: (date, error)
    """

    try:
        d = datetime.strptime(raw, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None, "Invalid date format."

    if d > date.today():
        return None, "Future dates are not allowed."

    return d, None